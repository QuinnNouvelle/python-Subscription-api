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

@app.route('/', methods=['GET'])
def homePage():
    return render_template('index.html')

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
        print("Webhook Successfully received")
        app.logger.debug("This is a debug Message")
        app.logger.info("Info Message")
        return jsonify({'message': 'Webhook received successfully'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)





