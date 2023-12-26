# pylint: disable=logging-fstring-interpolation
# pylint: disable=invalid-name
# pylint: disable=broad-exception-caught
# pylint: disable=protected-access
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
import random
import json
import pytest
from unittest.mock import patch, mock_open
from utils.Caspio_API import Caspio_API, NoUsersToUpdate

## They Work Tested 11-20-2023

# def test_Access_Code_Refresh():
#     """Tests if the Caspio_API class still gets the information in the event of an old Access Token Being Used."""

#     caspioAPI = Caspio_API()
#     caspioAPI._bearerAccessToken = "Broken or Old Access Token"
#     response = caspioAPI.get(endpoint="/v2/tables/Python_DP_PaymentLogs/records")
#     assert response.status_code == 200

# def test_Refresh_Code_Refresh():
#     """Tests if the Caspio_API class still gets the information in the event of an Old Refresh Token Being used to change the Access Token"""

#     caspioAPI = Caspio_API()
#     caspioAPI._bearerAccessToken = "Broken Or Old Access Token"
#     caspioAPI._refreshToken = "Broken Or Old Refresh Token"
#     response = caspioAPI.get(endpoint="/v2/tables/Python_DP_PaymentLogs/records")
#     assert response.status_code == 200

##

class MockEnvFile:
    def __init__(self, read_data):
        self.read_data = read_data

    def read(self):
        return self.read_data

    def readlines(self):
        return self.read_data.splitlines(True)

    def write(self, data):
        self.read_data = data

    def writelines(self, lines):
        self.read_data = ''.join(lines)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass



endpoint = "/v2/tables/Python_DP_PaymentLogs/records"

@pytest.fixture
def caspioAPI():
    return Caspio_API()




def test_get_request(caspioAPI):
    """Tests the get request from the Caspio_API to the specified endpoint."""
    response = caspioAPI.get(endpoint)
    assert response.status_code == 200

def test_post_request(caspioAPI):
    """Tests the post request from the Caspio_API to the specified endpoint."""
    data = {
        "Email"         : f"Test{random.randint(0,250)}@gmail.com",
        "CustomerID"    : f"cus_{random.randint(0,250)}{random.randint(0,250)}{random.randint(0,250)}",
        "UnitsPurchased": random.randint(1,250),
        "status"        : "active"
    }
    response = caspioAPI.post(endpoint=endpoint, data=data)

    assert response.status_code == 201

def test_put_request(caspioAPI):
    """Tests the put request from the Caspio_API to the specified endpoint."""
    response = caspioAPI.get(endpoint=endpoint)
    caspioData = json.loads(response.text)
    PK_ID = 0
    for line in caspioData["Result"]:
        PK_ID = line["PK_ID"]
        break

    newData = {"UnitsPurchased": random.randint(1,250)}
    response = caspioAPI.put(endpoint=endpoint, data=newData, qWhere=f'PK_ID={PK_ID}')

    assert response.status_code == 200

def test_updateUser(caspioAPI):
    """Tests the updateUser function in Caspio_API Class"""
    
    response = caspioAPI.get(endpoint=endpoint)
    caspioData = json.loads(response.text)
    CustomerID = ""
    for line in caspioData["Result"]:
        CustomerID = line["CustomerID"]
        break

    newData = {"UnitsPurchased": random.randint(1,250)}
    response = caspioAPI.updateUser(endpoint=endpoint, data=newData, customerID=CustomerID)

    assert response.status_code == 200
    
def test_mergeUser_New(caspioAPI):
    """Tests the mergeUser function creates a new user when no user exists with the CustomerID"""
    
    data = {
        "Email"         : f"Test{random.randint(0,500)}{random.randint(0,500)}@gmail.com",
        "CustomerID"    : f"cus_{random.randint(0,250)}{random.randint(0,250)}{random.randint(0,250)}",
        "UnitsPurchased": random.randint(1,250),
        "status"        : "active"
    }
    response = caspioAPI.mergeUser(data=data, endpoint=endpoint)

    assert response.status_code == 201

def test_mergeUser_Merge(caspioAPI):
    """Tests the mergeUser Function merges the data with the existing user with the same CustomerID"""
    
    CustomerID = ""
    response = caspioAPI.get(endpoint=endpoint)
    caspioData = json.loads(response.text)
    
    for line in caspioData["Result"]:
        CustomerID = line["CustomerID"]
        break
    data = {
        "Email"         : f"Test{random.randint(0,500)}{random.randint(0,500)}@gmail.com",
        "CustomerID"    : CustomerID,
        "UnitsPurchased": random.randint(1,250),
        "status"        : "active"
    }
    response = caspioAPI.mergeUser(data=data, endpoint=endpoint)
    assert response.status_code == 200

def test_delete_request(caspioAPI):
    """Tests the delete request from the Caspio_API to the specified endpoint."""
    
    response = caspioAPI.get(endpoint=endpoint)
    caspioData = json.loads(response.text)
    PK_ID = 0
    for line in caspioData["Result"]:
        PK_ID = line["PK_ID"]
        break
    response = caspioAPI.delete(endpoint=endpoint, qWhere=f'PK_ID={PK_ID}')
    assert response.status_code == 200

def test_NoUserToUpdate_exception(caspioAPI):
    """Tests that the NoUserToUpdate exception is thrown in the updateUser Function of the Caspio_API Class in the event of no user to update"""
    
    data = {"UnitsPurchased": 20}

    with pytest.raises(NoUsersToUpdate):
        caspioAPI.updateUser(data=data, endpoint=endpoint, customerID="NoCustomerID")

def test_write_to_env_file(caspioAPI):
    tokens = {
        "TOKEN1": "new_value1",
        "TOKEN2": "new_value2",
    }
    env_content = "TOKEN1=old_value1\nTOKEN2=old_value2\nTOKEN3=old_value3\n"
    updated_env_content = "TOKEN1=new_value1\nTOKEN2=new_value2\nTOKEN3=old_value3\n"

    mock_file = MockEnvFile(env_content)

    with patch("builtins.open", return_value=mock_file, create=True):
        caspioAPI._updateTokens(tokens)
        assert mock_file.read_data == updated_env_content


def test_update_nonexistent_tokens(caspioAPI):
    tokens = {
        "NONEXISTENT_TOKEN1": "new_value1",
        "NONEXISTENT_TOKEN2": "new_value2",
    }
    env_content = "TOKEN1=old_value1\nTOKEN2=old_value2\nTOKEN3=old_value3\n"

    with patch("builtins.open", mock_open(read_data=env_content), create=True) as mock_file:
        caspioAPI._updateTokens(tokens)
        mock_file().write.assert_not_called()


def test_update_tokens_no_change(caspioAPI):
    tokens = {}
    env_content = "TOKEN1=old_value1\nTOKEN2=old_value2\nTOKEN3=old_value3\n"

    with patch("builtins.open", mock_open(read_data=env_content), create=True) as mock_file:
        caspioAPI._updateTokens(tokens)
        mock_file.assert_called_with(".env", "w")
        mock_file().write.assert_not_called()

def test_update_tokens_empty_file(caspioAPI):
    tokens = {
        "TOKEN1": "new_value1",
        "TOKEN2": "new_value2",
    }

    with patch("builtins.open", mock_open(read_data=""), create=True) as mock_file:
        caspioAPI._updateTokens(tokens)
        mock_file.assert_called_with(".env", "w")
        mock_file().write.assert_not_called()

