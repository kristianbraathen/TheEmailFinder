import requests
from datetime import datetime
import psycopg2
from flask import Flask, jsonify, Blueprint
from .Db import db
import os
import threading

api2_blueprint = Blueprint('api2', __name__)

# SQL Server-tilkobling
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

def get_last_processed_id():
    """
    Hent høyeste 'id' fra imported_table hvor Status allerede er satt.
    """
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT MAX("id") FROM imported_table WHERE "Status" IS NOT NULL'
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
    except Exception as e:
        print(f"Feil ved henting av siste id: {e}")
        return 0

def process_organization_with_single_call(org_nr, cursor, conn):
    """
    Gjør ett API-kall til Brreg, sjekker status og oppdaterer databasen.
    Bruker eksisterende cursor og connection.
    """
    try:
        # Hent data fra Brreg API
        response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_nr}")
        if response.status_code != 200:
            response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/underenheter/{org_nr}")
        response.raise_for_status()
        data = response.json()

        # Ekstraher status
        is_konkurs, under_avvikling, slettedato, oppstartsdato = extract_company_status(data)
        if is_konkurs:
            status = 'konkurs'
        elif under_avvikling:
            status = 'under avvikling'
        elif slettedato:
            status = 'slettet'
        elif oppstartsdato and (datetime.now() - oppstartsdato).days < 3 * 365:
            status = 'oppstart mindre enn 3 år'
        else:
            status = 'aktiv selskap'

        # Oppdater status
        cursor.execute(
            'UPDATE imported_table SET "Status" = %s WHERE "Org_nr" = %s',
            (status, org_nr)
        )
        conn.commit()

        # Hent e-post om status kun er aktiv
        if status == 'aktiv selskap':
            epost = data.get('epostadresse')
            if epost:
                cursor.execute(
                    'UPDATE imported_table SET "E_post_1" = %s WHERE "Org_nr" = %s',
                    (epost, org_nr)
                )
                conn.commit()
                return 'updated'
        return 'no_email'

    except Exception as e:
        print(f"Feil under prosessering av {org_nr}: {e}")
        return 'error'

def extract_company_status(data):
    """
    Ekstraherer konkurs- og dato-informasjon fra API-data.
    """
    konkurs = data.get('konkurs', False)
    under_avvikling = data.get('underAvvikling', False)
    slettedato_str = data.get('slettedato')
    oppstartsdato_str = data.get('registreringsdatoEnhetsregisteret') or data.get('oppstartsdato')

    slettedato = datetime.fromisoformat(slettedato_str) if slettedato_str else None
    oppstartsdato = None
    if oppstartsdato_str:
        try:
            oppstartsdato = datetime.fromisoformat(oppstartsdato_str)
        except ValueError:
            print(f"Ugyldig datoformat: {oppstartsdato_str}")

    is_konkurs = bool(konkurs or under_avvikling or slettedato)
    return is_konkurs, under_avvikling, slettedato, oppstartsdato

def process_all_in_batches(batch_size=50):
    """
    Processes all organizations in batches based on rows where Status is NULL.
    Each batch uses a new DB connection and commits changes immediately.
    """
    try:
        while True:
            with psycopg2.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT "Org_nr", "id" FROM imported_table WHERE "Status" IS NULL ORDER BY "id" ASC LIMIT %s',
                    (batch_size,)
                )
                rows = cursor.fetchall()

                if not rows:
                    print("✅ Ingen flere organisasjoner å behandle.")
                    break

                print(f"🟡 Behandler batch med {len(rows)} organisasjoner...")

                for org_nr, _id in rows:
                    try:
                        result = process_organization_with_single_call(org_nr, cursor, conn)
                        print(f"✅ Org {org_nr}: {result}")
                    except Exception as e:
                        print(f"❌ Feil under prosessering av {org_nr} (id={_id}): {e}")

    except Exception as e:
        print(f"🚨 Kritisk feil under batch-prosessering: {e}")


process_running = False
process_lock = threading.Lock()

@api2_blueprint.route('/start_process_and_clean', methods=['POST'])
def start_process_and_clean():
    global process_running

    with process_lock:
        if process_running:
            return jsonify({"status": "Already running"}), 400

        process_running = True

        def background_job():
            try:
                process_all_in_batches()
            finally:
                global process_running
                with process_lock:
                    process_running = False

        threading.Thread(target=background_job, daemon=True).start()
        return jsonify({"status": "Processing started"}), 202

@api2_blueprint.route('/status', methods=['GET'])
def get_status():
    return jsonify({"running": process_running})

@api2_blueprint.route('/progress_summary', methods=['GET'])
def progress_summary():
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            # Count all companies
            cursor.execute('SELECT COUNT(*) FROM imported_table')
            total_num = cursor.fetchone()[0]
            # Count all active companies
            cursor.execute('SELECT COUNT(*) FROM imported_table WHERE "Status" = %s', ('aktiv selskap',))
            total_aktiv = cursor.fetchone()[0]
            # Count all active companies with a non-null email
            cursor.execute('SELECT COUNT(*) FROM imported_table WHERE "Status" = %s AND "E_post_1" IS NOT NULL', ('aktiv selskap',))
            with_email = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM imported_table WHERE "Status" IS NULL')
            remaining = cursor.fetchone()[0]
            last_id = get_last_processed_id()
        return jsonify({
            "total_num": total_num,
            "aktiv_selskap": total_aktiv,
            "aktiv_selskap_med_epost": with_email,
            "ikke_prosessert": remaining,
            "last_id": last_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
