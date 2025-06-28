from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import text, Column, Integer, String, UniqueConstraint, DateTime
from src.PyFiles.Db import db
from datetime import datetime

# Define the EmailResult model
class EmailResult(db.Model):
    __tablename__ = 'email_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Org_nr = Column(String(255), nullable=False)
    Firmanavn = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint('Org_nr', 'email', name='uix_org_nr_email'),
    )

email_result_blueprint = Blueprint('email_result', __name__)
CORS(email_result_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

@email_result_blueprint.route('/initialize-email-results', methods=['POST'])
def initialize_email_results():
    try:
        # Create the email_results table if it doesn't exist
        EmailResult.__table__.create(db.engine, checkfirst=True)
        return jsonify({"status": "success", "message": "Tables initialized"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/get_email_results', methods=['GET'])
def get_email_results():
    try:
        results = db.session.query(EmailResult).order_by(EmailResult.Org_nr).all()
        
        # Group results by Org_nr
        grouped_results = {}
        for result in results:
            if result.Org_nr not in grouped_results:
                grouped_results[result.Org_nr] = {
                    'Org_nr': result.Org_nr,
                    'Firmanavn': result.Firmanavn,
                    'emails': []
                }
            grouped_results[result.Org_nr]['emails'].append(result.email)
        
        return jsonify(list(grouped_results.values())), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/update_email', methods=['POST'])
def update_email():
    try:
        data = request.get_json()
        if not data or 'Org_nr' not in data or 'Firmanavn' not in data or 'email' not in data:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Check if record exists
        existing = db.session.query(EmailResult).filter_by(
            Org_nr=data['Org_nr'],
            email=data['email']
        ).first()

        if existing:
            # Update existing record
            existing.Firmanavn = data['Firmanavn']
        else:
            # Create new record
            new_result = EmailResult(
                Org_nr=data['Org_nr'],
                Firmanavn=data['Firmanavn'],
                email=data['email']
            )
            db.session.add(new_result)

        db.session.commit()
        return jsonify({"status": "success", "message": "Email updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/delete_stored_result', methods=['POST'])
def delete_stored_result():
    try:
        data = request.get_json()
        if not data or 'org_nr' not in data:
            return jsonify({"status": "error", "message": "Missing org_nr field"}), 400

        # Delete all records for the given Org_nr
        db.session.query(EmailResult).filter_by(Org_nr=data['org_nr']).delete()
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Records deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500 