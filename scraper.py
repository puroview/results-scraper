#! /usr/bin/python3

from bs4 import BeautifulSoup
from promotions import companies
from datetime import datetime, timedelta

import requests
import json


class Promotion:

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.cagematch_id = kwargs['cagematch_id']
        self.events_page = "https://www.cagematch.net/" + self.cagematch_id + "&page=8"
        
        dates = [datetime.today() - timedelta(days=x) for x in range(7)]
        self.date_list = []
        for i in reversed(dates):
            date = i.date().strftime('%d.%m.%Y')
            self.date_list.append(date)
            

    def get_events(self):
        self.results_list = []

        for date in self.date_list:
            
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

                    results = show.find_all('span', {'class': 'MatchResults'})
                    match_list = []
                    for result in results:
                        match_list.append(result.text)
                    
                    show_dict["results"] = match_list
                    
                    self.results_list.append(show_dict)
            else:
                pass
        self.clean_titles()
        return self.results_list

    def clean_titles(self):
        for show in self.results_list:
            show["location"] = show["title"].split('@ ')[1]
            show["title"] = show["title"].replace("- Event @", "@")
            show["title"] = show["title"].replace("- TV-Show @", "@")
            show["title"] = show["title"].split(') ', 1)[1].split('@')[0]
            show["title"] = show["title"].replace("- Tag ", "- Day ")

            



def get_promotions():
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
        promotions.append(prom_dict)

    return promotions

if __name__ == "__main__":
    promotions = get_promotions()

    for prom in promotions:
        prom = Promotion(**prom)
        
        events = prom.get_events()
        if events:
            print(prom.name + " Results:", '\n')
            for event in events:
                print("Event: " + event["title"])
                print("Date: " + event["date"])
                print("Location: " + event["location"])
                results = event["results"]
                for result in results:
                    print(result)
                print("\n")