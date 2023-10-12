from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from dotenv import dotenv_values
import stripe
from utils.Stripe_API import Stripe_API
from utils.Caspio_API import Caspio_API
import json

app = Flask(__name__)
config = dotenv_values('.env')
stripe.api_key = config["stripeSecretKey"]
endpoint_secret = config["signingSecret"]


gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)



# Replace 'your_secret_token' with your actual secret token
secret_token = config['testSecretToken']

def mergeUser(data: dict, endpoint: str, caspioAPI: Caspio_API, stripeAPI: Stripe_API) -> object:
    """Attempts to find user for the new data being submitted via CustomerID.
    If customerID is found the row is updated with information in the dict.
    If no email exists in Caspio Table then create a new record in that table with data.

    Args:
        self (object): Caspio_API Instance.
        data (dict): Key:Value information for user.
        endpoint (str): endpoint url of the table you want to affect

    Returns:
        object: request response object.
    """
    # Get All Records From A Table 
    #print(paymentLog)
    response = caspioAPI.get(endpoint)
    recordsDict = json.loads(response.text)

    # Iterate Through Those Records and update data
    for record in recordsDict['Result']:
        if data['CustomerID'] == record['CustomerID']:
            response = caspioAPI.put(endpoint, data, f"PK_ID={record['PK_ID']}")
            if response.status_code == 201 or response.status_code == 200:
                print(f'Successfully Updated user {record["Email"]} with Data: {data}')
            else: 
                print(response.status_code)
                print(f'ERROR: User {record["Email"]} with Data: {data} Is not updated in the database\nResponse: {response.text}')
            return response
        
    # If email does not exists on Caspio, post a new user.
    response = caspioAPI.post(endpoint, data)
    if response.status_code == 201:
        print(response.status_code)
        print(f'Successfully Created A new User with Data: {data}')
    else:
        print(f"{response.status_code} {response.text}")
    return response

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


# @app.route('/TitlePro/Subscriptions', methods=['POST'])
# def webhookSubscription():
#     StripeAPI = Stripe_API(config)
#     CaspioAPI = Caspio_API(config)
#     event = None
#     payload = request.data
#     sig_header = request.headers['STRIPE_SIGNATURE']

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except ValueError as e:
#         # Invalid payload
#         print(f"Invalid payload: {e}")
#         return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         print(f"Signature verification error: {e}")
#         return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

#     event_types = set({'customer.subscription.created','customer.subscription.deleted','customer.subscription.updated'})
#     if event['type'] in event_types: 
#         UserSubscriptionPayload = StripeAPI.handleSubscriptionEvent(event)
#         response = CaspioAPI.mergeUser(UserSubscriptionPayload)
#         return jsonify({'status': 'accepted', 'message': 'Event Successfully Triggered.'}), response.status_code
    
#     return jsonify({'status': 'accepted', 'message': 'Webhook Accepted'}), 200

@app.route('/test/dispositionPro/subscriptions', methods=['POST'])
def dispositionProSubscriptions():
    StripeAPI = Stripe_API(config=config, secretKey=config["stripeDispositionProSecretKeyDev"])
    CaspioAPI = Caspio_API(config=config)
    stripe.api_key = config["stripeDispositionProSecretKeyDev"]
    endpoint_secret = config["dispositionProStripeTestWebhookSigningSecret"]
    caspioEndpoint = '/v2/tables/Python_DP_PaymentLogs/records'
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        app.logger.warning(f'Invalid Payload From: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid payload'}, 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.warning(f'Invalid Stripe Signature from: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid signature'}, 400

    event_types = set({
        'customer.subscription.deleted'
        #'customer.subscription.updated'
    })
    print(event['type'])
    if event['type'] in event_types: 
        subscriptionObject = event['data']['object']
        invoiceObject = StripeAPI.getInvoiceObject(subscriptionObject['latest_invoice'])
        
        UserPayload = {
            "Email": str(invoiceObject['customer_email'] or 'Error@NoEmailPresent.sad'),
            # "Amount": invoiceObject['total'],
            "CustomerID": subscriptionObject['customer'],
            "UnitsPurchased": subscriptionObject['quantity'],
            "Status": subscriptionObject['status']       
        }
        
        response = mergeUser(
            data=UserPayload, 
            endpoint=caspioEndpoint, 
            caspioAPI=CaspioAPI, 
            stripeAPI=StripeAPI
        )
        
        if response.status_code == 201 or response.status_code == 200:
            app.logger.info("Event Successfully Triggered. Record Successfully Changed.")
            return {'status': 'accepted', 'message': 'Event Successfully Triggered. Record Successfully Changed.'}, response.status_code
        
        else:
            app.logger.error(f"Event Successfully Triggered. Record Failed To Created.\n{response.text}")
            return {'status': 'denied', 'message': 'Event Successfully Triggered. Record Failed To Created.'}
    elif event['type'] == 'invoice.paid':
        invoiceObject = event['data']['object']
        if invoiceObject['amount_due'] > 0:
            subscriptionObject = StripeAPI.getSubscriptionObject(invoiceObject['subscription'])

            UserPayload = {
                'Email': invoiceObject['customer_email'],
                'CustomerID': invoiceObject['customer'],
                'UnitsPurchased': subscriptionObject['quantity'],
                'Status': subscriptionObject['status']
            }

            response = mergeUser(
                data=UserPayload,
                endpoint=caspioEndpoint,
                caspioAPI=CaspioAPI,
                stripeAPI=StripeAPI
            )
        else:
            print("Do Not Change Units No Charge")
        
    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)





