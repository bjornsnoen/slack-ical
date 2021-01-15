import hashlib
import hmac
import os
from os import getenv
from time import time

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()
app = Flask(__name__)


def is_request_valid(request):
    """ Validates requests from slack, used if we want a bot """
    request_body = request.get_data().decode("utf8")
    timestamp = int(request.headers["X-Slack-Request-Timestamp"])
    if abs(time() - timestamp) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    sig_basestring = "v0:" + str(timestamp) + ":" + request_body
    slack_signing_secret = getenv("SIGNING_SECRET")
    my_signature = (
        "v0="
        + hmac.new(
            bytes(slack_signing_secret, "utf8"),
            bytes(sig_basestring, "utf8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(my_signature, request.headers["X-Slack-Signature"])


@app.route("/redirect", methods=["GET"])
def redirect():
    """ Redirect from oauth, exchanges temporoary token for real token and outputs it to the browser with instructions """
    error = request.args.get("error")
    if error:
        return "Awww :("

    code = request.args.get("code")

    real_token: dict = exchange_for_real_token(code)
    if "error" in real_token:
        return real_token

    if real_token["authed_user"]["scope"] != "users.profile:write":
        return render_template("abuse.html")

    return render_template(
        "success.html", token=real_token["authed_user"]["access_token"]
    )


def exchange_for_real_token(temporary_token: str) -> str:
    """ Perform the token exchange """
    client_secret: str = getenv("CLIENT_SECRET")
    client_id: str = getenv("CLIENT_ID")
    url = "https://slack.com/api/oauth.v2.access"
    response = requests.post(
        url,
        {
            "client_secret": client_secret,
            "client_id": client_id,
            "code": temporary_token,
        },
    )
    return response.json()
