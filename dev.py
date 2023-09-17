# app.py
#
# Use this sample code to handle webhook events in your integration.
#
# 1) Paste this code into a new file (app.py)
#
# 2) Install dependencies
#   pip3 install flask
#   pip3 install stripe
#
# 3) Run the server on http://localhost:4242
#   python3 -m flask run --port=4242

import json
import os
import stripe
import requests
from dotenv import dotenv_values
from utils.Stripe_API import Stripe_API
from utils.Caspio_API import Caspio_API

from flask import Flask, jsonify, request

config = dotenv_values(".env")



app = Flask(__name__)

StripeAPI = Stripe_API(config)
CaspioAPI = Caspio_API(config)

endpoint_secret = 'whsec_d07e3db61c55e1b808a9330eafa081b8386d7958aa5e059260f5e34f50d41c65'

stripe.api_key = config["stripeSecretKey"]


@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    event_types = set({'customer.subscription.created','customer.subscription.deleted','customer.subscription.updated'})

    if event['type'] in event_types: 
        UserSubscriptionPayload = StripeAPI.handleSubscriptionEvent(event)
        CaspioAPI.mergeUser(UserSubscriptionPayload, '/v2/tables/Python_Dev_TitlePro_PaymentLogs/records')
            
    

    
    return jsonify(success=True)

app.run(host="127.0.0.1", port=4242)