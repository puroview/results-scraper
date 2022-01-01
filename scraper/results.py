# External Imports
import logging
import requests
import string
from bs4 import BeautifulSoup

# Internal Imports
from models import Results, Promotions

## Classes
# ResultsScraper Class
class ResultsScraper:
    """
    A class for the results scraper, with methods for retrieving webscraped data and saving to the database
    
    Methods
    -------    
    update_events()
        For each promotion in the database, search for new results and add to DB

    get_events()
        Scrape the results for the promotion, for the dates provided

    clean_titles()
        Clean up and standardise the titles of shows found by the scraper

    clean_results()
        Clean up and standardise the text of results found by the scraper
    """
    def __init__(self):
        logging.info("Building ResultsScraper object")

    def update_events(self, date_list):
        """
        For all promotions in the database, search for new results and add to DB

        Parameters
        ----------
        date_list : list
            List of dates to retrieve results for

        Returns
        -------
        updated_shows :list
            Simple list of updated shows for use in notifications
        """
        logging.info("Updating events")
        
        # Build updated_shows list used later for notifications
        updated_shows = []

        logging.debug(Promotions.objects())

        # Get list of promotions from database
        for promotion in Promotions.objects():
            logging.info(f"Finding Events for {promotion.name}")

            logging.debug(f"Creating Promotion object for {promotion['name']}")
            # For each promotion, build a list of events
            events = self.get_events(promotion, date_list)

            if events:
                # Continue only if there are any events found for the promotion in the time frame
                logging.info(f"Found events for {promotion.name}")

                for event in events:
                    # For each event, add the promotion name to its attributes
                    event['promotion'] = promotion.name

                    # Check whether the show already exists, based on the event name and date
                    if not Results.objects(title=event['title'], date=event['date']):
                        # If it doesn't already exist, save it to the db and add to the list of updated shows
                        db_show = Results(**event).save()
                        logging.info(f"Saved document ID {db_show.id} for {event['promotion']}, {event['title']}, {event['date']}")
                        updated_shows.append(event['promotion'] + " - " + event['title'])
                    else:
                        # If show is already in the db, update the details
                        update = Results.objects(title=event['title'], date=event['date']).update(**event, full_result=True)
                        if update.modified_count > 0:
                            logging.info(f"Updated DB entry for {event['promotion']}, {event['title']}, {event['date']}")
                        else:
                            logging.info(f"DB entry exists for {event['promotion']}, {event['title']}, {event['date']}")
            else:
                logging.info(f"No events found for {promotion.name}")
            
        # Create string of updated shows for notifications
        updated_shows = '\n'.join(updated_shows)
        
        return updated_shows

    def get_events(self, promotion, date_list):
        """Scrape the results for the promotion, for the dates provided

        Parameters
        ----------
        promotion : object
            Promotion object pulled from DB
        date_list : list
            List of dates to retrieve results for

        Returns
        -------
        results_list
            List of results found for the promotion in the date range
        """
        logging.info(f"Getting events for {promotion.name}")
        
        # Create results_list to add found shows to
        results_list = []

        for date in date_list:

            logging.info(f"Grabbing web data to be scraped for {promotion.name}, {date}")
            
            # Build url based on promotion and date
            url = f"https://www.cagematch.net/{promotion.cagematch_id}&page=8&name=&vDay={date.split('.')[0]}&vMonth={date.split('.')[1]}&vYear={date.split('.')[2]}&showtype=&location=&arena=&region="
            logging.debug(f"scrape url: {url}")
            
            logging.info("Looking for events in the data")
            
            # Find the table of events for the date (usually one per day but can be multiple)
            events_table = BeautifulSoup(requests.get(url, headers={'Accept-Encoding': 'identity'}).text, "lxml").find('div', {'class': 'TableContents'})
            
            if events_table:
                logging.info(f"Pulling the shows for {date}")

                # Find each show in the table for the date
                shows = events_table.find_all('div', {'class': 'QuickResults'})
                
                for show in shows:
                    logging.info(f"Found a show, gathering info")
                    show_dict = {}
                    show_dict['title'] = show.find('div', {'class': 'QuickResultsHeader'}).text.strip()
                    show_dict['date'] = date
                    logging.info(f"Found show {show_dict['title']}, {show_dict['date']}")

                    logging.info(f"Finding match results for show {show_dict['title']}")
                    results = show.find_all('span', {'class': 'MatchResults'})
                    match_list = []
                    
                    for result in results:
                        logging.info(f"Found matched result {result.text}")
                        match_list.append(result.text)
                    
                    logging.debug(match_list)
                    show_dict['results'] = match_list
                    logging.debug(show_dict)
                    results_list.append(show_dict)

            else:
                logging.info(f"No events found for {promotion.name}, {date}")
        
        if results_list:

            logging.info("Running cleaners on event and result texts")
            self.clean_titles(results_list)
            self.clean_results(results_list)
            logging.debug(results_list)

            return results_list

    def clean_titles(self, results_list):
        """
        Clean up and standardise the titles of shows found by the scraper

        Parameters
        ----------
        result_list : list
            List of shows and their results, each show is a dict
        """
        logging.info("Formatting show titles")

        for show in results_list:
            logging.info(f"Formatting {show['title']}")
            show['location'] = show['title'].split('@ ')[1]
            show['title'] = show['title'].replace("- Event @", "@")
            show['title'] = show['title'].replace("- TV-Show @", "@")
            show['title'] = show['title'].split(') ', 1)[1].split('@')[0]
            show['title'] = show['title'].replace("- Tag ", "- Day ")
            show['title'] = show['title'].replace("Runde ", "Round ")
            logging.info(f"Finished formatting {show['title']}")

    def clean_results(self, results_list):
        """
        Clean up and standardise the text of results found by the scraper

        Parameters
        ----------
        result_list : list
            List of shows and their results, each show is a dict
        """
        logging.info("Formatting match results")
        
        for show in results_list:
            logging.info(f"Formatting match results for {show['title']}")
            for i in range(len(show['results'])):
                logging.info(f"Formatting match result {show['results'][i]}")
                show['results'][i] = show['results'][i].replace("TITLE CHANGE !!!", "<b>TITLE CHANGE</b>")
                logging.info(f"Finished formatting match result {show['results'][i]}")