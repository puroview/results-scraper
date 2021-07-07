# External Imports
import re
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import date

# Internal Imports
from db import Connector


class ScheduleScraper:
    """
    A class for the schedule scraper, with methods for retrieving webscraped data and saving to the database
    
    Attributes
    ----------
    puwota_url : str
        the current url of the puwota website

    today : str
        generated string of today's date in format %Y-%m-%d

    Methods
    -------
    get_today_schedule()
        Pull today's scheduled shows from the puwota website

    clean_schedule()
        Clean up and standardise the format of text in the schedule data

    update_db()
        Insert the found scheduled shows into the database
    """
    def __init__(self):
        logging.info("Building schedule scraper")
        
        self.puwota_url = "https://en.puwota.com"
        logging.debug(f"URL: {self.puwota_url}")

        logging.info("Setting requests session parameters")
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.keep_alive = False

        logging.info("Setting today's date")
        self.today = date.today().strftime('%Y-%m-%d')
        logging.debug(f"Date: {self.today}")

    def get_today_schedule(self):
        """
        Pull today's scheduled shows from the puwota website
        
        Returns
        -------
        show_list
            List of shows found in the web scrape
        """
        logging.info("Retrieving page data")
        page = self.session.get(self.puwota_url)
        soup = BeautifulSoup(page.text, "html.parser")

        logging.info("Finding today's schedule")
        shows = soup.find('script', string=re.compile(self.today)).find_next("ul").find_all("li", ["color01", "color02"])
        logging.debug(f"Schedule source data: {shows}")

        logging.debug("Creating empty show_list")
        show_list = []

        logging.info("Finding shows in today's schedule")
        for show in shows:
            show_info = show.find_next("li").find("a")
            logging.debug(f"show_info: {show_info}")
            show_text = [text for text in show_info.stripped_strings]
            logging.debug(f"show_text: {show_text}")
            show_dict = {
                "promotion": show.get_text(),
                "link": show_info['href'],
                "time": show_text[0].split()[0],
                "location": show_text[0].split()[1],
                "venue": show_text[1]
            }
            logging.debug(f"show_dict: {show_dict}")

            logging.info(f"Found show: {show_dict['promotion']}, {show_dict['time']}, {show_dict['location']}, {show_dict['venue']}")
            
            logging.debug("Adding show to show_list")
            show_list.append(show_dict)
        
        return show_list

    def clean_schedule(self):
        """
        Clean up and standardise the format of text in the schedule data
        
        Returns
        -------
        show_list
            List of shows with formatted and standardised text
        """
        logging.info("Retrieving today's scheduled shows")
        show_list = self.get_today_schedule()
        
        logging.info("Cleaning up formatting of show text")
        for show in show_list:
            if show["location"] == "webcast":
                logging.debug(f"Replacing \"webcast\" with \"Live Stream\" for show {show['promotion']} {show['time']}")
                show["location"] = "Live Stream"

            logging.debug(f"Setting title case on promotion name for show {show['promotion']} {show['time']}")
            show["promotion"] = show["promotion"].title()
            logging.debug(f"Setting title case on location name for show {show['promotion']} {show['time']}")
            show["location"] = show["location"].title()
            logging.debug(f"Setting title case on venue name for show {show['promotion']} {show['time']}")
            show["venue"] = show["venue"].title()

        return show_list

    def update_db(self):
        """
        Insert the found scheduled shows into the database
        """
        logging.info("Connecting to db collection \"schedule\"")
        db = Connector('schedule')
        
        show_list = self.clean_schedule()
        logging.debug(f"show_list: {show_list}")
        
        for show in show_list:
            logging.info(f"Inserting/updating db entry for show {show['promotion']} {show['time']}")
            inserted_id = db.update({"date": self.today, "promotion": show["promotion"], "time": show["time"]} ,show)
            logging.debug(f"inserted_id: {inserted_id}")

