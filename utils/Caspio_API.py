import base64
import json
import requests
from flask import current_app

class Caspio_API:
  
    def __init__(self: object, config):
        self._config = config

    @property
    def config(self: object):
        return self._config

    @config.setter
    def config(self: object, config):
        self._config = config

    def _updateTokens(self: object, tokens: dict):
        """Private Function.  Used to update the .env file.  Only updates the key:value 
        pair specified in 'tokens'.

        Args:
            self (object): Caspio_API Instance.
            tokens (dict): Key:Value Pairs of tokens that need updated.
        """

        with open(self.config['envPath'], "r") as env_file:
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
        with open(self.config['envPath'], "w") as env_file:
            env_file.writelines(updated_lines)

        self.config = updated_lines
        print(f"Variables updated in .env")

    def _getBearerAccessToken(self: object) -> object:
        """Private Function. Requests BearerAccessToken from Caspio.
        Only Updates .env variables when response.status_code = 200.
        Args:
            self (object): Caspio_API Instance.

        Returns:
            object: Response Object of post request.
        """

        postData = f"grant_type=client_credentials&client_id={self.config['ClientID']}&client_secret={self.config['ClientSecret']}"
        response = requests.post(self.config["accessTokenURL"],data=postData)
        if response.status_code == 200:
            jsonData = json.loads(response.text)
            tokens = {
                "bearerAccessToken": jsonData["access_token"],
                "refreshToken": jsonData["refresh_token"]
            }
            self._updateTokens(tokens)
            
        return response
        
    def _refreshBearerAccessToken(self: object):
        """Private Function.  Uses the Caspio Refresh token to refresh the Caspio Bearer Access Token. 
        https://howto.caspio.com/web-services-api/rest-api/authenticating-rest/
        Args:
            self (object): Caspio_API Instance.
        """
        dataToEncode = f"{self.config['ClientID']}:{self.config['ClientSecret']}"
        binaryData = dataToEncode.encode("utf-8")
        encodedData = base64.b64encode(binaryData)
        decodedData = encodedData.decode('utf-8')
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + decodedData
        }

        postData = f"grant_type=refresh_token&refresh_token={self.config['refreshToken']}"
        
        response = requests.post(self.config["accessTokenURL"],data=postData, headers=headers)

        if (response.status_code == 401):
            ## get new bearer access token and refresh token
            self._getBearerAccessToken()
            self._refreshBearerAccessToken()
            return
        if (response.status_code == 200):
            responseDict = json.loads(response.text)
            print(response.text)
            tokens = {
                "bearerAccessToken": responseDict['access_token']
            }
            self._updateTokens(tokens)


        print(response.text)
        
    def get(self: object, endpoint: str) -> object:
        """Simple GET Request to Caspio API.

        Args:
            self (object): Caspio_API Instance.
            endpoint (str): endpoint of GET request.

        Returns:
            object: GET response object.
        """
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        response = requests.get(self.config["apiURL"] + endpoint,headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.get(endpoint)
        #print(f"{response.status_code}: {response.text}")
        print(type(response))
        return response

    def put(self: object, endpoint: str, data: dict, qWhere: str) -> object:
        """Simple PUT request.  Requires data in a dict of values changed, 
        and an identifier for the row being changed.

        Args:
            self (object): Caspio_API Instance.
            endpoint (str): url endpoint of put request.
            data (dict): Key:Value pairs of the information being updated.
            qWhere (str): Identifier for the line being changed ex: qWhere = f"PaymentID={record['PaymentID']}".

        Returns:
            object: PUT request response object.
        """
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        print(f"{JSONData}\n")
        print(f"{self.config['apiURL']}{endpoint}?q.where={qWhere}")

        response = requests.put(f"{self.config['apiURL']}{endpoint}?q.where={qWhere}",headers=headers, data=JSONData)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.put(endpoint, data)
        print(f"{response.status_code}: {response.text}")
        if response.status_code == 200:
            print(f"Successfully Updated row: {qWhere}, With Data: {data}")
        return response

    def post(self: object, endpoint: str, data: dict) -> object:
        """Simple POST request to specified endpoint.

        Args:
            self (object): Caspio_API Instance
            endpoint (str): url endpoint of POST request.
            data (dict): Dictionary of data passed into the POST request.

        Returns:
            object: POST request response object.
        """
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        JSONData = json.dumps(data)
        response = requests.post(self.config["apiURL"] + endpoint,headers=headers, data=JSONData)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.post(endpoint, data)
        print(f"{response.status_code}: {response.text}")
        return response

    def delete(self: object, endpoint: str, qWhere: str) -> object:
        """Simple DEL request to specified endpoint.

        Args:
            self (object): Caspio_API Instance
            endpoint (str): url endpoint of DEL request.

        Returns:
            object: DEL request response object.
        """
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        response = requests.delete(f"{self.config['apiURL']}{endpoint}?q.where={qWhere}",headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.delete(endpoint)
        print(f"{response.status_code}: {response.text}")
        return response

    def mergeUser(self: object, data: dict, endpoint: str) -> object:
        """Attempts to find user for the new data being submitted via email.
        If email is found the row is updated with information in the dict.
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
        response = self.get(endpoint)
        recordsDict = json.loads(response.text)

        # Iterate Through Those Records and update data
        for record in recordsDict['Result']:
            if data['CustomerID'] == record['CustomerID']:
                #del data["CustomerID"]
                response = self.put(endpoint, data, f"PK_ID={record['PK_ID']}")
                if response.status_code == 201 or response.status_code == 200:
                    print(f'Successfully Updated user {record["Email"]} with Data: {data}')
                else: 
                    print(response.status_code)
                    print(f'ERROR: User {record["Email"]} with Data: {data} Is not updated in the database\nResponse: {response.text}')
                return response
        # If email does not exists on Caspio, post a new user.
        response = self.post(endpoint, data)
        if response.status_code == 201:
            print(response.status_code)
            print(f'Successfully Created A new User with Data: {data}')
        else:
            print(f"{response.status_code} {response.text}")
        return response