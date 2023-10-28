import stripe
import requests
import json
from flask import current_app
from dataclasses import dataclass

# The library needs to be configured with your account's secret key.
    # Ensure the key is kept out of any version control system you might be using.

class Stripe_API:
    # This is your Stripe CLI webhook secret for testing your endpoint locally.
    endpoint_secret = 'whsec_d07e3db61c55e1b808a9330eafa081b8386d7958aa5e059260f5e34f50d41c65'

    def __init__(self, secretKey: str):
        self.headers = { "Authorization": f"Bearer {secretKey}"}

    def get(self, endpoint: str) -> dict:
        """Perform a get request to endpoint

        Args: endpoint (str): url endpoint of api get request
        Returns: dict: Json response data turned into a dict.
        """
    
        response = requests.get(f"https://api.stripe.com/{endpoint}", headers=self.headers)

        return dict(json.loads(response.text))

    def getSubscriptionObject(self, subscriptionID: str) -> dict:
        """Perform a Get request to /v1/subscriptions/id

        Args: subscriptionID (str): ID of the Stripe Subscription Object
        Returns: dict: Json response data turned into a dict.
        """
        response = requests.get(f"https://api.stripe.com/v1/subscriptions/{subscriptionID}", headers=self.headers)
        #print(response.text)

        return dict(json.loads(response.text))
    
    def getInvoiceObject(self, invoiceID: str)  -> dict:
        """Perform a Get request to /v1/invoices/id 
        Currently used to retreive: email, billing reason

        Args: invoiceID (str): Stripe Invoice ID
        Returns: dict: Json response data turned into a dict.
        """
        response = requests.get(f"https://api.stripe.com/v1/invoices/{invoiceID}", headers=self.headers)

        return dict(json.loads(response.text))

