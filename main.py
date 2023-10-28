from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from dotenv import dotenv_values
import stripe
from utils.Stripe_API import Stripe_API
from utils.Caspio_API import Caspio_API
import datetime
import json

app = Flask(__name__)
config = dict(dotenv_values('.env'))
stripe.api_key = config["stripeSecretKey"]
endpoint_secret = config["signingSecret"]
caspioEndpoint = '/v2/tables/DP_Payment_Logs/records'
environment = "Prod"

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
                app.logger.info(f'Successfully Updated user {record["Email"]} with Data: {data}')
            else: 
                app.logger.error(response.status_code)
                app.logger.error(f'User {record["Email"]} with Data: {data} Is not updated in the database\nResponse: {response.text}')
            return response
    
        
    # If email does not exists on Caspio, post a new user.
    response = caspioAPI.post(endpoint, data)
    if response.status_code == 201:
        print(response.status_code)
        app.logger.info(f'Successfully Created A new User with Data: {data}')
    else:
        app.logger.info(f"{response.status_code} {response.text}")
    return response

def updateUser(data: dict, endpoint: str, caspioAPI: Caspio_API, stripeAPI: Stripe_API):
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
                app.logger.info(f'Successfully Updated user {record["Email"]} with Data: {data}')
            else: 
                app.logger.error(response.status_code)
                app.logger.error(f'User {record["Email"]} with Data: {data} Is not updated in the database\nResponse: {response.text}')
            return response
    app.logger.info(f"There are no records in caspio that exists with customerID: {data['CustomerID']}")
    return 400

@app.route('/', methods=['GET'])
def homePage():
    return render_template(f'index{environment}.html')

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

@app.route('/live/dispositionPro/subscriptions', methods=['POST'])
def dispositionProSubscriptions():
    StripeAPI = Stripe_API(secretKey=config[f"stripeDispositionProSecretKey{environment}"])
    CaspioAPI = Caspio_API(envPath=config['envPath'],
                           clientID=config['ClientID'],
                           clientSecret=config['ClientSecret'],
                           accessTokenURL=config['accessTokenURL'],
                           refreshToken=config['refreshToken'],
                           bearerAccessToken=config['bearerAccessToken'],
                           apiURL=config['apiURL'])
    stripe.api_key = config[f"stripeDispositionProSecretKey{environment}"]
    endpoint_secret = config[f"stripeDispositionProSigningSecret{environment}"]
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


    app.logger.info(event['type'])
    match event['type']:
        case 'customer.subscription.deleted':
            subscriptionObject = event['data']['object']
            invoiceObject = StripeAPI.getInvoiceObject(subscriptionObject['latest_invoice'])
            UserPayload = {
                "CustomerID": subscriptionObject['customer'],
                "Status": subscriptionObject['status']       
            }
            app.logger.info(UserPayload)
            updateUser(
                data=UserPayload, 
                endpoint=caspioEndpoint, 
                caspioAPI=CaspioAPI, 
                stripeAPI=StripeAPI
            )
        case 'invoice.paid':
            invoiceObject = event['data']['object']
            if invoiceObject['amount_due'] > 0:
                app.logger.info(f"Invoice ID: {invoiceObject['id']} | Customer Email: {invoiceObject['customer_email']} | Amount Due: {invoiceObject['amount_due']} | Amount Paid: {invoiceObject['amount_paid']}")
                subscriptionObject = StripeAPI.getSubscriptionObject(invoiceObject['subscription'])
                UserPayload = {
                    'Email': invoiceObject['customer_email'],
                    'CustomerID': invoiceObject['customer'],
                    'UnitsPurchased': subscriptionObject['quantity'],
                    'Status': subscriptionObject['status']
                }
                mergeUser(
                    data=UserPayload,
                    endpoint=caspioEndpoint,
                    caspioAPI=CaspioAPI,
                    stripeAPI=StripeAPI
                )
            else:
                app.logger.info("Do Not Change Units No Charge")
        case 'customer.subscription.updated':
            subscriptionObject = event['data']['object']
            #print(json.dumps(subscriptionObject, indent=4))
            unixTime = subscriptionObject['cancel_at']
            if subscriptionObject['cancel_at'] != None:
                datetime_obj = datetime.datetime.utcfromtimestamp(unixTime)
                formatted_date = datetime_obj.strftime('%m/%d/%Y')
                UserPayload = {
                    "CustomerID": subscriptionObject['customer'],
                    "EndDate": formatted_date    
                }
                updateUser(
                    data=UserPayload,
                    endpoint=caspioEndpoint,
                    caspioAPI=CaspioAPI,
                    stripeAPI=StripeAPI
                )
            else: 
                UserPayload = {
                    "CustomerID": subscriptionObject['customer'],
                    "EndDate": ""    
                }
                updateUser(
                    data=UserPayload,
                    endpoint=caspioEndpoint,
                    caspioAPI=CaspioAPI,
                    stripeAPI=StripeAPI
                )
    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200

@app.errorhandler(404) 
def not_found(e): 
    try:
        UserMachine = request.headers["User-Agent"]
    except:
        UserMachine = ""
    try:
        requestIP = request.headers["X-Real-Ip"]
    except:
        requestIP = ""
    app.logger.info(f"Nerd Using {UserMachine}. From IP: {requestIP}")
    return {"Message": f"Stop"}, 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)





