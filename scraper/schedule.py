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
        
        # URL for the english puwota site
        self.puwota_url = "https://en.puwota.com"
        logging.debug(f"URL: {self.puwota_url}")

        # Set up requests session - puwota is quite strict with rate limiting so set retries accordingly
        logging.info("Setting requests session parameters")
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.keep_alive = False

        # Build a string of today's date for finding the relevant elements
        logging.info("Setting today's date")
        # Uncomment to set a specific day, eg for testing
        #self.today = "2022-01-22"
        # Otherwise use below to pull today's date
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
        # Build BS object
        logging.info("Retrieving page data")
        page = self.session.get(self.puwota_url)
        soup = BeautifulSoup(page.text, "html.parser")

        # Find today's shedule by locating the <script> with today's date in
        # Puwota colours the sections according to type of promotion, so find color01 (puro) and color02 (joshi)
        logging.info("Finding today's schedule")
        shows = soup.find('script', string=re.compile(self.today)).find_next("ul").find_all("div", ["color01", "color02"])
        logging.debug(f"Schedule source data: {shows}")

        # Build the empty show_list for the dictionaries to be stored in
        logging.debug("Creating empty show_list")
        show_list = []

        logging.info("Finding shows in today's schedule")

        # "show" is the li element found matching the color0X class
        # Example: <li class="cname_a color01">New Japan</li>
        for show in shows:
            
            # Show time, location etc is hyperlinked in the next li element down from "show"
            # Example: <a href="https://www.njpw.co.jp/schedule" rel="nofollow" target="_blank">18:00 Hokkaido<br/>Makomanai Sekisui Heim Ice Arena</a>
            show_info = show.find_next("div").find("a")
            logging.debug(f"show_info: {show_info}")

            # Build a list from the text found in the hyperlink
            # Time and city are on one line, then venue (if any) on the next
            show_text = [text for text in show_info.stripped_strings]
            logging.debug(f"show_text: {show_text}")
            
            # Build the dictionary for the show details to be held in
            show_dict = {}

            # Get the promotion name from the text of "show"
            # This should always exist at the mimimum, but catch errors to prevent crashes
            try:
                show_dict['promotion'] = show.get_text()
                logging.info(f"Promotion name: {show_dict['promotion']}")
            except Exception as e:
                logging.error(e)
            
            # Set the link by pulling the href from the "show_info" element
            # Catch errors in case there is no link (puwota removes links after the date has passed, so this probably depends on timing)
            try:
                show_dict['link'] = show_info['href']
                logging.info(f"Show link: {show_dict['link']}")
            except Exception as e:
                logging.warning(f"No link found for {show_dict['promotion']}")
                logging.error(e)

            # Set the show time by pulling it from the text and catch errors if it doesn't exist
            try:
                show_dict['time'] = show_text[0].split()[0]
                logging.info(f"Show time: {show_dict['time']}")
            except IndexError as e:
                logging.warning(f"No time found for {show_dict['promotion']}")
                logging.error(e)

            # Set the show location/city by pulling it from the text and catch errors if it doesn't exist
            # If the show is live stream only, that is found here
            try:
                show_dict['location'] = show_text[0].split()[1]
            except IndexError as e:
                logging.warning(f"No location found for {show_dict['promotion']}")
                logging.error(e)

            # Set the show venue by pulling it from the text and catch errors if it doesn't exist
            # Venue often doesn't exist, especially for smaller shows
            try:
                show_dict['venue'] = show_text[1]
            except IndexError as e:
                logging.warning(f"No venue found for {show_dict['promotion']}")
                logging.error(e)

            # Set show date as today. This is a string now and set as a datetime when added to the DB
            show_dict['date'] = self.today
            
            logging.info(f"Found show: {show_dict['promotion']}, {show_dict['time']}")
            logging.debug(f"show_dict: {show_dict}")
            
            logging.debug("Adding show to show_list")

            # Add the show dictionary to the list of shows to be returned
            # If the dict doesn't have a "promotion" key, this one was likely picked up due to a parsing error
            if show_dict['promotion']:
                show_list.append(show_dict)
        
        # Return the list of show dicts
        return show_list

    def clean_schedule(self, show_list):
        """
        Clean up and standardise the format of text in the schedule data

        Parameters
        ----------
        show_list
            List of shows dicts, produced by the scraper
        
        Returns
        -------
        show_list
            List of shows with formatted and standardised text
        """        
        logging.info("Cleaning up formatting of show text")
        logging.debug(f"show_list: {show_list}")

        # For each show in the list, there are some common replacements due to formatting on puwota that isn't common in english speaking usage
        for show in show_list:
            # For each show in the list, there are some common replacements due to formatting on puwota that isn't common in english speaking usage
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

            if show["promotion"] == "Ryukyu":
                show["promotion"] = "Ryukyu Dragon Pro Wrestling"

            if show["promotion"] == "Shinshu":
                show["promotion"] = "Shinshu Pro Wrestling Federation"

            # Set title case for the promotion name, unless it is already all caps (ie DDT)
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

                # ChocoPro shows are formatted differently on puwota, we standardise it here
                if show["venue"] == "ChocoPro":
                    show["promotion"] = "ChocoPro"
                    show["location"] = "Tokyo"
                    show["venue"] = "Ichigaya Chocolate Square"

        logging.debug(f"Cleaned show_list: {show_list}")
        return show_list

    def update_db(self, show_list):
        """
        Insert the found scheduled shows into the database
        
        Parameters
        ----------
        show_list
            List of shows with formatted and standardised text
        """
        logging.info("Adding shows to database")
        
        # For each show in the list, add it to the DB
        for show in show_list:
            # If show isn't already in DB, save it
            # Query has to be based on promotion, date AND time at minimum in case of 2 shows from one promotion in a day
            if not Schedule.objects(promotion=show['promotion'], date=show['date'], time=show['time']):
                db_show = Schedule(**show).save()
                logging.info(f"Saved document ID {db_show.id} for  {show['promotion']}, {show['time']}")

            # If the show is already present in the DB, update it incase the script is being re-run on a specific day
            # Run an update in case of changes since the last time the scraper ran (or changes were made to the clean_schedule method)
            else:
                update = Schedule.objects(promotion=show['promotion'], date=show['date'], time=show['time']).update(**show, full_result=True)
                if update.modified_count > 0:
                    logging.info(f"Updated DB entry for {show['promotion']}, {show['time']}")
                else:
                    logging.info(f"DB entry exists for {show['promotion']}, {show['time']}")

