"""
MongoDB models as defined by the Document and DynamicDocument classes
http://docs.mongoengine.org/apireference.html?highlight=connect#documents
"""
from mongoengine import (
    Document, StringField, DateTimeField, BooleanField, URLField, ListField, DynamicDocument
)

class Newsletters(Document):
    url = URLField(required=True, unique=True)
    firstdate = StringField()
    lastdate = StringField()
    week = StringField()
    year = StringField()

    meta = {
        "indexes": ["url"],
        "ordering": ["url"]
    }

class Promotions(Document):
    name = StringField()
    cagematch_id = StringField(required=True, unique=True)
    short_name = StringField()

    meta = {
        "indexes": ["short_name", "cagematch_id"],
        "ordering": ["short_name"],
        "allow_inheritance": True
    }

class Results(Document):
    title = StringField()
    date = StringField()
    location = StringField()
    promotion = StringField()
    results = ListField()

    meta = {
        "indexes": ["date", "title", "promotion"],
        "ordering": ["-date"],
        "allow_inheritance": True
    }

class Schedule(DynamicDocument):
    date = DateTimeField(unique_with=['promotion', 'time'])
    promotion = StringField()
    time = StringField()
    link = StringField()
    location = StringField()
    venue = StringField()

    meta = {
        "allow_inheritance": True
        
    }

class Users(Document):
    email = StringField(required=True, unique=True)
    receives_newsletter = BooleanField()
    confirmed = BooleanField()
    confirmed_on = DateTimeField()

    meta = {
        "indexes": ["email"]
    }

class Replacements(Document):
    category = StringField()
    original = StringField(unique_with=['category'])
    replacement = StringField()