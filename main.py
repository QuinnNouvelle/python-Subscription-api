from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Use ProxyFix to handle reverse proxy headers (when behind a reverse proxy)
#app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Replace 'your_secret_token' with your actual secret token
secret_token = 'SuperSecretToken'


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
    app.run(host="0.0.0.0", port=5000)





