import json
import requests
# The library needs to be configured with your account's secret key.
# Ensure the key is kept out of any version control system you might be using.

class Stripe_API:

    def __init__(self, secretKey: str):
        self.headers = { "Authorization": f"Bearer {secretKey}"}

    def get(self, endpoint: str) -> dict:
        """Perform a get request to endpoint

        Args: endpoint (str): url endpoint of api get request
        Returns: dict: Json response data turned into a dict.
        """
        try:
            response = requests.get(f"https://api.stripe.com/{endpoint}", headers=self.headers, timeout=10)
            return dict(json.loads(response.text))
        except Exception as e:
            return {"Error": True, "Exception" : e}
            
    def getSubscriptionObject(self, subscriptionID: str) -> dict:
        """Perform a Get request to /v1/subscriptions/id

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

