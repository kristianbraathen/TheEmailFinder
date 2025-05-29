from flask import jsonify, Blueprint
import requests
import os

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch/run"

WEBJOBS_USER = os.getenv("WEBJOBS_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS")

STOP_FLAG_FILE = "/app/stop_webjob.flag"  # <-- Endre hvis nødvendig

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        # Slett gammelt stoppflagg først (start ny runde)
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)

        response = requests.post(WEBJOBS_BASE_URL, auth=(WEBJOBS_USER, WEBJOBS_PASS))
        print("➡️ Statuskode:", response.status_code)
        print("➡️ Respons:", response.text)

        if response.status_code == 202:
            return jsonify({"status": "WebJob startet"}), 202
        else:
            return jsonify({
                "status": "Feil ved start",
                "status_code": response.status_code,
                "details": response.text
            }), 500
    except Exception as e:
        return jsonify({
            "status": "Feil under start",
            "details": str(e)
        }), 500

@trigger_webjobs.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        return jsonify({"status": "Stoppflagg satt – WebJob bør avslutte snart"}), 200
    except Exception as e:
        return jsonify({"status": "Kunne ikke skrive stoppflagg", "details": str(e)}), 500
