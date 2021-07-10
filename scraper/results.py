# External Imports
import logging
import requests
import string
from bs4 import BeautifulSoup

# Internal Imports
from db import Connector
from models import Result, Promotion

## Classes
# Promotion class
class Promotion(Promotion):
    """
    A class for promotions, with methods to find results for a given list of dates, and format the text in the results
    
    Attributes
    ----------
    name : str
        The name of the promotion

    cagematch_id : str
        Unique ID of the promotion on cagematch.net

    events_page : str
        URL of the promotion's cagematch results page

    Methods
    -------
    get_events(date_list)
        Scrape the results for the promotion, for the dates provided
    
    clean_titles(results_list)
        Standardise the formatting of text in the show titles, making some replacements for more reader friendly text

    clean_results(results_list)
        Standardise the formatting of text in the results, making some replacements for more reader friendly text
    """
    def __init__(self, **kwargs):
        logging.info(f"Building promotion object for {kwargs['name']}")

        self.name = kwargs['name']
        logging.debug(f"name: {self.name}")

        self.cagematch_id = kwargs['cagematch_id']
        logging.debug(f"cagematch_id: {self.cagematch_id}")

        self.events_page = "https://www.cagematch.net/" + self.cagematch_id + "&page=8"
        logging.debug(f"events_page: {self.events_page}")
                
    def get_events(self, date_list):
        """Scrape the results for the promotion, for the dates provided

        Parameters
        ----------
        date_list : list
            List of dates to retrieve results for

        Returns
        -------
        results_list
            List of results found for the promotion in the date range
        """
        logging.info(f"Getting events for {self.name}")

        logging.debug("Creating empty results_list dict")
        results_list = []

        for date in date_list:
            logging.info(f"Grabbing web data to be scraped for {self.name}, {date}")
            
            url = self.events_page + f"&name=&vDay={date.split('.')[0]}&vMonth={date.split('.')[1]}&vYear={date.split('.')[2]}&showtype=&location=&arena=&region="
            logging.debug(f"scrape url: {url}")
            
            logging.info("Looking for events in the data")
            events_table = BeautifulSoup(requests.get(url, headers={'Accept-Encoding': 'identity'}).text, "lxml").find('div', {'class': 'TableContents'})
            
            if events_table:
                logging.info(f"Pulling the shows for {date}")
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
                logging.info(f"No events found for {self.name}, {date}")
                pass
        
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


class ResultsScraper:
    """
    A class for the results scraper, with methods for retrieving webscraped data and saving to the database
    
    Methods
    -------
    update_promotions()
        Update the stored list of japanese promotions, adding new ones to the database
    
    update_events()
        For each promotion in the database, search for new results and add to DB
    """
    def __init__(self):
        logging.info("Building ResultsScraper object")

        logging.info("Setting URL of promotions page")
        self.promotions_page = "https://www.cagematch.net/?id=8&view=promotions&region=&status=aktiv&name=&location=japan"
        logging.debug(f"Promotions page URL: {self.promotions_page}")

    def update_promotions(self):
        """
        Update the stored list of japanese promotions, adding new ones to the database

        Parameters
        ----------
        date_list : list
            List of dates to retrieve results for

        Returns
        -------
        results_list : list
            List of results found for the promotion in the date range
        """
        logging.info("Updating promotions")
        
        logging.info(f"Scraping promotions page {self.promotions_page}")
        promotions = BeautifulSoup((requests.get(self.promotions_page, headers={'Accept-Encoding': 'identity'})).text, "lxml").find('div', {'class': 'TableContents'}).find_all('tr')
        
        logging.debug("Building empty promotions list")
        promotion_list = []

        logging.info("Finiding promotions within the data")
        for prom in promotions:
            logging.info("Found a promotion, gathering info")

            logging.debug("Building empty promotion dict")
            promotion_dict = {}

            promotion_dict['name'] = prom.find_all('td')[2].text
            promotion_dict['cagematch_id'] = prom.find('a').get('href')

            if promotion_dict['name'] == "Wrestling In Japan - Freelance Shows":
                promotion_dict['name'] = "Others"

            promotion_dict['short_name'] = promotion_dict['name'].translate(str.maketrans('', '', string.punctuation))
            promotion_dict['short_name'] = promotion_dict['short_name'].replace(" ", "")
            logging.info(f"Got info for promotion {promotion_dict['name']}")

            if promotion_dict['name'] != "Name":
                logging.info("Adding promotion_dict to promotion_list")
                promotion_list.append(promotion_dict)

        for prom in promotion_list:
            logging.info(f"Updating database entry for {prom['name']}")
            inserted_id = self.db_promotions.update({"name": prom['name']}, prom)

            if inserted_id:
                logging.info("Added New Promtion \"{}\" to DB".format(prom['name'].strip()))

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
        
        updated_shows = []

        for promotion in self.db_promotions.find({}, {"_id": 0}):
            logging.info(f"Finding Events for {promotion['name']}")

            logging.debug(f"Creating Promotion object for {promotion['name']}")
            promotion = Promotion(**promotion)
            events = promotion.get_events(date_list)

            if events:
                logging.info(f"Found events for {promotion.name}")

                for event in events:
                    event['promotion'] = promotion.name
                    inserted_id = self.db_results.update({"title": event['title'], "date": event['date']}, event)

                    if inserted_id:
                        logging.info(f"Added Show {event['title']} to database")
                        logging.debug(f"Inserted ID: {str(inserted_id)}")
                        updated_shows.append(event['promotion'] + " - " + event['title'])

                    else:
                        logging.info(f"Show {event['title'].strip()} already in database")

            else:
                logging.info(f"No events found for {promotion.name}")
            
        return updated_shows