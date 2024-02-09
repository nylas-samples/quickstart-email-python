# Import your dependencies
from dotenv import load_dotenv
import os
from nylas import Client
from flask import Flask, request, redirect, url_for, session, jsonify
from flask_session.__init__ import Session
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest

# Load your env variables
load_dotenv()

# Create the app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize Nylas client
nylas = Client(
    api_key = os.environ.get("NYLAS_API_KEY"),
    api_uri = os.environ.get("NYLAS_API_URI")
)

# Call the authorization page
@app.route("/oauth/exchange", methods=["GET"])
def authorized():
    if session.get("grant_id") is None:
        code = request.args.get("code")
        exchangeRequest = CodeExchangeRequest({"redirect_uri": "http://localhost:5000/oauth/exchange",
                                               "code": code,
                                               "client_id": os.environ.get("NYLAS_CLIENT_ID")})
        exchange = nylas.auth.exchange_code_for_token(exchangeRequest)
        session["grant_id"] = exchange.grant_id
        return redirect(url_for("login"))

# Main page
@app.route("/nylas/auth", methods=["GET"])
def login():
    if session.get("grant_id") is None:
        config = URLForAuthenticationConfig({"client_id": os.environ.get("NYLAS_CLIENT_ID"), 
                                            "redirect_uri" : "http://localhost:5000/oauth/exchange"})
        url = nylas.auth.url_for_oauth2(config)
        print(url)
        return redirect(url)
    else:
        return f'{session["grant_id"]}'

@app.route("/nylas/recent-emails", methods=["GET"])
def recent_emails():
    query_params = {"limit": 5} 
    try:
        messages, _, _ = nylas.messages.list(session["grant_id"], query_params)
        return jsonify(messages)
    except Exception as e:
        return f'{e}'

@app.route("/nylas/send-email", methods=["GET"])
def send_email():
    try:
        body = {"subject" : "Your Subject Here", 
                     "body":"Your Email Here",
                     "reply_to":[{"name": "Name", "email": os.environ.get("EMAIL")}],
                     "to":[{"name": "Name", "email": os.environ.get("EMAIL")}]}

        message = nylas.messages.send(session["grant_id"], request_body = body).data

        return jsonify(message)
    except Exception as e:
        return f'{e}'

# Run our application
if __name__ == "__main__":
    app.run()
