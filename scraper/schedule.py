# External Imports
import re
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import date

# Internal Imports
from models import Schedule


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
        logging.info(f"Date: {self.today}")

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
            
            show_dict = {}

            try:
                show_dict['promotion'] = show.get_text()
            except Exception as e:
                logging.warning(e)
            
            try:
                show_dict['link'] = show_info['href']
            except Exception as e:
                logging.warning(f"No link found for {show_dict['promotion']}")
                logging.error(e)

            try:
                show_dict['time'] = show_text[0].split()[0]
            except IndexError as e:
                logging.warning(f"No time found for {show_dict['promotion']}")
                logging.error(e)

            try:
                show_dict['location'] = show_text[0].split()[1]
            except IndexError as e:
                logging.warning(f"No location found for {show_dict['promotion']}")
                logging.error(e)

            try:
                show_dict['venue'] = show_text[1]
            except IndexError as e:
                logging.warning(f"No venue found for {show_dict['promotion']}")
                logging.error(e)

            show_dict['date'] = self.today

            logging.debug(f"show_dict: {show_dict}")

            logging.info(f"Found show: {show_dict['promotion']}, {show_dict['time']}")
            
            logging.debug("Adding show to show_list")
            show_list.append(show_dict)
        
        return show_list

    def clean_schedule(self, show_list):
        """
        Clean up and standardise the format of text in the schedule data
        
        Returns
        -------
        show_list
            List of shows with formatted and standardised text
        """        
        logging.info("Cleaning up formatting of show text")
        for show in show_list:
            if show["location"] == "webcast":
                logging.debug(f"Replacing \"webcast\" with \"Live Stream\" for show {show['promotion']} {show['time']}")
                show["location"] = "Live Stream"

            if show["promotion"] == "Tokyo Womans":
                show["promotion"] = "Tokyo Joshi Pro"

            if show["promotion"] == "2AW(KDOJO)":
                show["promotion"] = "2AW"

            if show["promotion"] == "Michinoku":
                show["promotion"] = "Michinoku Pro"

            if show["promotion"] == "New Japan":
                show["promotion"] = "New Japan Pro Wrestling"

            logging.debug(f"Setting title case on promotion name for show {show['promotion']} {show['time']}")
            if "promotion" in show.keys() and not show['promotion'].isupper():
                show["promotion"] = show["promotion"].title()
            
            # Title case location and venue, but ignore all caps words, ie Shinjuku FACE
            logging.debug(f"Setting title case on location name for show {show['promotion']} {show['time']}")
            if "location" in show.keys():
                show["location"] = ' '.join([word.title() if word.islower() else word for word in show["location"].split()])
            logging.debug(f"Setting title case on venue name for show {show['promotion']} {show['time']}")
            if "venue" in show.keys():
                show["venue"] = ' '.join([word.title() if word.islower() else word for word in show["venue"].split()])

        return show_list

    def update_db(self, show_list):
        """
        Insert the found scheduled shows into the database
        """   
        logging.debug(f"show_list: {show_list}")
        
        for show in show_list:
            if not Schedule.objects(promotion=show['promotion'], date=show['date'], time=show['time']):
                db_show = Schedule(**show).save()
                logging.info(f"Saved document ID {db_show.id} for  {show['promotion']}, {show['time']}")
            else:
                update = Schedule.objects(promotion=show['promotion'], date=show['date'], time=show['time']).update(**show, full_result=True)
                if update.modified_count > 0:
                    logging.info(f"Updated DB entry for {show['promotion']}, {show['time']}")
                else:
                    logging.info(f"DB entry exists for {show['promotion']}, {show['time']}")

