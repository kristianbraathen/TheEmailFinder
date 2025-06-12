from flask import Blueprint, jsonify
from flask_cors import CORS
from sqlalchemy import text, Column, Integer, String, UniqueConstraint
from src.PyFiles.Db import db

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