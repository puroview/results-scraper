# External Imports
import logging
import requests
import string
from bs4 import BeautifulSoup

# Internal Imports
from models import Promotions

## Classes
# PromotionsScraper Class
class PromotionsScraper:
    """
    A class for the results scraper, with methods for retrieving webscraped data and saving to the database

    Attributes
    ----------
    promotions_page
        URL of the promotions page on cagematch
    
    Methods
    -------
    update_promotions()
        Update the stored list of japanese promotions, adding new ones to the database
    """
    def __init__(self):
        logging.info("Building ResultsScraper object")

        # Url of the cagematch page listing japanese promotions
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
        
        # Build beautifulsoup object
        # Each row in the table is a promotion
        logging.info(f"Scraping promotions page {self.promotions_page}")
        promotions_data = BeautifulSoup((requests.get(self.promotions_page, headers={'Accept-Encoding': 'identity'})).text, "lxml").find('div', {'class': 'TableContents'}).find_all('tr')
        
        logging.info("Finiding promotions within the data")

        # For each row, pull the relevant info about the promotion
        for p in promotions_data:
            logging.info("Found a promotion, gathering info")

            # Create promotion dict
            logging.debug("Building empty promotion dict")
            promotion = {}

            # The 3rd td tag in each row contains the promotion name
            promotion['name'] = p.find_all('td')[2].text
            # Each row includes the link to the promotion's cagematch page, in short form, ie "?id=8&nr=7"
            promotion['cagematch_id'] = p.find('a').get('href')

            # Change general promotion name to something less specific
            if promotion['name'] == "Wrestling In Japan - Freelance Shows":
                promotion['name'] = "Others"

            # Remove spaces and punctuation from the promotion name to make a short name for consistent identification
            promotion['short_name'] = promotion['name'].translate(str.maketrans('', '', string.punctuation))
            promotion['short_name'] = promotion['short_name'].replace(" ", "")
            logging.info(f"Got info for promotion {promotion['name']}")
            logging.debug(f"promotion_info: {promotion}")

            # Ignore the entry with name "Name", this comes from the table header row
            if promotion['name'] != "Name":               
                logging.info(f"Updating database entry for {promotion['name']}")

                # Update/add the promotion into the DB
                update = Promotions.objects(cagematch_id=promotion["cagematch_id"]).update(upsert=True, full_result=True, **promotion)

                if update.modified_count > 0:
                    logging.info(f"Updated DB entry for {promotion['name']}")
                else:
                    logging.info(f"DB entry exists for {promotion['name']}")