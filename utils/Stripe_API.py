import stripe
import requests
import json


# The library needs to be configured with your account's secret key.
    # Ensure the key is kept out of any version control system you might be using.

class Stripe_API:
    # This is your Stripe CLI webhook secret for testing your endpoint locally.
    endpoint_secret = 'whsec_d07e3db61c55e1b808a9330eafa081b8386d7958aa5e059260f5e34f50d41c65'

    def __init__(self, config):
        self.config = config
        self.headers = { "Authorization": f"Bearer {config['localStripeSecret']}"}

    def get(self, endpoint: str):
        """Perform a get request to endpoint

        Args:
            endpoint (str): url endpoint of api get request

        Returns:
            dict: Json response data turned into a dict.
        """
    
        response = requests.get(f"https://api.stripe.com/{endpoint}", headers=self.headers)

        return json.loads(response.text)

    def getSubscriptionObject(self, subscriptionID: str):
        """Perform a Get request to /v1/subscriptions/id

        Args:
            subscriptionID (str): ID of the Stripe Subscription Object
        Returns:
            dict: Json response data turned into a dict.
        """
        print("Here you are in the SUBSCRIPTION FUNCTION\n")
        

        response = requests.get(f"https://api.stripe.com/v1/subscriptions/{subscriptionID}", headers=self.headers)

        #print(response.text)

        return json.loads(response.text)
    
    def getInvoiceObject(self, invoiceID: str):
        """Perform a Get request to /v1/invoices/id 
        Currently used to retreive: email, billing reason

        Args:
            invoiceID (str): Stripe Invoice ID
        Returns:
            dict: Json response data turned into a dict.
        """

        print("Here you are in the INVOICE FUNCTION\n")
        
        response = requests.get(f"https://api.stripe.com/v1/invoices/{invoiceID}", headers=self.headers)

        return json.loads(response.text)

    def handleSubscriptionEvent(self, event: dict):
        print(f"Handling event type: {event['type']}")

        # This is a Subscription Object https://stripe.com/docs/api/subscriptions/object
        subscriptionObject = event['data']['object']

        # This is the Invoice Object https://stripe.com/docs/api/invoices/object
        invoiceObject = self.getInvoiceObject(subscriptionObject['latest_invoice'])
        subPlanID = subscriptionObject['plan']['id']

        # This is the Plan Object https://stripe.com/docs/api/plans/object
        planObject = self.get(f"v1/plans/{subPlanID}")

        # This is the Product Object https://stripe.com/docs/api/products/object
        productObject = self.get(f"v1/products/{planObject['product']}")

        relaventPayload = {
            "Email": str(invoiceObject['customer_email'] or 'Error@NoEmailPresent.sad'),
            "CID_Stripe": subscriptionObject['customer'],
            "PlanID": planObject['product'],
            "PlanName": productObject['name'],
            "Amount": subscriptionObject['plan']['amount'],
            "Reason": f"{invoiceObject['billing_reason']} {str(subscriptionObject['cancellation_details']['reason'] or '')}",
            "Status": subscriptionObject['status']
            
        }
        

        print(relaventPayload)
        return relaventPayload

        
        # else:
        #     print(f"Event Type: {event['type']}")


