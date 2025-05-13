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
    Processes all organizations in batches, restarting the function after each batch.
    Prints running totals for progress tracking.
    """
    updated_count = no_email_count = error_count = 0
    total_updated = total_no_email = total_error = 0  # Running totals
    last_id = get_last_processed_id()
    print(f"Siste behandlet ID: {last_id}")

    try:
        while True:
            with psycopg2.connect(connection_string) as conn:
                cursor = conn.cursor()
                # Fetch the next batch of rows
                cursor.execute(
                    'SELECT "Org_nr", "id" FROM imported_table WHERE "id" > %s ORDER BY "id" ASC LIMIT %s',
                    (last_id, batch_size)
                )
                rows = cursor.fetchall()

            if not rows:
                print("Ingen flere organisasjoner å behandle.")
                break

            print(f"🟡 Starter batch med {len(rows)} organisasjoner.")

            for org_nr, _id in rows:
                result = process_organization_with_single_call(org_nr)
                if result == 'updated':
                    updated_count += 1
                elif result == 'no_email':
                    no_email_count += 1
                else:
                    error_count += 1

                # Update the last processed ID
                last_id = _id

            # Update running totals
            total_updated += updated_count
            total_no_email += no_email_count
            total_error += error_count

            # Log batch and running totals
            print(f"✅ Ferdig batch. Oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")
            print(f"🔢 Totalt så langt: Oppdatert: {total_updated}, Ingen e-post: {total_no_email}, Feil: {total_error}")

            # Return intermediate results for the current batch
            yield {
                "updated_count": updated_count,
                "no_email_count": no_email_count,
                "error_count": error_count,
                "total_updated": total_updated,
                "total_no_email": total_no_email,
                "total_error": total_error,
                "last_id": last_id,
            }

            # Reset counts for the next batch
            updated_count = no_email_count = error_count = 0

    except Exception as e:
        print(f"Feil under batch-prosessering: {e}")
        yield {"error": str(e)}

    finally:
        print("🔚 Ferdig med alle batcher.")


@api2_blueprint.route('/process_and_clean_organizations', methods=['POST'])
def process_and_clean_endpoint():
    try:
        results = []
        for batch_result in process_all_in_batches():
            results.append(batch_result)
            # Optionally, you can log or store intermediate results here

        return jsonify({
            'status': 'Behandling fullført.',
            'batches': results
        }), 200
    except Exception as e:
        return jsonify({'error': f'Feil oppstod: {e}'}), 500
