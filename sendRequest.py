import requests

url = "https://nouvelletechdemo.com/webhook"

headers = {
    "Content-Type": "application/json",
    "X-Secret-Token": "SuperSecretToken"
}

r = requests.post(url, headers=headers)
print("Status Code:", r.status_code)
print("Response Content:", r.text)