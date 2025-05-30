from flask import jsonify, Blueprint
import requests
import os
import json

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch/run"

# Get credentials from environment variables
WEBJOBS_USER = os.getenv("WEBJOBS_USER") or os.getenv("DEPLOY_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS") or os.getenv("DEPLOY_PASS")

# Use the WebJob's directory for the flag file
WEBJOB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STOP_FLAG_FILE = os.path.join(WEBJOB_ROOT, "stop_webjob.flag")

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        # Log credentials status (without exposing them)
        print(f"Checking credentials - User exists: {bool(WEBJOBS_USER)}, Pass exists: {bool(WEBJOBS_PASS)}")
        
        if not WEBJOBS_USER or not WEBJOBS_PASS:
            return jsonify({
                "status": "Feil ved start",
                "details": "Missing WebJob credentials",
                "status_code": 500
            }), 500

        # Delete old stop flag first
        if os.path.exists(STOP_FLAG_FILE):
            try:
                os.remove(STOP_FLAG_FILE)
                print(f"Successfully removed stop flag at {STOP_FLAG_FILE}")
            except Exception as e:
                print(f"Warning: Could not remove stop flag: {e}")

        print(f"Attempting to start WebJob at: {WEBJOBS_BASE_URL}")
        response = requests.post(
            WEBJOBS_BASE_URL, 
            auth=(WEBJOBS_USER, WEBJOBS_PASS),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")

        try:
            response_json = response.json() if response.text else {}
            print(f"Response JSON: {response_json}")
        except json.JSONDecodeError:
            print("Response was not JSON format")
            response_json = {}

        if response.status_code in [200, 202]:
            return jsonify({
                "status": "WebJob startet",
                "details": response_json,
                "status_code": response.status_code
            }), 200
        else:
            return jsonify({
                "status": "Feil ved start",
                "details": response.text,
                "status_code": response.status_code
            }), 500
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return jsonify({
            "status": "Nettverksfeil",
            "details": str(e),
            "status_code": 500
        }), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "status": "Uventet feil",
            "details": str(e),
            "status_code": 500
        }), 500

@trigger_webjobs.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        return jsonify({"status": "Stoppflagg satt – WebJob bør avslutte snart"}), 200
    except Exception as e:
        print(f"Error setting stop flag: {e}")
        return jsonify({"status": "Kunne ikke skrive stoppflagg", "details": str(e)}), 500
