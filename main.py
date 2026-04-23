import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

TENANT_ID     = os.getenv("TENANT_ID")
CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token():
    # Authenticate with Microsoft identity platform and return a Bearer token

    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }

    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_mail_by_upn(upn: str, token: str):
    # Query Microsoft Graph API and return the user object for the given UPN
    url = f"https://graph.microsoft.com/v1.0/users/{upn}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()

@app.route("/get-mail", methods=["GET"])
def get_mail():
    # Accept a UPN as a query param, fetch the user from Graph, and return their email
    upn = request.args.get("upn")

    if not upn:
        return jsonify({"error": "upn query parameter is required"}), 400

    try:
        token = get_access_token()
        user  = get_mail_by_upn(upn, token)

        if user is None:
            return jsonify({"error": f"No user found with UPN: {upn}"}), 404

        return jsonify({
            "userPrincipalName": user.get("userPrincipalName"),
            "email":             user.get("mail"),
            "id":                user.get("id"),
        }), 200

    except requests.HTTPError as e:
        return jsonify({"error": str(e)}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)