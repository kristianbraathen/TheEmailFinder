from flask import jsonify, Blueprint
import requests
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
import json

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

# Azure resource details
SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
RESOURCE_GROUP = 'theemailfinder'
WEBAPP_NAME = 'theemailfinder'
WEBJOB_NAME = 'webjobemailsearch'

# Use the WebJob's directory for the flag file
WEBJOB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STOP_FLAG_FILE = os.path.join(WEBJOB_ROOT, "stop_webjob.flag")

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        print("Starting WebJob using Azure Management API...")
        
        # Delete old stop flag first
        if os.path.exists(STOP_FLAG_FILE):
            try:
                os.remove(STOP_FLAG_FILE)
                print(f"Successfully removed stop flag at {STOP_FLAG_FILE}")
            except Exception as e:
                print(f"Warning: Could not remove stop flag: {e}")

        # Get Azure token
        credential = DefaultAzureCredential()
        web_client = WebSiteManagementClient(credential, SUBSCRIPTION_ID)

        # Trigger WebJob
        print(f"Triggering WebJob {WEBJOB_NAME} in {WEBAPP_NAME}")
        result = web_client.web_apps.run_triggered_web_job(
            resource_group_name=RESOURCE_GROUP,
            name=WEBAPP_NAME,
            web_job_name=WEBJOB_NAME
        )

        print(f"WebJob trigger result: {result}")
        return jsonify({
            "status": "WebJob startet",
            "details": "WebJob trigger request sent successfully",
            "status_code": 200
        }), 200

    except Exception as e:
        print(f"Error triggering WebJob: {str(e)}")
        return jsonify({
            "status": "Feil ved start",
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
