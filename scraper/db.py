# External Imports
import os
from pymongo import MongoClient

class Connector:

    def __init__(self, table):
        self.client = MongoClient("mongodb+srv://" + os.environ['DBUSER'] + ":" + os.environ['DBPASS'] + "@" + os.environ['DBURL'] + "?retryWrites=true&w=majority")
        self.db = self.client.puroview
        self.table = self.db[table]

    def post(self, post_data):
        result = self.table.insert_one(post_data)
        return result.inserted_id

    def find(self, find_data, find_filter=None):
        if find_filter:
            result = self.table.find(find_data, find_filter)
        else:
            result = self.table.find(find_data)
        return result
        
    def update(self, update_filter, update_data):
        result = self.table.update_one(update_filter, {"$set": update_data}, upsert=True)
        return result.upserted_id

    def distinct(self, find_data):
        result = self.table.distinct(find_data)
        return result