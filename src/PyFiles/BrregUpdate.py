import requests
from datetime import datetime
import psycopg2
from flask import Flask, jsonify, Blueprint
from .Db import db
import os

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


def process_organization_with_single_call(org_nr):
    """
    Gjør ett API-kall til Brreg, sjekker status og oppdaterer databasen.
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
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE imported_table SET "Status" = %s WHERE "Org_nr" = %s',
                (status, org_nr)
            )
            conn.commit()

        # Hent e-post om status kun er aktiv
        if status == 'aktiv selskap':
            epost = data.get('epostadresse')
            if epost:
                with psycopg2.connect(connection_string) as conn:
                    cursor = conn.cursor()
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
    Behandler organisasjoner i batcher basert på siste behandlet id.
    """
    updated_count = no_email_count = error_count = 0
    last_id = get_last_processed_id()
    print(f"Siste behandlet ID: {last_id}")

    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT "Org_nr", "id" FROM imported_table WHERE "id" > %s ORDER BY "id" ASC',
                (last_id,)
            )
            rows = cursor.fetchall()

        if not rows:
            print("Ingen nye organisasjoner å behandle.")
            return updated_count, no_email_count, error_count

        # Del opp i batcher
        for batch_start in range(0, len(rows), batch_size):
            batch = rows[batch_start:batch_start + batch_size]
            print(f"🟡 Starter batch {batch_start // batch_size + 1}/{(len(rows)-1)//batch_size+1}")

            for org_nr, _id in batch:
                result = process_organization_with_single_call(org_nr)
                if result == 'updated':
                    updated_count += 1
                elif result == 'no_email':
                    no_email_count += 1
                else:
                    error_count += 1

            print(f"✅ Ferdig batch {batch_start // batch_size + 1}. Oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")
            time.sleep(1)

    except Exception as e:
        print(f"Feil under batch-prosessering: {e}")
        error_count += 1

    finally:
        print(f"🔚 Ferdig! Oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")
        return updated_count, no_email_count, error_count


@api2_blueprint.route('/process_and_clean_organizations', methods=['POST'])
def process_and_clean_endpoint():
    try:
        updated, no_email, errors = process_all_in_batches()
        return jsonify({
            'status': 'Behandling fullført.',
            'updated_count': updated,
            'no_email_count': no_email,
            'error_count': errors
        }), 200
    except Exception as e:
        return jsonify({'error': f'Feil oppstod: {e}'}), 500
