from flask import jsonify, Blueprint, request
import requests
import os
import traceback
import logging

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Kudu API details
WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch/run"

# Get credentials from environment variables
WEBJOBS_USER = os.getenv("WEBJOBS_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS")

# Use the current working directory for the flag file
STOP_FLAG_FILE = os.path.join(os.getcwd(), "stop_webjob.flag")

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        logger.info("Starting WebJob trigger process...")
        
        # Check if credentials are available
        if not WEBJOBS_USER or not WEBJOBS_PASS:
            logger.error("Missing WebJobs credentials")
            return jsonify({
                "status": "Feil ved start",
                "details": "Mangler WebJobs påloggingsinformasjon"
            }), 500

        # Remove old stop flag if it exists
        if os.path.exists(STOP_FLAG_FILE):
            try:
                os.remove(STOP_FLAG_FILE)
                logger.info("Successfully removed stop flag")
            except Exception as e:
                logger.warning(f"Could not remove stop flag: {e}")

        logger.info(f"Attempting to trigger WebJob at: {WEBJOBS_BASE_URL}")
        
        # Get provider from request
        provider = request.json.get('provider', 'googlekse')
        logger.info(f"Using provider: {provider}")
        
        # Trigger the WebJob with proper headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Format the request body according to Azure WebJobs API
        body = {
            "properties": {
                "arguments": f"--provider {provider}"
            }
        }
        
        logger.info(f"Sending request with body: {body}")
        
        response = requests.post(
            WEBJOBS_BASE_URL,
            auth=(WEBJOBS_USER, WEBJOBS_PASS),
            headers=headers,
            json=body
        )
        
        logger.info(f"WebJob trigger response - Status: {response.status_code}, Text: {response.text}")

        # Both 200 and 202 are valid success responses for WebJob triggers
        if response.status_code in [200, 202]:
            # Get WebJob status
            status_url = WEBJOBS_BASE_URL.replace("/run", "")
            status_response = requests.get(
                status_url, 
                auth=(WEBJOBS_USER, WEBJOBS_PASS),
                headers={'Accept': 'application/json'}
            )
            status_data = status_response.json() if status_response.status_code == 200 else {}
            
            return jsonify({
                "status": "WebJob startet",
                "webjob_status": status_data.get("status", "Unknown"),
                "last_run": status_data.get("last_run", "Unknown"),
                "next_run": status_data.get("next_run", "Unknown"),
                "run_count": status_data.get("run_count", 0),
                "response_code": response.status_code
            }), 200
        else:
            logger.error(f"Failed to trigger WebJob: {response.status_code} - {response.text}")
            return jsonify({
                "status": "Feil ved start",
                "status_code": response.status_code,
                "details": response.text
            }), 500

    except Exception as e:
        logger.error(f"Exception in trigger_webjob_start: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "Feil under start",
            "details": str(e)
        }), 500

@trigger_webjobs.route("/stop", methods=["POST"])
def trigger_webjob_stop():
    try:
        # Set the stop flag in the current directory
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        
        logger.info(f"Stop flag set successfully at {STOP_FLAG_FILE}")
        return jsonify({"status": "Stoppflagg satt – WebJob bør avslutte snart"}), 200
    except Exception as e:
        logger.error(f"Error setting stop flag: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "Kunne ikke skrive stoppflagg",
            "details": str(e)
        }), 500
