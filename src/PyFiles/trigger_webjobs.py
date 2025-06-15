from flask import Blueprint, request, jsonify
import requests
import os

trigger_webjobs = Blueprint('trigger_webjobs', __name__)

# Base URL for webjobs
WEBJOBS_BASE_URL = "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs"

# Get credentials from environment variables
WEBJOBS_USER = os.getenv('WEBJOBS_USER')
WEBJOBS_PASS = os.getenv('WEBJOBS_PASS')

# Google KSE endpoints
@trigger_webjobs.route('/googlekse/status', methods=['GET'])
def status_googlekse():
    try:
        response = requests.get(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-googlekse/history",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            history = response.json()
            # Check if there's a recent run that's still running
            if history and len(history) > 0:
                latest_run = history[0]
                return jsonify({
                    'running': latest_run.get('status') == 'Running',
                    'message': latest_run.get('status')
                }), 200
            return jsonify({'running': False, 'message': 'No recent runs'}), 200
        else:
            return jsonify({'error': f'Failed to get webjob status: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/googlekse/start', methods=['POST'])
def start_googlekse():
    try:
        response = requests.post(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-googlekse/run",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Started Google KSE webjob successfully'}), 200
        else:
            return jsonify({'error': f'Failed to start webjob: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/googlekse/stop', methods=['POST'])
def stop_googlekse():
    try:
        # First check if the webjob is running
        status_response = requests.get(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-googlekse/history",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if status_response.status_code == 200:
            history = status_response.json()
            if history and len(history) > 0:
                latest_run = history[0]
                if latest_run.get('status') == 'Running':
                    # Use the run endpoint with a stop parameter
                    response = requests.post(
                        f"{WEBJOBS_BASE_URL}/webjobemailsearch-googlekse/run",
                        auth=(WEBJOBS_USER, WEBJOBS_PASS),
                        json={'stop': True}
                    )
                    
                    if response.status_code in [200, 202]:
                        return jsonify({'message': 'Stopped Google KSE webjob successfully'}), 200
                    else:
                        return jsonify({'error': f'Failed to stop webjob: {response.text}'}), response.status_code
                else:
                    return jsonify({'message': 'Webjob is not running'}), 200
            else:
                return jsonify({'message': 'No webjob runs found'}), 200
        else:
            return jsonify({'error': f'Failed to get webjob status: {status_response.text}'}), status_response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# KSE API endpoints
@trigger_webjobs.route('/kseapi/status', methods=['GET'])
def status_kseapi():
    try:
        response = requests.get(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kseapi/history",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            history = response.json()
            # Check if there's a recent run that's still running
            if history and len(history) > 0:
                latest_run = history[0]
                return jsonify({
                    'running': latest_run.get('status') == 'Running',
                    'message': latest_run.get('status')
                }), 200
            return jsonify({'running': False, 'message': 'No recent runs'}), 200
        else:
            return jsonify({'error': f'Failed to get webjob status: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/kseapi/start', methods=['POST'])
def start_kseapi():
    try:
        response = requests.post(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kseapi/run",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Started KSE API webjob successfully'}), 200
        else:
            return jsonify({'error': f'Failed to start webjob: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/kseapi/stop', methods=['POST'])
def stop_kseapi():
    try:
        # Stop the webjob
        response = requests.post(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kseapi/stop",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Stopped KSE API webjob successfully'}), 200
        else:
            return jsonify({'error': f'Failed to stop webjob: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# KSE 1881 endpoints
@trigger_webjobs.route('/kse1881/status', methods=['GET'])
def status_kse1881():
    try:
        response = requests.get(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kse1881/history",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            history = response.json()
            # Check if there's a recent run that's still running
            if history and len(history) > 0:
                latest_run = history[0]
                return jsonify({
                    'running': latest_run.get('status') == 'Running',
                    'message': latest_run.get('status')
                }), 200
            return jsonify({'running': False, 'message': 'No recent runs'}), 200
        else:
            return jsonify({'error': f'Failed to get webjob status: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/kse1881/start', methods=['POST'])
def start_kse1881():
    try:
        response = requests.post(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kse1881/run",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Started KSE 1881 webjob successfully'}), 200
        else:
            return jsonify({'error': f'Failed to start webjob: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trigger_webjobs.route('/kse1881/stop', methods=['POST'])
def stop_kse1881():
    try:
        # Stop the webjob
        response = requests.post(
            f"{WEBJOBS_BASE_URL}/webjobemailsearch-kse1881/stop",
            auth=(WEBJOBS_USER, WEBJOBS_PASS)
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Stopped KSE 1881 webjob successfully'}), 200
        else:
            return jsonify({'error': f'Failed to stop webjob: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
        return jsonify({'error': str(e)}), 500 