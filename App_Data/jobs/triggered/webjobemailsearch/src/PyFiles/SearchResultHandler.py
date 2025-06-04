_instance = None  # Singleton instance for SearchResultHandler

from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import Column, Integer, String, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from .Db import db, get_db_connection
import psycopg2
import logging
import os

# Define STOP_FLAG_FILE path
STOP_FLAG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "stop_webjob.flag")

Base = declarative_base()
email_result_blueprint = Blueprint('email_result', __name__)
CORS(email_result_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

# --- MODELS ---

class EmailResult(Base):
    __tablename__ = 'search_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Org_nr = Column(Integer, nullable=False)
    company_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint('Org_nr', 'email', name='uq_org_email'),)


class ProcessStatus(Base):
    __tablename__ = 'process_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_name = Column(String(255), nullable=False, unique=True)
    last_processed_id = Column(Integer, nullable=False, default=0)

# --- INIT FUNCTIONS ---

def create_tables():
    try:
        # Create tables
        Base.metadata.create_all(db.engine)
        
        # Ensure the unique constraint exists
        with db.engine.connect() as conn:
            # Check if constraint exists
            result = conn.execute(text("""
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_org_email' 
                AND conrelid = 'search_results'::regclass
            """))
            if not result.scalar():
                # Add constraint if it doesn't exist
                conn.execute(text("""
                    ALTER TABLE search_results 
                    ADD CONSTRAINT uq_org_email 
                    UNIQUE ("Org_nr", email)
                """))
                conn.commit()
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        raise

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

# --- SEARCH FUNCTION ---

class SearchResultHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process_running = True
        
    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
            _instance.logger.info("[INSTANCE] Created new SearchResultHandler instance")
        return _instance
        
    def start(self):
        self.process_running = True
        self.logger.info("[START] Process started")
        
    def stop(self):
        self.process_running = False
        self.logger.info("[STOP] Process stopped by user")
        
    def check_stop(self, force_run=False):
        if os.path.exists(STOP_FLAG_FILE):
            self.logger.info("[STOP] Stop flag detected, stopping process")
            self.process_running = False
            try:
                os.remove(STOP_FLAG_FILE)
                self.logger.info("[STOP] Stop flag removed")
            except Exception as e:
                self.logger.warning(f"[STOP] Could not remove stop flag: {e}")
            return True
            
        if not force_run and not self.process_running:
            self.logger.info("[STOP] Process stopped by user")
            return True
        return False

def search_emails_and_display(search_provider=None, batch_size=5, force_run=False):
    """Main search function that uses a search provider to find emails
    Args:
        search_provider: Instance of a search provider (GoogleKse, KseApi, etc.)
        batch_size (int): Number of records to process per batch
        force_run (bool): Whether to force continue running even if process_running is False
    Returns:
        bool: True if successful, False otherwise
    """
    instance = SearchResultHandler.get_instance()
    
    # Check if we can start
    if not force_run and hasattr(search_provider, 'process_running') and not search_provider.process_running:
        instance.logger.info("🔴 Cannot start: provider process_running is False")
        return False
        
    try:
        # Ensure tables and constraints exist
        create_tables()
        
        # Ensure process is started and log initial state
        instance.start()  # This sets process_running to True
        if hasattr(search_provider, 'start'):
            search_provider.start()  # Ensure provider is also started
            
        instance.logger.info(f"🔵 process_running is {instance.process_running}")
        instance.logger.info("🔵 search_emails_and_display() started.")
        
        if search_provider is None:
            instance.logger.error("❌ No search provider specified")
            return False

        last_id = get_last_processed_id()

        while True:  # Changed to always check conditions inside loop
            if not (instance.process_running or force_run):
                instance.logger.info("🔴 Process stopped by user")
                break

            instance.logger.info(f"🟡 Fetching batch starting from last_id: {last_id}")
            
            query = text("""
                SELECT id, "Org_nr", "Firmanavn"
                FROM imported_table
                WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL AND id > :last_id
                ORDER BY id ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {"last_id": last_id, "limit": batch_size})
            rows = result.fetchall()

            if not rows:
                instance.logger.info("✅ No more records to process. Exiting loop.")
                break

            instance.logger.info(f"🟡 Processing batch of {len(rows)} records (last_id: {last_id}).")

            for row in rows:
                if not (instance.process_running or force_run):
                    instance.logger.info("🔴 Process stopped by user")
                    break

                row_id, org_nr, company_name = row
                instance.logger.info(f"🔍 Processing org_nr: {org_nr}, company_name: {company_name}")

                # Use the search provider to find emails
                email_list = search_provider.search_company(company_name)

                if email_list:
                    instance.logger.info(f"📧 Found {len(email_list)} unique emails for org_nr {org_nr}")
                    for email in email_list:
                        insert_query = text("""
                            INSERT INTO search_results ("Org_nr", company_name, email)
                            VALUES (:org_nr, :company_name, :email)
                            ON CONFLICT ("Org_nr", email) DO NOTHING
                        """)
                        db.session.execute(insert_query, {"org_nr": org_nr, "company_name": company_name, "email": email})
                    db.session.commit()
                    instance.logger.info(f"✅ Emails saved for org_nr: {org_nr}")

                last_id = row_id
                update_last_processed_id(new_id=last_id)

        instance.logger.info("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        instance.logger.error(f"❌ Error in search_emails_and_display(): {str(e)}")
        db.session.rollback()
        return False
    finally:
        if not force_run:  # Only stop if not force_run
            instance.stop()
            if hasattr(search_provider, 'stop'):
                search_provider.stop()
        instance.logger.info(f"🔄 Final process state - running: {instance.process_running}, force_run: {force_run}")

# --- FLASK ROUTES ---

@email_result_blueprint.route('/initialize-email-results', methods=['POST'])
def initialize_email_results():
    try:
        create_tables()
        return jsonify({"status": "success", "message": "Tables initialized"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/get_email_results', methods=['GET'])
def get_email_results():
    try:
        results = db.session.query(EmailResult).all()
        return jsonify([{"id": r.id, "Org_nr": r.Org_nr, "company_name": r.company_name, "email": r.email} for r in results]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/delete_stored_result', methods=['POST'])
def delete_stored_result():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"status": "error", "message": "No ID provided"}), 400
        result = db.session.query(EmailResult).filter_by(id=data['id']).first()
        if result:
            db.session.delete(result)
            db.session.commit()
            return jsonify({"status": "success", "message": "Result deleted"}), 200
        return jsonify({"status": "error", "message": "Result not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@email_result_blueprint.route('/update_email', methods=['POST'])
def update_email():
    try:
        data = request.get_json()
        if not data or 'id' not in data or 'email' not in data:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        result = db.session.query(EmailResult).filter_by(id=data['id']).first()
        if result:
            result.email = data['email']
            db.session.commit()
            return jsonify({"status": "success", "message": "Email updated"}), 200
        return jsonify({"status": "error", "message": "Result not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


