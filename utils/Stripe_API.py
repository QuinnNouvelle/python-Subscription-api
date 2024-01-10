import json
import requests
# The library needs to be configured with your account's secret key.
# Ensure the key is kept out of any version control system you might be using.
class FailedGetRequest(Exception):
    """Throws when get request is not 200, or 201"""



class Stripe_API:

    def __init__(self, secretKey: str):
        self.headers = { "Authorization": f"Bearer {secretKey}"}

    def get(self, endpoint: str) -> dict:
        """Perform a get request to endpoint

        Args: endpoint (str): url endpoint of api get request
        Returns: dict: Json response data turned into a dict.
        """
        
        response = requests.get(f"https://api.stripe.com/{endpoint}", headers=self.headers, timeout=10)
        if response.status_code == 200:
            return dict(json.loads(response.text))
        raise FailedGetRequest(f"{response.status_code} : {response.text}")
            
    def getSubscriptionObject(self, subscriptionID: str) -> dict:
        """Perform a Get request to /v1/subscriptions/id
        https://stripe.com/docs/api/subscriptions/object

        Args: subscriptionID (str): ID of the Stripe Subscription Object
        Returns: dict: Json response data turned into a dict.
        """
        return self.get(f"v1/subscriptions/{subscriptionID}")
    
    def getInvoiceObject(self, invoiceID: str)  -> dict:
        """Perform a Get request to /v1/invoices/id 
        Currently used to retreive: email, billing reason

        Args: invoiceID (str): Stripe Invoice ID
        Returns: dict: Json response data turned into a dict.
        """
        return self.get(f"v1/invoices/{invoiceID}")

