# External Imports
import logging
import http.client
import os
import urllib

## Classes
# Pushover Class
class Pushover():
    """
    A class for a pushover client session, with the ability to push notification messages

    Attributes
    ----------
    token : str
        Pushover API token

    user : str
        Pushover API user

    Methods
    -------
    push_message()
        Push out a notification to the Pushover client
    """
    def __init__(self):
        logging.info("Creating Pushover notifier")
        
        # Get Pushover API credentials from env variables
        logging.info("Grabbing Pushover credentials")

        self.token = os.environ["PUSHOVER_TOKEN"]
        self.user = os.environ["PUSHOVER_USER"]

        logging.debug(f"Pushover Token: ****{self.token[:4]}")
        logging.debug(f"Pushover User: ****{self.user[:4]}")

        logging.info("Finished grabbing Pushover credentials")

    def push_message(self, message):
        """
        Push out a notification to the Pushover client
        
        Parameters
        ----------
        message : str
            The contents of the message to be pushed, as a string
        """
        logging.info("Creating Pushover message")

        # Connect to Pushover API endpoint
        conn = http.client.HTTPSConnection("api.pushover.net:443")

        # Send Pushover message request
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.token,
                         "user": self.user,
                         "message": (message)
                         }),
                     {"Content-type": "application/x-www-form-urlencoded"})

        logging.debug(f"Pushover message: {message}")
        
        # Send the Pushover notification
        logging.info("Sending Pushover notification")
        conn.getresponse()
