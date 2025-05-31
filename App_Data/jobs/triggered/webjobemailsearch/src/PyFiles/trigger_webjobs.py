from flask import jsonify, Blueprint
import requests
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
import json

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Azure resource details
SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
RESOURCE_GROUP = 'theemailfinder'
WEBAPP_NAME = 'theemailfinder'
WEBJOB_NAME = 'webjobemailsearch'

# Kudu API details (fallback)
WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch/run"
WEBJOBS_USER = os.getenv("WEBJOBS_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS")

# Use the WebJob's directory for the flag file
WEBJOB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STOP_FLAG_FILE = os.path.join(WEBJOB_ROOT, "stop_webjob.flag")

def get_webjob_status():
    try:
        credential = DefaultAzureCredential()
        web_client = WebSiteManagementClient(credential, SUBSCRIPTION_ID)
        
        # Get WebJob status
        webjob = web_client.web_apps.list_triggered_web_job_histories(
            resource_group_name=RESOURCE_GROUP,
            name=WEBAPP_NAME,
            web_job_name=WEBJOB_NAME
        )
        
        # Convert to list to get the most recent run
        runs = list(webjob)
        if runs:
            latest_run = runs[-1]
            return {
                "status": latest_run.status,
                "start_time": latest_run.start_time,
                "end_time": latest_run.end_time,
                "duration": latest_run.duration
            }
        return {"status": "No runs found"}
    except Exception as e:
        print(f"Error getting WebJob status: {str(e)}")
        return {"status": "Error", "details": str(e)}

@trigger_webjobs.route("/status", methods=["GET"])
def get_status():
    status = get_webjob_status()
    return jsonify(status)

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        logger.info("Starting WebJob trigger process...")
        
        # Try Kudu API first since we know we have these credentials
        if WEBJOBS_USER and WEBJOBS_PASS:
            logger.info("Attempting to use Kudu API...")
            # Delete old stop flag first
            if os.path.exists(STOP_FLAG_FILE):
                try:
                    os.remove(STOP_FLAG_FILE)
                    logger.info("Successfully removed stop flag")
                except Exception as e:
                    logger.warning(f"Could not remove stop flag: {e}")

            response = requests.post(WEBJOBS_BASE_URL, auth=(WEBJOBS_USER, WEBJOBS_PASS))
            logger.info(f"Kudu API response status: {response.status_code}")
            
            if response.status_code == 202:
                return jsonify({"status": "WebJob startet", "method": "kudu_api"}), 202
            else:
                logger.error(f"Kudu API error: {response.status_code} - {response.text}")
                return jsonify({
                    "status": "Feil ved start",
                    "method": "kudu_api",
                    "status_code": response.status_code,
                    "details": response.text
                }), 500
                
        # Fallback to Azure Management API only if Kudu fails and we have subscription ID
        elif SUBSCRIPTION_ID:
            logger.info("Kudu credentials not found, attempting Azure Management API...")
            try:
                credential = DefaultAzureCredential()
                web_client = WebSiteManagementClient(credential, SUBSCRIPTION_ID)
                
                result = web_client.web_apps.run_triggered_web_job(
                    resource_group_name=RESOURCE_GROUP,
                    name=WEBAPP_NAME,
                    web_job_name=WEBJOB_NAME
                )
                logger.info("Successfully triggered WebJob using Azure Management API")
                return jsonify({"status": "WebJob startet", "method": "azure_api"}), 200
            except Exception as azure_error:
                logger.error(f"Azure Management API failed: {str(azure_error)}")
                return jsonify({
                    "status": "Feil ved start",
                    "method": "azure_api",
                    "details": str(azure_error)
                }), 500
        else:
            logger.error("No valid authentication method available")
            return jsonify({
                "status": "Feil ved start",
                "details": "Ingen gyldig autentiseringsmetode tilgjengelig"
            }), 500
            
    except Exception as e:
        logger.error(f"Critical error in trigger_webjob_start: {str(e)}")
        return jsonify({
            "status": "Feil ved start",
            "details": str(e)
        }), 500

@trigger_webjobs.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        # First check if it's actually running
        status = get_webjob_status()
        if status.get("status") != "Running":
            return jsonify({
                "status": "Not Running",
                "details": status,
                "status_code": 400
            }), 400

        # Set the stop flag
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        
        return jsonify({
            "status": "Stoppflagg satt – WebJob bør avslutte snart",
            "current_status": status
        }), 200
    except Exception as e:
        print(f"Error setting stop flag: {e}")
        return jsonify({
            "status": "Kunne ikke skrive stoppflagg", 
            "details": str(e)
        }), 500
