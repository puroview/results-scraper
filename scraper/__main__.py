# External imports
import os
import logging
import argparse 
from datetime import datetime, timedelta
from mongoengine import connect

# Internal Imports
from notifier import Pushover
from results import ResultsScraper
from schedule import ScheduleScraper
from promotions import PromotionsScraper

## Configure Logging

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('scraper.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s# %(message)s', datefmt='%d.%m.%y-%H:%M:%S')
f_format = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s# %(message)s', datefmt='%d.%m.%y-%H:%M:%S')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
# Level also set here as logs weren't being output without it
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[c_handler, f_handler]
    )

## Parse Arguments
parser = argparse.ArgumentParser(description="Puroview scraper")

# Set mutually exclusive arguments
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--promotions", action="store_true", help="Updates promotions listed on cagematch")
group.add_argument("--results", action="store_true", help="Daily results scraper")
group.add_argument("--schedule", action="store_true", help="Daily schedule scraper")

# Parse arguments
args = parser.parse_args()

# Create pushover notifier
pushover = Pushover()

# Establish connection to the mongodb cluster
# http://docs.mongoengine.org/apireference.html?highlight=connect#mongoengine.connect
connect(host=os.environ['DBURL'])

# Run script based on provided arguments
# Promotions scraper
if args.promotions:
    logging.info("Launching promotions scraper")
    scraper = PromotionsScraper()
    scraper.update_promotions()


# Results scraper
if args.results:
    logging.info("Launching results scraper")
    
    #Instantiate an instance of the ResultsScraper class
    scraper = ResultsScraper()

    # Build a list of the dates for the last 7 days
    date_list = [(datetime.today() - timedelta(days=x)).strftime('%d.%m.%Y') for x in reversed(range(7))]
    logging.debug(f"date_list: {date_list}")

    # Run the event scraper and store the returned string
    updated_events = scraper.update_events(date_list)

    # Build notifiers
    logging.info("Sending notifications")

    # Send message based on whether updated_events contains any entries
    if updated_events:
        pushover.push_message('Results Scraper complete, added shows:\n' + updated_events)
    else:
        pushover.push_message('Results Scraper complete, no shows added.')

# Schedule scraper
if args.schedule:
    logging.info("Launching schedule scraper")

    # Instantiate an instance of the ScheduleScraper class
    scraper = ScheduleScraper()

    # Scrape scheduled shows and add to the database
    show_list = scraper.get_today_schedule()
    show_list = scraper.clean_schedule(show_list)
    scraper.update_db(show_list)

    # Sent a pushover with the scraped shows
    updated_shows = '\n'.join(s['promotion'] + ", " + s['time'] for s in show_list)

    if show_list:
        pushover.push_message('Schedule scraper complete, added shows:\n' + updated_shows)
    else:
        pushover.push_message('Schedule scraper complete, no shows added.')
