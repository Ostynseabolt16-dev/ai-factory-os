
import os
import base64
import hashlib
import secrets
import webbrowser
from urllib.parse import urlencode

import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ETSY_API_KEY = os.getenv("ETSY_API_KEY")
ETSY_SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET")
REDIRECT_URI = os.getenv("ETSY_REDIRECT_URI")

code_verifier = secrets.token_urlsafe(64)

hashed = hashlib.sha256(code_verifier.encode()).digest()

code_challenge = (
    base64.urlsafe_b64encode(hashed)
    .decode()
    .replace("=", "")
)

SCOPES = [
    "listings_w",
    "listings_r",
    "shops_r",
    "shops_w",
    "transactions_r"
]

auth_params = {
    "response_type": "code",
    "client_id": ETSY_API_KEY,
    "redirect_uri": REDIRECT_URI,
    "scope": " ".join(SCOPES),
    "state": "factoryos",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}

auth_url = (
    "https://www.etsy.com/oauth/connect?"
    + urlencode(auth_params)
)

@app.route("/callback")
def callback():
    code = request.args.get("code")

    token_url = "https://api.etsy.com/v3/public/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": ETSY_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier,
    }

    response = requests.post(token_url, json=data)

    token_data = response.json()

    print("\nTOKEN RESPONSE:\n")
    print(token_data)

    return "Authorization successful. You can close this tab."

if __name__ == "__main__":
    print("\nOpening Etsy authorization page...\n")
    webbrowser.open(auth_url)
    app.run(port=8000)