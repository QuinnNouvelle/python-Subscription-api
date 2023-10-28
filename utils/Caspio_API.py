import base64
import json
import requests
from flask import current_app

class Caspio_API:
  
    def __init__(self, envPath: str, clientID: str, clientSecret: str, accessTokenURL: str, refreshToken: str, bearerAccessToken: str, apiURL: str):
        self.envPath = str(envPath)
        self.clientID = str(clientID)
        self.clientSecret = str(clientSecret)
        self.accessTokenURL = str(accessTokenURL)
        self.refreshToken = str(refreshToken)
        self.bearerAccessToken = str(bearerAccessToken)
        self.apiURL = str(apiURL)

    def _updateTokens(self, tokens: dict):
        """Private Function.  Used to update the .env file.  Only updates the key:value 
        pair specified in 'tokens'.

        Args:
            self (object): Caspio_API Instance.
            tokens (dict): Key:Value Pairs of tokens that need updated.
        """

        with open(self.envPath, "r") as env_file:
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
        with open(self.envPath, "w") as env_file:
            env_file.writelines(updated_lines)

        current_app.logger.info(f'.env File Updated with rows {tokens}')

    def _getBearerAccessToken(self) -> requests.Response:
        """Private Function. Requests BearerAccessToken from Caspio.
        Only Updates .env variables when response.status_code = 200.
        Args:
            self (object): Caspio_API Instance.

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        postData = f"grant_type=client_credentials&client_id={self.clientID}&client_secret={self.clientSecret}"
        response = requests.post(self.accessTokenURL,data=postData)
        if response.status_code == 200:
            jsonData = json.loads(response.text)
            self.bearerAccessToken = jsonData["access_token"]
            self.refreshToken = jsonData["refresh_token"]
            tokens = {
                "bearerAccessToken": jsonData["access_token"],
                "refreshToken": jsonData["refresh_token"]
            }
            self._updateTokens(tokens)
            
        return response
        
    def _refreshBearerAccessToken(self):
        """Private Function.  Uses the Caspio Refresh token to refresh the Caspio Bearer Access Token. 
        https://howto.caspio.com/web-services-api/rest-api/authenticating-rest/
        Args:
            self (object): Caspio_API Instance.
        """
        dataToEncode = f"{self.clientID}:{self.clientSecret}"
        binaryData = dataToEncode.encode("utf-8")
        encodedData = base64.b64encode(binaryData)
        decodedData = encodedData.decode('utf-8')
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + decodedData
        }

        postData = f"grant_type=refresh_token&refresh_token={self.refreshToken}"
        response = requests.post(self.accessTokenURL,data=postData, headers=headers)

        if (response.status_code == 401):
            ## get new bearer access token and refresh token
            self._getBearerAccessToken()
            self._refreshBearerAccessToken()
        elif (response.status_code == 200):
            responseDict = json.loads(response.text)
            self.bearerAccessToken = responseDict['access_token']
            tokens = {
                "bearerAccessToken": responseDict['access_token']
            }
            self._updateTokens(tokens)

        
    def get(self, endpoint: str) -> requests.Response:
        """Simple GET Request to Caspio API.

        Args:
            self (object): Caspio_API Instance.
            endpoint (str): endpoint of GET request.

        Returns:
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        headers = {
            "Authorization": f"bearer {self.bearerAccessToken}",
            "Content-Type": "application/json"
        }
        response = requests.get(self.apiURL+ endpoint,headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.get(endpoint)
        else:
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
            "Authorization": f"bearer {self.bearerAccessToken}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        response = requests.put(f"{self.apiURL}{endpoint}?q.where={qWhere}",headers=headers, data=JSONData)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.put(endpoint, data)
        else:
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
            "Authorization": f"bearer {self.bearerAccessToken}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        response = requests.post(self.apiURL + endpoint,headers=headers, data=JSONData)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.post(endpoint, data)
        return response

    def delete(self, endpoint: str, qWhere: str) -> requests.Response:
        """Simple DEL request to specified endpoint.

        Args:
            self (object): Caspio_API Instance
            endpoint (str): url endpoint of DEL request.

        Returns: 
            requests.Response: The Response <Response> object, which contains a server's response to an HTTP request.
        """
        headers = {
            "Authorization": f"bearer {self.bearerAccessToken}",
            "Content-Type": "application/json"
        }
        response = requests.delete(f"{self.apiURL}{endpoint}?q.where={qWhere}",headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.delete(endpoint)
        return response
