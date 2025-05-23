from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import Column, Integer, String, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from .Db import db,get_db_connection

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

# --- SEARCH FUNCTION ---

def search_emails_and_display(batch_size=5):
    global process_running
    try:
        print(f"🔵 process_running is {process_running}")
        print("🔵 search_emails_and_display() started.")
        
        last_id = get_last_processed_id()

        while True:
            print(f"🟡 Fetching batch starting from last_id: {last_id}")
            
            query = text(f"""
                SELECT id, "Org_nr", "Firmanavn"
                FROM imported_table
                WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL AND id > :last_id
                ORDER BY id ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {"last_id": last_id, "limit": batch_size})
            rows = result.fetchall()

            if not rows:
                print("✅ Ingen flere rader å behandle. Exiting loop.")
                break

            print(f"🟡 Behandler batch med {len(rows)} rader (last_id: {last_id}).")

            for row in rows:
                if not process_running:
                    print("🔴 Prosessen er stoppet av brukeren.")
                    break

                row_id, org_nr, company_name = row
                print(f"🔍 Processing org_nr: {org_nr}, company_name: {company_name}")

                search_query = f'"{company_name}" "Norge"'
                print(f"🔍 Søker med query: {search_query}")

                search_results = google_custom_search(search_query)
                all_emails = []
                for url in search_results:
                    if not process_running:
                        print("🔴 Prosessen er stoppet av brukeren.")
                        break
                    print(f"🌐 Extracting emails from URL: {url}")
                    emails = extract_email_selenium(url)
                    all_emails.extend(emails)

                unique_emails = set(all_emails)
                email_list = list(unique_emails)

                if email_list:
                    print(f"📧 Found emails: {email_list}")
                    for email in email_list:
                        insert_query = text("""
                            INSERT INTO search_results ("Org_nr", company_name, email)
                            VALUES (:org_nr, :company_name, :email)
                            ON CONFLICT ("Org_nr", email) DO NOTHING
                        """)
                        db.session.execute(insert_query, {"org_nr": org_nr, "company_name": company_name, "email": email})
                    db.session.commit()
                    print(f"✅ Emails inserted into database for org_nr: {org_nr}")

                last_id = row_id
                update_last_processed_id(new_id=last_id)

            if not process_running:
                print("🔴 Exiting loop as process_running is False.")
                break

        print("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        print(f"❌ Feil i search_emails_and_display(): {str(e)}")
        db.session.rollback()
        return False

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
        email_results = db.session.query(EmailResult).all()
        results = [{
            'id': r.id,
            'Org_nr': r.Org_nr,
            'company_name': r.company_name,
            'email': r.email
        } for r in email_results]
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
        deleted_rows = db.session.query(EmailResult).filter_by(Org_nr=org_nr).delete()
        db.session.commit()
        if deleted_rows:
            return jsonify({"status": f"Slettet {deleted_rows} resultater for org.nr {org_nr}."})
        else:
            return jsonify({"status": f"Ingen rader funnet for org.nr {org_nr}."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Feil under sletting", "error": str(e)}), 500


@email_result_blueprint.route('/update_email', methods=['POST'])
def update_email():
    data = request.get_json()
    org_nr = data.get('org_nr')
    email = data.get('email')

    if not org_nr or not email:
        return jsonify({'error': 'Ugyldige data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Oppdater e-post i imported_table
        cursor.execute(
            "UPDATE imported_table SET e_post_1 = %s WHERE org_nr = %s",
            (email, org_nr)
        )

        # Slett fra EmailResult (search_result)
        cursor.execute(
            "DELETE FROM email_result WHERE org_nr = %s",
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
        print("Feil i update_email:", e)
        return jsonify({'error': 'Intern feil'}), 500

