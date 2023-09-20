from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from dotenv import dotenv_values
import stripe
from utils.Stripe_API import Stripe_API
from utils.Caspio_API import Caspio_API

app = Flask(__name__)
config = dotenv_values('.env')
stripe.api_key = config["stripeSecretKey"]
endpoint_secret = config["signingSecret"]


gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

StripeAPI = Stripe_API(config)
CaspioAPI = Caspio_API(config)

# Replace 'your_secret_token' with your actual secret token
secret_token = config['testSecretToken']

endpoint_secret = "whsec_d07e3db61c55e1b808a9330eafa081b8386d7958aa5e059260f5e34f50d41c65"

@app.route('/', methods=['GET'])
def homePage():
    return render_template('index.html')

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
        response = CaspioAPI.mergeUser(UserSubscriptionPayload)
        return jsonify({'status': 'accepted', 'message': 'Event Successfully Triggered.'}), response.status_code
    return jsonify({'status': 'accepted', 'message': 'Webhook Accepted'}), 200

app.run(host="127.0.0.1", port=4242)