import requests
import argparse
from dotenv import dotenv_values

config = dotenv_values('.env')

def main():
    parser = argparse.ArgumentParser(description='A Scripts that sends a generic post request to a specific endpoint')
    parser.add_argument('url', type=str, help='Full URL of the webhook endpoint')
    args = parser.parse_args()

    url = args.url

    headers = {
        "Content-Type": "application/json",
        "X-Secret-Token": config['testSecretToken']
    }

    r = requests.post(url, headers=headers)
    print("Status Code:", r.status_code)
    print("Response Content:", r.text)

if __name__ == '__main__':
    main()
