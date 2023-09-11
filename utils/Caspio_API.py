from dotenv import dotenv_values
import json
import requests

class Caspio_API:
    env_file_path = ".env"
    config = dotenv_values(".env")

    accessTokenURL = config["accessTokenURL"]
    cliendID = config["ClientID"]
    client_secret = config["ClientSecret"]
    refreshToken = config["refreshToken"]
    accessToken = config["bearerAccessToken"]
    api_url = config["apiURL"]

    def _updateTokens(self, tokens: dict):
        with open(self.env_file_path, "r") as env_file:
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
        with open(self.env_file_path, "w") as env_file:
            env_file.writelines(updated_lines)

        print(f"Variables updated in {self.env_file_path}")


    def _getBearerAccessToken(self):
        postData = f"grant_type=client_credentials&client_id={self.cliendID}&client_secret={self.client_Secret}"
        response = requests.post(self.accessTokenURL,data=postData)
        if response.status_code == 200:
            jsonData = json.loads(response.text)
            tokens = {
                "bearerAccessToken": jsonData["access_token"],
                "refreshToken": jsonData["refresh_token"]
            }
            updateTokens(tokens)
            
        print(response.text)
        

    def _refreshBearerAccessToken(self):
        dataToEncode = f"{self.clientID}:{self.client_secret}"
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
            getBearerAccessToken()
            refreshBearerAccessToken(self.clientID, self.client_secret, self.refreshToken)
        if (response.status_code == 200):
            tokens = {
                "bearerAccessToken": jsonData["access_token"]
            }
            updateTokens(tokens)


        print(response.text)
        

    def get(self, endpoint: str):
        headers = {
            "Authorization": "bearer " + self.accessToken,
            "Content-Type": "application/json"
        }
        response = requests.get(self.api_url + endpoint,headers=headers)
        if response.status_code == 401:
            refreshBearerAccessToken()
            getCaspio(endpoint, self.accessToken)
        return json.loads(response.text)