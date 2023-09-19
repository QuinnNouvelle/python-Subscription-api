import base64
import json
import requests

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

    def _getBearerAccessToken(self: object):
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
        if (response.status_code == 200):
            responseDict = json.loads(response.text)
            print(response.text)
            tokens = {
                "bearerAccessToken": responseDict['access_token']
            }
            self._updateTokens(tokens)


        print(response.text)
        
    def get(self: object, endpoint: str) -> object:
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        response = requests.get(self.config["apiURL"] + endpoint,headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.get(endpoint)
        #print(f"{response.status_code}: {response.text}")
        return response

    def put(self: object, endpoint: str, data, qWhere: str) -> object:
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

    def delete(self: object, endpoint: str) -> object:
        headers = {
            "Authorization": f"bearer {self.config['bearerAccessToken']}",
            "Content-Type": "application/json"
        }
        response = requests.delete(self.config["apiURL"] + endpoint,headers=headers)
        if response.status_code == 401:
            self._refreshBearerAccessToken()
            self.delete(endpoint)
        print(f"{response.status_code}: {response.text}")
        return response

    def mergeUser(self: object, data: dict, endpoint: str):
        # Get All Records From A Table
        response = self.get(endpoint)
        recordsDict = json.loads(response.text)

        # Iterate Through Those Records
        for record in recordsDict['Result']:
            if data['Email'] == record['Email']:
                del data["Email"]
                response = self.put(endpoint, data, f"PaymentID={record['PaymentID']}")
                return response
        response = self.post(endpoint, data)
        print(f'Successfully Created A new User with Data: {data}')
        return response