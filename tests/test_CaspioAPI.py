from utils.Caspio_API import Caspio_API
from dotenv import dotenv_values
import random
import string
import secrets
import json

config = dotenv_values(".env")
CaspioAPI = Caspio_API(config)
testTable = "/v2/tables/Python_Dev_TitlePro_PaymentLogs/records"
plans = ['Gold Plan', 'Silver Plan', 'Bronze Plan']




def test_enviornment_Variable_keys():
    assert CaspioAPI.config == config

def test_enviornment_Variable_values():
    passed = True
    for item in config:
        if CaspioAPI.config[item] != config[item]: passed = False
    assert passed

def test_post_request():
    testUser = {
            "Email": ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(random.randrange(7,20))) + '@mail.com',
            "CID_Stripe": 'cus_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanID": 'prod_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanName": random.choice(plans),
            "Amount": 1500,
            "Reason": "subscription_create",
            "Status": "active"
        }
    response = CaspioAPI.post(testTable, testUser)
    assert response.status_code == 201

def test_get_request():
    response = CaspioAPI.get(testTable)
    Results = json.loads(response.text)['Result']
    assert response.status_code == 200

def test_put_request():
    userUpdate = {
            "PlanName": random.choice(plans),
            "Amount": random.randrange(15,25) * 100,
            "Status": "active"
        }
    response = CaspioAPI.get(testTable)
    Results = json.loads(response.text)['Result']
    maxLength = len(Results)
    PK_ID = Results[random.randrange(0,maxLength)]['PK_ID']
    PUTresponse = CaspioAPI.put(testTable, userUpdate, f'PK_ID={PK_ID}')
    assert PUTresponse.status_code == 200

def test_del_request():
    response = CaspioAPI.get(testTable)
    Results = json.loads(response.text)['Result']
    maxLength = len(Results)
    PK_ID = Results[random.randrange(0,maxLength)]['PK_ID']
    response = CaspioAPI.delete(testTable, f'PK_ID={PK_ID}')
    assert response.status_code == 200

def test_mergeUser_newUser():
    newUser = {
            "Email": ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(random.randrange(7,20))) + '@mail.com',
            "CID_Stripe": 'cus_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanID": 'prod_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanName": random.choice(plans),
            "Amount": random.randrange(15,25) * 100,
            "Reason": "subscription_create",
            "Status": "active"
        }
    
    response = CaspioAPI.mergeUser(newUser)
    assert response.status_code == 201

def test_mergeUser_updateUser():
    newUser = {
            "Email": ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(random.randrange(7,20))) + '@mail.com',
            "CID_Stripe": 'cus_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanID": 'prod_' + ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range (random.randrange(10,20))),
            "PlanName": random.choice(plans),
            "Amount": random.randrange(15,25) * 100,
            "Reason": "subscription_create",
            "Status": "active"
        }
    userUpdate = {
        "Email": newUser['Email'],
        "PlanName": random.choice(plans),
        "Amount": random.randrange(15,25) * 100,
    }
    CaspioAPI.post(testTable,newUser)
    
    response = CaspioAPI.mergeUser(newUser)

    assert response.status_code == 200


