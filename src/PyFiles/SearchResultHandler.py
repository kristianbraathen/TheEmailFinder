from flask import Blueprint, jsonify
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from .Db import db

# Initialize the declarative base
Base = declarative_base()
email_result_blueprint = Blueprint('email_result', __name__)

# Define the SQLAlchemy model for the email_results table
class EmailResult(Base):
    __tablename__ = 'search_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Org_nr = Column(Integer, nullable=False)
    company_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)

# Function to create the email_results table
def create_email_results_table():
    Base.metadata.create_all(db.engine)

# Route to initialize the email_results table
@email_result_blueprint.route('/initialize-email-results', methods=['POST'])
def initialize_email_results():
    try:
        create_email_results_table()
        return jsonify({'status': 'email_results table created successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to create email_results table: {str(e)}'}), 500

@email_result_blueprint.route('/get-email-results', methods=['GET'])
def get_email_results():
    try:
        # Query the database for all EmailResult entries
        email_results = db.session.query(EmailResult).all()
        
        # Convert the result into a list of dictionaries
        results = []
        for result in email_results:
            results.append({
                'id': result.id,
                'Org_nr': result.Org_nr,
                'company_name': result.company_name,
                'email': result.email,
            })
        
        # Return the results as JSON
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch email results: {str(e)}'}), 500

@email_result_blueprint.route('/delete_stored_result', methods=['POST'])
def delete_stored_result():
    data = request.get_json()
    org_nr = data.get("org_nr")

    if not org_nr:
        return jsonify({"status": "Feil: Org.nr mangler"}), 400

    try:
        # Slett alle rader knyttet til denne orgenheten
        deleted_rows = db_session.query(EmailResult).filter_by(org_nr=org_nr).delete()
        db_session.commit()

        if deleted_rows:
            return jsonify({"status": f"Slettet {deleted_rows} resultater for org.nr {org_nr}."})
        else:
            return jsonify({"status": f"Ingen rader funnet for org.nr {org_nr}."})

    except Exception as e:
        db_session.rollback()
        return jsonify({"status": "Feil under sletting", "error": str(e)}), 500

@email_result_blueprint.route("/update_email", methods=["POST"])
def update_email():
    try:
        # Parse the request JSON
        data = request.get_json()
        org_nr = data.get("org_nr")
        email = data.get("email")

        if not org_nr or not email:
            return jsonify({"error": "Org.nr and email are required."}), 400

        # Perform the update in the database
        query = text(
            'UPDATE imported_table SET "e_post_1" = :email WHERE "org_nr" = :org_nr'
        )
        db.session.execute(query, {"email": email, "org_nr": org_nr})
        db.session.commit()

        return jsonify({"status": "E-post oppdatert!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500
