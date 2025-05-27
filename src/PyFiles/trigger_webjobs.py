from flask import Blueprint, jsonify
import requests
import os

trigger_webjobs_bp = Blueprint("trigger_webjobs", __name__)

WEBJOB_NAME = "webjobemailsearch"  # <- Bytt med riktig navn
WEBJOBS_BASE_URL = f"https://theemailfinder.scm.azurewebsites.net/api/triggeredwebjobs/{WEBJOB_NAME}/run"

WEBJOBS_USER = os.getenv("WEBJOBS_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS")

STOP_FLAG_FILE = "/app/stop_webjob.flag"  # <-- Endre hvis nødvendig

@trigger_webjobs_bp.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        # Slett gammelt stoppflagg først (start ny runde)
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)

        response = requests.post(WEBJOBS_BASE_URL, auth=(WEBJOBS_USER, WEBJOBS_PASS))
        if response.status_code == 202:
            return jsonify({"status": "WebJob startet"}), 202
        else:
            return jsonify({"status": "Feil ved start", "details": response.text}), 500
    except Exception as e:
        return jsonify({"status": "Feil under start", "details": str(e)}), 500

@trigger_webjobs_bp.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        return jsonify({"status": "Stoppflagg satt – WebJob bør avslutte snart"}), 200
    except Exception as e:
        return jsonify({"status": "Kunne ikke skrive stoppflagg", "details": str(e)}), 500
