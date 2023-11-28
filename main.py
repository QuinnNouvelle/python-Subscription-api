import logging
import datetime
from flask import Flask, render_template, request
from dotenv import dotenv_values
import stripe
from utils.Stripe_API import Stripe_API
from utils.Caspio_API import Caspio_API, NoUsersToUpdate



app = Flask(__name__)
config = dict(dotenv_values('.env'))
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


def DP_invoice_paid(invoiceObject: dict, endpoint: str, stripeAPI: Stripe_API, caspioAPI: Caspio_API):
    """The Main logic for the invoice.paid trigger coming from Stripe. For DispositionPro

    Args:
        invoiceObject (dict): https://stripe.com/docs/api/invoices/object
        stripeAPI (Stripe_API): Instance of Stripe_API class
        caspioAPI (Caspio_API): Instance of Caspio_API class
    """
    if invoiceObject['amount_due'] > 0:
        subscriptionObject = stripeAPI.getSubscriptionObject(invoiceObject['subscription'])
        UserPayload = {
            'Email': invoiceObject['customer_email'],
            'CustomerID': invoiceObject['customer'],
            'UnitsPurchased': subscriptionObject['quantity'],
            'Status': subscriptionObject['status']
        }
        app.logger.info(f"Invoice ID: {invoiceObject['id']} | Amount Due: {invoiceObject['amount_due']} | Amount Paid: {invoiceObject['amount_paid']} | Payload: {UserPayload}")
        try:
            response = caspioAPI.mergeUser(data=UserPayload, endpoint=endpoint)

            if response.status_code in {200, 201}:
                app.logger.info("MERGE SUCCESS")
            else:
                app.logger.error("MERGE FAILED")
                app.logger.error(f"{response.status_code} {response.text}")
                app.logger.error(f"Make sure that {UserPayload} is added to Caspio")
        except Exception as e:
            app.logger.error(f"MERGE FAILED: {e}")
            app.logger.error(f"Make sure that {UserPayload} is added to Caspio")
    else:
        app.logger.info("Do Not Change Units No Charge")

def TP_invoice_paid(invoiceObject: dict, stripeAPI: Stripe_API, endpoint: str, caspioAPI: Caspio_API):
    """The Main logic for the TitlePro invoice.paid trigger coming from Stripe.

    Args:
        invoiceObject (dict): https://stripe.com/docs/api/invoices/object
        stripeAPI (Stripe_API): Instance of Stripe_API class
        caspioAPI (Caspio_API): Instance of Caspio_API class
    """
    if invoiceObject['amount_due'] > 0:
        subscriptionObject = stripeAPI.getSubscriptionObject(invoiceObject['subscription'])
        UserPayload = {
            'Email': invoiceObject['customer_email'],
            'CustomerID': invoiceObject['customer'],
            'Purchased_Seats': subscriptionObject['quantity'],
            'Status': subscriptionObject['status']
        }
        app.logger.info(f"Invoice ID: {invoiceObject['id']} | Amount Due: {invoiceObject['amount_due']} | Amount Paid: {invoiceObject['amount_paid']} | Payload: {UserPayload}")
        try:
            response = caspioAPI.mergeUser(data=UserPayload, endpoint=endpoint)

            if response.status_code in {200, 201}:
                app.logger.info("MERGE SUCCESS")
            else:
                app.logger.error("MERGE FAILED")
                app.logger.error(f"{response.status_code} {response.text}")
                app.logger.error(f"Make sure that {UserPayload} is added to Caspio")
        except Exception as e:
            app.logger.error(f"MERGE FAILED: {e}")
            app.logger.error(f"Make sure that {UserPayload} is added to Caspio")
    else:
        app.logger.info("Do Not Change Seats No Charge")

def customer_subscription_deleted(subscriptionObject: dict, endpoint: str, caspioAPI: Caspio_API):
    """The Main logic for the customer.subscription.deleted trigger coming from Stripe.

    Args:
        subscriptionObject (dict): https://stripe.com/docs/api/subscriptions/object
        caspioAPI (Caspio_API): Instance of Caspio_API Class
    """
    UserPayload = {"Status": subscriptionObject['status']}
    app.logger.info(f"CustomerID: {subscriptionObject['customer']} | Payload: {UserPayload}")
    try:
        response = caspioAPI.updateUser(data=UserPayload, endpoint=endpoint, customerID=subscriptionObject['customer'])
        if response.status_code == 200:
            app.logger.info("UPDATE SUCCESS")
        else:
            app.logger.error("UPDATE FAILED")
            app.logger.error(response.status_code, response.text)
            app.logger.error(f"Make sure CustomerID: {subscriptionObject['customer']} | Gets Payload: {UserPayload}")
    except NoUsersToUpdate:
        app.logger.error("Event: Customer cancellation requested period has ended, the subscription should be canceled but for some reason no users were found in caspio")
    except Exception as e:
        app.logger.error(e)

def customer_subscription_updated(subscriptionObject: dict, endpoint: str, caspioAPI: Caspio_API):
    """The Main logic for the DispositionPro customer.subscription.updated trigger coming from Stripe.

    Args:
        subscriptionObject (dict): https://stripe.com/docs/api/subscriptions/object
        caspioAPI (Caspio_API): Instance of Caspio_API Class
    """
    unixTime = subscriptionObject['cancel_at']
    UserPayload = {}
    if subscriptionObject['cancel_at'] is not None:
        datetime_obj = datetime.datetime.utcfromtimestamp(unixTime)
        formatted_date = datetime_obj.strftime('%m/%d/%Y')
        UserPayload = {"EndDate": formatted_date}   
    else:
        UserPayload = {"EndDate": ""}
    app.logger.info(f"CustomerID: {subscriptionObject['customer']} | Payload: {UserPayload}")
    try:
        response = caspioAPI.updateUser(customerID=subscriptionObject['customer'], data=UserPayload, endpoint=endpoint)
        if response.status_code == 200:
            app.logger.info("UPDATE SUCCESS")
        else:
            app.logger.error(f"UPDATE FAILED | !! Make Sure CustomerID: {subscriptionObject['customer']} | Is updated with Payload: {UserPayload} in Caspio !!")
    except NoUsersToUpdate:
        app.logger.warning(f"No user exists with customerID {subscriptionObject['customer']}")
    except Exception as e:
        app.logger.error(e)

@app.route('/', methods=['GET'])
def homePage():
    ENVIRONMENT = "Prod"
    return render_template(f'index{ENVIRONMENT}.html')


@app.route('/live/dispositionPro/subscriptions', methods=['POST'])
def dispositionProSubscriptions():
    """Main listening endpoint for STRIPE Disposition Pro PROD webhook."""
    dispositionProEndpoint = '/v2/tables/DP_Payment_Logs/records'
    ENVIRONMENT = "Prod"
    stripeAPI = Stripe_API(secretKey=config[f"stripeDispositionProSecretKey{ENVIRONMENT}"])
    caspioAPI = Caspio_API()
    stripe.api_key = config[f"stripeDispositionProSecretKey{ENVIRONMENT}"]
    endpoint_secret = config[f"stripeDispositionProSigningSecret{ENVIRONMENT}"]
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        app.logger.warning(e)
        app.logger.warning(f'Invalid Payload From: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid payload'}, 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.warning(e)
        app.logger.warning(f'Invalid Stripe Signature from: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid signature'}, 400


    match event['type']:
        case 'customer.subscription.deleted':
            customer_subscription_deleted(subscriptionObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI)
        case 'invoice.paid':
            DP_invoice_paid(invoiceObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI, stripeAPI=stripeAPI)
        case 'customer.subscription.updated':
            customer_subscription_updated(subscriptionObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI)


    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200

@app.route('/test/dispositionPro/subscriptions', methods=['POST'])
def test_dispositionProSubscriptions():
    """Test listening endpoint for STRIPE Disposition Pro DEV webhook."""
    dispositionProEndpoint = '/v2/tables/Python_DP_PaymentLogs/records'
    ENVIRONMENT = "Dev"
    stripeAPI = Stripe_API(secretKey=config[f"stripeDispositionProSecretKey{ENVIRONMENT}"])
    caspioAPI = Caspio_API()
    stripe.api_key = config[f"stripeDispositionProSecretKey{ENVIRONMENT}"]
    endpoint_secret = config[f"stripeDispositionProSigningSecret{ENVIRONMENT}"]
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        app.logger.warning(e)
        app.logger.warning(f'Invalid Payload From: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid payload'}, 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.warning(e)
        app.logger.warning(f'Invalid Stripe Signature from: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid signature'}, 400


    match event['type']:
        case 'customer.subscription.deleted':
            customer_subscription_deleted(subscriptionObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI)
        case 'invoice.paid':
            DP_invoice_paid(invoiceObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI, stripeAPI=stripeAPI)
        case 'customer.subscription.updated':
            customer_subscription_updated(subscriptionObject=event['data']['object'], endpoint=dispositionProEndpoint, caspioAPI=caspioAPI)


    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200

@app.route('/test/titlePro/subscriptions', methods=['POST'])
def test_titleProSubscriptions():
    """Test listening endpoint for STRIPE TitlePro DEV webhook."""
    titleProEndpoint = '/v2/tables/Python_Dev_TitlePro_PaymentLogs/records'
    ENVIRONMENT = "Dev"
    stripeAPI = Stripe_API(secretKey=config[f"stripeTitleProSecretKey{ENVIRONMENT}"])
    caspioAPI = Caspio_API()
    stripe.api_key = config[f"stripeTitleProSecretKey{ENVIRONMENT}"]
    endpoint_secret = config[f"stripeTitleProSigningSecret{ENVIRONMENT}"]
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        app.logger.warning(e)
        app.logger.warning(f'Invalid Payload From: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid payload'}, 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.warning(e)
        app.logger.warning(f'Invalid Stripe Signature from: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid signature'}, 400

    match event['type']:
        case 'customer.subscription.deleted':
            customer_subscription_deleted(subscriptionObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI)
        case 'invoice.paid':
            TP_invoice_paid(invoiceObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI, stripeAPI=stripeAPI)
        case 'customer.subscription.updated':
            customer_subscription_updated(subscriptionObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI)
    
    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200

@app.route('/live/titlePro/subscriptions', methods=['POST'])
def titleProSubscriptions():
    """Live listening endpoint for STRIPE TitlePro PROD webhook."""
    titleProEndpoint = '/v2/tables/TitlePro_PaymentLogs/records'
    ENVIRONMENT = "Prod"
    stripeAPI = Stripe_API(secretKey=config[f"stripeTitleProSecretKey{ENVIRONMENT}"])
    caspioAPI = Caspio_API()
    stripe.api_key = config[f"stripeTitleProSecretKey{ENVIRONMENT}"]
    endpoint_secret = config[f"stripeTitleProSigningSecret{ENVIRONMENT}"]
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        app.logger.warning(e)
        app.logger.warning(f'Invalid Payload From: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid payload'}, 400

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.warning(e)
        app.logger.warning(f'Invalid Stripe Signature from: {request.remote_addr}')
        return {'status': 'error', 'message': 'Invalid signature'}, 400

    match event['type']:
        case 'customer.subscription.deleted':
            customer_subscription_deleted(subscriptionObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI)
        case 'invoice.paid':
            TP_invoice_paid(invoiceObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI, stripeAPI=stripeAPI)
        case 'customer.subscription.updated':
            customer_subscription_updated(subscriptionObject=event['data']['object'], endpoint=titleProEndpoint, caspioAPI=caspioAPI)

    return {'status': 'accepted', 'message': 'Webhook Accepted'}, 200


@app.errorhandler(404)
def not_found():
    try:
        UserMachine = request.headers["User-Agent"]
    except Exception:
        UserMachine = ""
    try:
        requestIP = request.headers["X-Real-Ip"]
    except Exception:
        requestIP = ""
    app.logger.info(f"Nerd Using {UserMachine}. From IP: {requestIP}")
    return {"Message": "Stop"}, 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)





