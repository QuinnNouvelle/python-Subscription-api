import base64
import json
import requests
from flask import current_app
from dotenv import dotenv_values

class NoUsersToUpdate(Exception):
    "Raised when No Users are found with the Customer ID so there is no Update to be done."

class Caspio_API:
    
    _config = dict(dotenv_values('.env'))
    _clientID = _config["ClientID"]
    _clientSecret = _config['ClientSecret']
    _accessTokenURL = _config['accessTokenURL']
    _refreshToken = _config['refreshToken']
    _bearerAccessToken = _config['bearerAccessToken']
    _apiURL = _config['apiURL']

    def _updateTokens(self, tokens: dict):
        """Private Function.  Used to update the .env file.  Only updates the key:value 
        pair specified in 'tokens'.

        Args:
            self (object): Caspio_API Instance.
            tokens (dict): Key:Value Pairs of tokens that need updated.
        """
        envPath = ".env"

        with open(envPath, "r") as env_file:
            lines = env_file.readlines()
        
        updated_lines = []
        for line in lines:
            for key, new_value in tokens.items():
                if line.startswith(f"{key}="):
                    # Replace the existing value with the new value
                    updated_lines.append(f"{key}={new_value}\n")
                    break  # Stop looking for this key in subsequent lines
            else:
                updated_lines.append(line)

        # Write the modified content back to the file
        with open(envPath, "w") as env_file:
            env_file.writelines(updated_lines)

        #current_app.logger.info(f'.env File Updated with rows {tokens}')

    def _get_BearerAccessToken(self) -> requests.Response:
        """Private Function. Requests _BearerAccessToken from Caspio. Gets A new BAT and Refresh token from Caspio
        Only Updates .env variables when response.status_code = 200.
        Args:
            self (object): Caspio_API Instance.

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """


        postData = f"grant_type=client_credentials&client_id={self._clientID}&client_secret={self._clientSecret}"
        try:
            response = requests.post(self._accessTokenURL,data=postData, timeout=10)
        except Exception as e:
            current_app.logger.error(e)

        if response.status_code == 200:
            jsonData = json.loads(response.text)
            self._bearerAccessToken = jsonData["access_token"]
            self._refreshToken = jsonData["refresh_token"]
            tokens = {
                "bearerAccessToken": jsonData["access_token"],
                "refreshToken": jsonData["refresh_token"]
            }
            self._updateTokens(tokens)
            
        return response
        
    def _refresh_BearerAccessToken(self):
        """Private Function.  Uses the Caspio Refresh token to refresh the Caspio Bearer Access Token. 
        https://howto.caspio.com/web-services-api/rest-api/authenticating-rest/
        Args:
            self (object): Caspio_API Instance.
        """
        dataToEncode = f"{self._clientID}:{self._clientSecret}"
        binaryData = dataToEncode.encode("utf-8")
        encodedData = base64.b64encode(binaryData)
        decodedData = encodedData.decode('utf-8')
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + decodedData
        }

        postData = f"grant_type=refresh_token&refresh_token={self._refreshToken}"
        try:
            response = requests.post(self._accessTokenURL,data=postData, headers=headers, timeout=10)
        except Exception as e:
            response = requests.Response()
            current_app.logger.error(e)

        if (response.status_code == 400):
            self._get_BearerAccessToken()
        elif (response.status_code == 200):
            responseDict = json.loads(response.text)
            self._bearerAccessToken = responseDict['access_token']
            tokens = {
                "bearerAccessToken": responseDict['access_token']
            }
            self._updateTokens(tokens)

        
    def get(self, endpoint: str, qWhere: str = None) -> requests.Response:
        """Simple GET Request to Caspio API.

        Args:
            self (object): Caspio_API Instance.
            endpoint (str): endpoint of GET request.

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        headers = {
            "Authorization": f"bearer {self._bearerAccessToken}",
            "Content-Type": "application/json"
        }
        try:
            if qWhere:
                response = requests.get(f"{self._apiURL}{endpoint}?q.where={qWhere}",headers=headers, timeout=10)
            else:
                response = requests.get(self._apiURL+ endpoint,headers=headers, timeout=10)
        except Exception as e:
            response = requests.Response()
            current_app.logger.error(e)

        if response.status_code == 401:
            self._refresh_BearerAccessToken()
            response = self.get(endpoint)
            
        return response

    def put(self, endpoint: str, data: dict, qWhere: str) -> requests.Response:
        """Simple PUT request.  Requires data in a dict of values changed, 
        and an identifier for the row being changed.

        Args:
            self (object): Caspio_API Instance.
            endpoint (str): url endpoint of put request.
            data (dict): Key:Value pairs of the information being updated.
            qWhere (str): Identifier for the line being changed ex: qWhere = f"PaymentID={record['PaymentID']}".

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        headers = {
            "Authorization": f"bearer {self._bearerAccessToken}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        try:
            response = requests.put(f"{self._apiURL}{endpoint}?q.where={qWhere}",headers=headers, data=JSONData, timeout=10)
        except Exception as e:
            response = requests.Response()
            current_app.logger.error(e)


        if response.status_code == 401:
            self._refresh_BearerAccessToken()
            response = self.put(endpoint, data, qWhere)
        
        return response

    def post(self, endpoint: str, data: dict) -> requests.Response:
        """Simple POST request to specified endpoint.

        Args:
            self (object): Caspio_API Instance
            endpoint (str): url endpoint of POST request.
            data (dict): Dictionary of data passed into the POST request.

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        headers = {
            "Authorization": f"bearer {self._bearerAccessToken}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        try:
            response = requests.post(self._apiURL + endpoint,headers=headers, data=JSONData, timeout=10)
        except Exception as e:
            response = requests.Response()
            current_app.logger.error(e)

        if response.status_code == 401:
            self._refresh_BearerAccessToken()
            response = self.post(endpoint, data)
        return response
        

    def delete(self, endpoint: str, qWhere: str) -> requests.Response:
        """Simple DEL request to specified endpoint.

        Args:
            self (object): Caspio_API Instance
            endpoint (str): url endpoint of DEL request.

        Returns: 
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.  Or an empty Response() object if the requests times out
        """
        headers = {
            "Authorization": f"bearer {self._bearerAccessToken}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.delete(f"{self._apiURL}{endpoint}?q.where={qWhere}",headers=headers, timeout=10)
        except Exception as e:
            response = requests.Response()
            current_app.logger.error(e)
            

        if response.status_code == 401:
            self._refresh_BearerAccessToken()
            response = self.delete(endpoint, qWhere)
        return response

    def mergeUser(self, data: dict, endpoint: str) -> requests.Response:
        """Attempts to find user for the new data being submitted via CustomerID.
        If CustomerID is found the row is updated with information in the dict.
        If no CustomerID exists in Caspio Table then create a new record in that table with data.

        Args:
            data (dict): Key:Value information for user.
            endpoint (str): endpoint url of the table you want to affect

        Returns:
            requests.Response

        """
        response = self.get(endpoint)
        
        # Check that I got the response correctly
        if response.status_code in {200, 201}:
            recordsDict = json.loads(response.text)
            # Checks if the CustomerID Exists in the Table
            for record in recordsDict['Result']:
                if data['CustomerID'] == record['CustomerID']:
                    response = self.put(endpoint, data, f"PK_ID={record['PK_ID']}")
                    return response
            # If CustomerID does not exists on Caspio, post a new user.
            response = self.post(endpoint, data)
        return response

    def updateUser(self, customerID: str, data: dict, endpoint: str) -> requests.Response:
        """Attempts to find user for the new data being submitted via CustomerID.
        If customerID is found the row is updated with information in the dict.
        If no customerID exists in Caspio Table throw an Error

        Args:
            data (dict): Key:Value information for user.
            endpoint (str): endpoint url of the table you want to affect
            caspioAPI (Caspio_API): Instance of the Caspio_API class

        Returns:
            requests.Response
        """
        response = self.get(endpoint)

        if response.status_code in {200, 201}:
            recordsDict = json.loads(response.text)
            for record in recordsDict['Result']:
                if customerID == record['CustomerID']:
                    response = self.put(endpoint, data, f"PK_ID={record['PK_ID']}")
                    return response
            raise NoUsersToUpdate
        return response
