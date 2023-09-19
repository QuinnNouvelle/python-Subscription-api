from utils.Caspio_API import Caspio_API
from dotenv import dotenv_values

config = dotenv_values(".env")
CaspioAPI = Caspio_API(config)

def test_enviornment_Variable_keys():
    assert CaspioAPI.config == config

def test_enviornment_Variable_values():
    passed = True
    for item in config:
        if CaspioAPI.config[item] != config[item]: passed = False
    assert passed

def test_get_request():
    response = CaspioAPI.get('/v2/applications')
    assert response.status_code == 200