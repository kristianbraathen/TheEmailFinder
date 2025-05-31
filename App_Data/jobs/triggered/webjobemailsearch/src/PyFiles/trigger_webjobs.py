from flask import jsonify, Blueprint
import requests
import os
import logging

trigger_webjobs = Blueprint("trigger_webjobs", __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Kudu API details
WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch/run"
WEBJOBS_USER = os.getenv("WEBJOBS_USER")
WEBJOBS_PASS = os.getenv("WEBJOBS_PASS")

# Use the WebJob's directory for the flag file
WEBJOB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STOP_FLAG_FILE = os.path.join(WEBJOB_ROOT, "stop_webjob.flag")

@trigger_webjobs.route("/start", methods=["POST"])
def trigger_webjob_start():
    try:
        logger.info("Starting WebJob trigger process...")
        
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
        else:
            logger.error("No Kudu API credentials available")
            return jsonify({
                "status": "Feil ved start",
                "details": "Mangler Kudu API påloggingsinformasjon"
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
        # Set the stop flag
        with open(STOP_FLAG_FILE, "w") as f:
            f.write("STOP")
        
        return jsonify({
            "status": "Stoppflagg satt – WebJob bør avslutte snart"
        }), 200
    except Exception as e:
        logger.error(f"Error setting stop flag: {e}")
        return jsonify({
            "status": "Kunne ikke skrive stoppflagg", 
            "details": str(e)
        }), 500
