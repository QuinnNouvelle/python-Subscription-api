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

    def __init__(self, config, secretKey):
        self.config = config
        self.headers = { "Authorization": f"Bearer {secretKey}"}

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
        print("Running: getSubscriptionObject()\n")
        

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
        response = requests.get(f"https://api.stripe.com/v1/invoices/{invoiceID}", headers=self.headers)

        return json.loads(response.text)

    def handleSubscriptionEvent(self, event: dict):
        current_app.logger.debug(f"Handling event type: {event['type']}")

        # This is a Subscription Object https://stripe.com/docs/api/subscriptions/object
        subscriptionObject = event['data']['object']

        # This is the Invoice Object https://stripe.com/docs/api/invoices/object
        invoiceObject = self.getInvoiceObject(subscriptionObject['latest_invoice'])
        subPlanID = subscriptionObject['plan']['id']

        # This is the Plan Object https://stripe.com/docs/api/plans/object
        planObject = self.get(f"v1/plans/{subPlanID}")
        current_app.logger.debug(f"{planObject}")

        # This is the Product Object https://stripe.com/docs/api/products/object
        productObject = self.get(f"v1/products/{planObject['product']}")

        relaventPayload = {
            "Email": str(invoiceObject['customer_email'] or 'Error@NoEmailPresent.sad'),
            "CustomerID": subscriptionObject['customer'],
            "PlanID": planObject['product'],
            "PlanName": productObject['name'],
            "Amount": subscriptionObject['plan']['amount'],
            "Reason": f"{invoiceObject['billing_reason']} {str(subscriptionObject['cancellation_details']['reason'] or '')}",
            "Status": subscriptionObject['status']       
        }
        

        current_app.logger.debug(relaventPayload)
        return relaventPayload

    def handleSubscriptionEventDP(self, event: dict):   
        current_app.logger.debug(f"Handling event type: {event['type']}")
        # This is a Subscription Object https://stripe.com/docs/api/subscriptions/object
        subscriptionObject = event['data']['object']

        # DEBUG STATEMENT
        #current_app.logger.debug(f'SUBSCRIPTION OBJECT: {subscriptionObject}')
        # DEBUG STATEMENT

        # This is the Invoice Object https://stripe.com/docs/api/invoices/object
        invoiceObject = self.getInvoiceObject(subscriptionObject['latest_invoice'])
        formattedInvoiceObject = json.dumps(invoiceObject, indent=4)
        current_app.logger.debug(f'INVOICE OBJECT: {formattedInvoiceObject}')
        subscriptionID = subscriptionObject['id']

        # DEBUG STATEMENT
        #current_app.logger.debug(f"PLAN OBJECT: {formattedPlanObject}")
        # DEBUG STATEMENT
        totalAmount = 0
        for line in invoiceObject['lines']['data']:
            totalAmount += line['quantity']
            

        print(f"Amount: {invoiceObject['total']}\nTotalAmount: {totalAmount}\nPreviousAmount: {invoiceObject['lines']['data'][0]['quantity']}")

        relaventPayload = {
            "Email": str(invoiceObject['customer_email'] or 'Error@NoEmailPresent.sad'),
            # "Amount": invoiceObject['total'],
            "CustomerID": subscriptionObject['customer'],
            "SubscriptionID": subscriptionObject['id'],
            "UnitsPurchased": subscriptionObject['quantity'],
            "Reason": f"{invoiceObject['billing_reason']} {str(subscriptionObject['cancellation_details']['reason'] or '')}",
            "Status": subscriptionObject['status']       
        }

        current_app.logger.info(relaventPayload)
        return relaventPayload

