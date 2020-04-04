from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import json
import string

from db import Connector
import notifier


class Promotion:

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.cagematch_id = kwargs['cagematch_id']
        self.events_page = "https://www.cagematch.net/" + self.cagematch_id + "&page=8"
                

    def get_events(self):
        results_list = []

        for date in date_list:
            
            day = date.split(".")[0]
            month = date.split(".")[1]
            year = date.split(".")[2]

            page = self.events_page + "&name=&vDay={}&vMonth={}&vYear={}&showtype=&location=&arena=&region=".format(day, month, year)

            events = requests.get(page)
            soup = BeautifulSoup(events.text, "lxml")
            
            events_table = soup.find('div', {'class': 'TableContents'})
            
            if events_table:
                shows = events_table.find_all('div', {'class': 'QuickResults'})
                
                for show in shows:
                    show_name = show.find('div', {'class': 'QuickResultsHeader'})
                    show_dict = {}
                    show_name = show_name.text
                    show_dict["title"] = show_name.strip()
                    show_dict["date"] = date
                    print('Found Show - {}'.format(show_dict['title']))

                    results = show.find_all('span', {'class': 'MatchResults'})
                    match_list = []
                    for result in results:
                        match_list.append(result.text)
                    
                    show_dict["results"] = match_list
                    
                    results_list.append(show_dict)
            else:
                pass
        if results_list:
            self.clean_titles(results_list)
            self.clean_results(results_list)
            return results_list

    def clean_titles(self, results_list):
        print("Formatting Show Titles")
        for show in results_list:
            show["location"] = show["title"].split('@ ')[1]
            show["title"] = show["title"].replace("- Event @", "@")
            show["title"] = show["title"].replace("- TV-Show @", "@")
            show["title"] = show["title"].split(') ', 1)[1].split('@')[0]
            show["title"] = show["title"].replace("- Tag ", "- Day ")
            show["title"] = show["title"].replace("Runde ", "Round ")

    def clean_results(self, results_list):
        print("Formatting Match Results")
        for show in results_list:
            for i in range(len(show['results'])):
                show['results'][i] = show['results'][i].replace("TITLE CHANGE !!!", "<b>TITLE CHANGE</b>")


def update_promotions():
    print("Updating Promotion List")
    promotions_page = "https://www.cagematch.net/?id=8&view=promotions&region=&status=aktiv&name=&location=japan"
    soup = BeautifulSoup((requests.get(promotions_page)).text, "lxml")
    table = soup.find('div', {'class': 'TableContents'})
    
    promotions = []
    for prom in table.find_all('tr'):
        prom_dict = {}
        prom_dict["name"] = prom.find_all('td')[2].text
        prom_dict["cagematch_id"] = prom.find('a').get('href')
        if prom_dict['name'] == "Wrestling In Japan - Freelance Shows":
            prom_dict['name'] = "Others"
        prom_dict["short_name"] = prom_dict["name"].translate(str.maketrans('', '', string.punctuation))
        prom_dict["short_name"] = prom_dict["short_name"].replace(" ", "")
        if prom_dict["name"] != "Name":
            promotions.append(prom_dict)

    db = Connector('promotions')

    for prom in promotions:
        inserted_id = db.update({"name": prom["name"]}, prom)
        if inserted_id:
            print("Added New Promtion \"{}\" to DB".format(prom["name"].strip()))

def update_events():
    db_proms = Connector('promotions')
    db_results = Connector('results')

    updated_shows = []

    for prom in db_proms.find({}, {"_id": 0}):
        print("Finding Events for {}".format(prom["name"]))
        prom = Promotion(**prom)
        events = prom.get_events()

        if events:
            for event in events:
                event["promotion"] = prom.name
                inserted_id = db_results.update({"title": event["title"], "date": event["date"]}, event)
                if inserted_id:
                    print('Adding Show {}'.format(event["title"]))
                    print('Inserted ID: ' + str(inserted_id))
                    updated_shows.append(event["promotion"] + " - " + event["title"])
                else:
                    print('Show "{}" already in DB'.format(event["title"].strip()))
        
    return updated_shows


if __name__ == "__main__":
    
    update_promotions()

    dates = [datetime.today() - timedelta(days=x) for x in range(7)]
    date_list = []
    for i in reversed(dates):
        date = i.date().strftime('%d.%m.%Y')
        date_list.append(date)

    updated_shows = update_events()
    updated_shows = '\n'.join(updated_shows)
    notifier = notifier.Notifier()
    if updated_shows:
        notifier.pushover('Scraper complete, added shows:\n' + updated_shows)
    else:
        notifier.pushover('Scraper complete, no shows added.')
