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

secret_token = config['testSecretToken']

stripe.api_key = config["stripeSecretKey"]


@app.route('/webhook/subscriptions', methods=['POST'])
def webhookSubscription():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print(f"Invalid payload: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Signature verification error: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    event_types = set({'customer.subscription.created','customer.subscription.deleted','customer.subscription.updated'})
    if event['type'] in event_types: 
        UserSubscriptionPayload = StripeAPI.handleSubscriptionEvent(event)
        CaspioAPI.mergeUser(UserSubscriptionPayload, '/v2/tables/Python_Dev_TitlePro_PaymentLogs/records')
        
    return jsonify(success=True)

@app.route('/webhook', methods=['POST'])
def webhook():
    received_token = request.headers.get('X-Secret-Token')

    if received_token != secret_token:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json  # Parse JSON data sent by the webhook provider
    except:
        data = ""

    # Process the webhook data here (e.g., save it to a database or perform some action)
    try:
        return jsonify({'message': 'Webhook received successfully'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

app.run(host="127.0.0.1", port=4242)