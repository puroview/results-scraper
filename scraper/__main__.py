# External imports
import logging
import argparse 
from datetime import datetime, timedelta

# Internal Imports
from notifier import Pushover
from results import ResultsScraper
from schedule import ScheduleScraper

## Configure Logging

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('scraper.log')
c_handler.setLevel(logging.INFO)
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
group.add_argument("--results", action="store_true", help="Daily results scraper")
group.add_argument("--schedule", action="store_true", help="Daily schedule scraper")

# Parse arguments
args = parser.parse_args()

# Run script based on provided arguments
# Results scraper
if args.results:
    logging.info("Launching results scraper")
    
    #Instantiate an instance of the ResultsScraper class
    scraper = ResultsScraper()

    # Run the update promotions method
    scraper.update_promotions()

    # Build a list of the dates for the last 7 days
    date_list = [(datetime.today() - timedelta(days=x)).strftime('%d.%m.%Y') for x in reversed(range(7))]

    # Run the event scraper and store the returned string
    updated_events = '\n'.join(scraper.update_events(date_list))

    # Build notifiers
    logging.info("Sending notifications")
    pushover = Pushover()

    # Send message based on whether updated_events contains any entries
    if updated_events:
        pushover.push_message('Scraper complete, added shows:\n' + updated_events)
    else:
        pushover.push_message('Scraper complete, no shows added.')

# Schedule scraper
if args.schedule:
    logging.info("Launching schedule scraper")

    # Instantiate an instance of the ScheduleScraper class
    scraper = ScheduleScraper()

    # Scrape scheduled shows and add to the database
    scraper.update_db()
