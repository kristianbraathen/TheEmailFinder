from flask import jsonify, Blueprint
import requests
import os
import traceback

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

        print(f"Attempting to trigger WebJob at: {WEBJOBS_BASE_URL}")
        print(f"Using credentials - User: {WEBJOBS_USER}, Pass: {'*' * len(WEBJOBS_PASS) if WEBJOBS_PASS else 'None'}")
        
        response = requests.post(WEBJOBS_BASE_URL, auth=(WEBJOBS_USER, WEBJOBS_PASS))
        print("➡️ Statuskode:", response.status_code)
        print("➡️ Respons:", response.text)
        print("➡️ Headers:", response.headers)

        if response.status_code == 202:
            # Get WebJob status
            status_url = WEBJOBS_BASE_URL.replace("/run", "")
            status_response = requests.get(status_url, auth=(WEBJOBS_USER, WEBJOBS_PASS))
            status_data = status_response.json() if status_response.status_code == 200 else {}
            
            return jsonify({
                "status": "WebJob startet",
                "webjob_status": status_data.get("status", "Unknown"),
                "last_run": status_data.get("last_run", "Unknown"),
                "next_run": status_data.get("next_run", "Unknown"),
                "run_count": status_data.get("run_count", 0)
            }), 202
        else:
            return jsonify({
                "status": "Feil ved start",
                "status_code": response.status_code,
                "details": response.text,
                "headers": dict(response.headers)
            }), 500
    except Exception as e:
        print(f"Exception details: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "Feil under start",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

@trigger_webjobs.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        return jsonify({"status": "Stoppflagg satt – WebJob bør avslutte snart"}), 200
    except Exception as e:
        print(f"Stop exception: {str(e)}")
        print(f"Stop traceback: {traceback.format_exc()}")
        return jsonify({"status": "Kunne ikke skrive stoppflagg", "details": str(e)}), 500
