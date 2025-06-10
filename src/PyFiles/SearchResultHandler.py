from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import Column, Integer, String, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from .Db import db,get_db_connection
import psycopg2
import logging
from .GoogleKse import GoogleKse

Base = declarative_base()
email_result_blueprint = Blueprint('email_result', __name__)
CORS(email_result_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

# --- MODELS ---

class ProcessStatus(Base):
    __tablename__ = 'process_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_name = Column(String(255), nullable=False, unique=True)
    last_processed_id = Column(Integer, nullable=False, default=0)

class EmailSearch(Base):
    __tablename__ = 'email_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Org_nr = Column(String(255), nullable=False)
    Firmanavn = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint('Org_nr', 'email', name='uix_org_nr_email'),
    )

# --- INIT FUNCTIONS ---

def create_tables():
    Base.metadata.create_all(db.engine)

# --- PROCESS STATUS HELPERS ---

PROCESS_NAME_EMAIL_SEARCH = "email_search"

def get_last_processed_id(process_name=PROCESS_NAME_EMAIL_SEARCH):
    status = db.session.query(ProcessStatus).filter_by(process_name=process_name).first()
    if status:
        return status.last_processed_id
    else:
        new_status = ProcessStatus(process_name=process_name, last_processed_id=0)
        db.session.add(new_status)
        db.session.commit()
        return 0

def update_last_processed_id(process_name=PROCESS_NAME_EMAIL_SEARCH, new_id=None):
    if new_id is None:
        return
    status = db.session.query(ProcessStatus).filter_by(process_name=process_name).first()
    if status:
        status.last_processed_id = new_id
    else:
        status = ProcessStatus(process_name=process_name, last_processed_id=new_id)
        db.session.add(status)
    db.session.commit()

class SearchResultHandler:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchResultHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.process_running = False
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def search_emails_and_display(self, batch_size=5, force_run=False):
        try:
            if self.process_running and not force_run:
                self.logger.warning("Process is already running")
                return False

            self.process_running = True
            self.logger.info("Email search process started")

            while True:
                query = text("""
                    SELECT id, "Org_nr", "Firmanavn"
                    FROM imported_table
                    WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL
                    ORDER BY id ASC
                    LIMIT :limit
                """)
                result = db.session.execute(query, {"limit": batch_size})
                rows = result.fetchall()

                if not rows:
                    self.logger.info("No more companies to process")
                    break

                for row in rows:
                    if not (self.process_running or force_run):
                        break

                    row_id, org_nr, firmanavn = row
                    search_query = f'"{firmanavn}" "Norge"'
                    google_kse = GoogleKse.get_instance()
                    search_results = google_kse.search_company(firmanavn)
                    all_emails = []
                    
                    for url in search_results:
                        if not self.process_running:
                            break
                        emails = google_kse.extract_email_selenium(url)
                        all_emails.extend(emails)

                    unique_emails = set(all_emails)
                    email_list = list(unique_emails)

                    if email_list:
                        for email in email_list:
                            insert_query = text("""
                                INSERT INTO email_results ("Org_nr", "Firmanavn", email)
                                VALUES (:org_nr, :firmanavn, :email)
                                ON CONFLICT ("Org_nr", email) DO NOTHING
                            """)
                            db.session.execute(insert_query, {"org_nr": org_nr, "firmanavn": firmanavn, "email": email})
                        db.session.commit()

                if not self.process_running:
                    break

            self.process_running = False
            return True

        except Exception as e:
            self.logger.error(f"Error in search process: {str(e)}")
            db.session.rollback()
            self.process_running = False
            return False
        finally:
            if not force_run:
                self.stop()
                if hasattr(google_kse, 'stop'):
                    google_kse.stop()

# --- FLASK ROUTES ---

@email_result_blueprint.route('/initialize-email-results', methods=['POST'])
def initialize_email_results():
    try:
        create_tables()
        return jsonify({'status': 'Tables created or already exist.'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to create tables: {str(e)}'}), 500

@email_result_blueprint.route('/get_email_results', methods=['GET'])
def get_email_results():
    try:
        # Ensure table exists
        create_tables()
        
        query = text('SELECT id, "Org_nr", "Firmanavn", email FROM email_results')
        result = db.session.execute(query)
        results = [{
            'id': r.id,
            'Org_nr': r.Org_nr,
            'Firmanavn': r.Firmanavn,
            'email': r.email
        } for r in result]
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
        query = text('DELETE FROM email_results WHERE "Org_nr" = :org_nr')
        result = db.session.execute(query, {"org_nr": org_nr})
        db.session.commit()
        if result.rowcount:
            return jsonify({"status": f"Slettet {result.rowcount} resultater for org.nr {org_nr}."})
        else:
            return jsonify({"status": f"Ingen rader funnet for org.nr {org_nr}."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Feil under sletting", "error": str(e)}), 500


@email_result_blueprint.route('/update_email', methods=['POST'])
def update_email():
    data = request.get_json()
    org_nr = data.get('Org_nr')
    email = data.get('email')

    if not org_nr or not email:
        return jsonify({'error': 'Ugyldige data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Oppdater e-post i imported_table
        cursor.execute(
            'UPDATE imported_table SET "E_post_1" = %s WHERE "Org_nr" = %s',
            (email, str(org_nr))
        )

        # Slett fra EmailResult (search_result)
        cursor.execute(
            'DELETE FROM email_results WHERE "Org_nr" = %s',
            (org_nr,)
        )
        deleted_rows = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'status': f"E-post oppdatert og {deleted_rows} søkeresultat(er) slettet for org.nr {org_nr}."
        }), 200

    except Exception as e:
        print(f"Feil ved oppdatering/sletting: {e}")  # Logg feilen
        return jsonify({'error': 'Intern feil', 'details': str(e)}), 500


