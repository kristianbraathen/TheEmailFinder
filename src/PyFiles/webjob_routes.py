import os
from flask import Blueprint, jsonify, request
import requests
from requests.auth import HTTPBasicAuth

webjob_blueprint = Blueprint("webjob", __name__)

WEBJOB_URL = "https://theemailfinder.scm.azurewebsites.net/api/triggeredwebjobs/emailsearch/run"
WEBJOB_USERNAME = os.environ.get("WEBJOB_USERNAME")
WEBJOB_PASSWORD = os.environ.get("WEBJOB_PASSWORD")

@webjob_blueprint.route("/trigger-webjob", methods=["POST"])
def trigger_webjob():
    if not WEBJOB_USERNAME or not WEBJOB_PASSWORD:
        return jsonify({"error": "Miljøvariabler mangler"}), 500

    try:
        response = requests.post(
            WEBJOB_URL,
            auth=HTTPBasicAuth(WEBJOB_USERNAME, WEBJOB_PASSWORD)
        )

        if response.ok:
            return jsonify({"status": "WebJob trigget"}), 200
        else:
            return jsonify({"error": "Feil ved trigging", "details": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": f"Noe gikk galt: {str(e)}"}), 500
