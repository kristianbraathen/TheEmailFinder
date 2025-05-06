import requests
from datetime import datetime, timedelta
import psycopg2
from flask import Flask, jsonify, Blueprint
from .Db import db
import os

api2_blueprint = Blueprint('api2', __name__)

# SQL Server-tilkobling
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

def get_last_processed_org_nr():
    """Hent det siste behandlet org_nr."""
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_processed_org_nr FROM process_log ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Feil ved henting av siste behandlet org_nr: {e}")
        return None

def update_last_processed_org_nr(org_nr):
    """Oppdater det siste behandlet org_nr."""
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO process_log (last_processed_org_nr)
                VALUES (%s)
            """, (org_nr,))
            conn.commit()
    except Exception as e:
        print(f"Feil ved oppdatering av siste behandlet org_nr: {e}")


def process_organization_with_single_call(org_nr):
    """
    Gjør ett API-kall til Brreg (enheter eller underenheter), sjekker konkursstatus
    og oppdaterer status i databasen.
    """
    try:
        # Prøv enheter først
        response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_nr}")
        if response.status_code != 200:
            # Fallback til underenheter hvis enheter feiler
            response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/underenheter/{org_nr}")
        if response.status_code != 200:
            print(f"Kunne ikke hente data for orgNr {org_nr}.")
            return "error"

        response.raise_for_status()  # Raise exception hvis begge feiler
        data = response.json()

        # Sjekk konkursstatus og oppstartsdato
        is_konkurs, under_avvikling, slettedato, oppstartsdato = extract_company_status(data)

        # Bestem status
        Status = ""  # Python-variabelen med stor S for å matche kolonnen i databasen
        if is_konkurs:
            Status = "konkurs"
        elif under_avvikling:
            Status = "under avvikling"
        elif slettedato:
            Status = "slettet"
        elif oppstartsdato and (datetime.now() - oppstartsdato).days < 3 * 365:
            Status = "oppstart mindre enn 3 år"
        else:
            Status = "aktiv selskap"

        # Oppdater statusfeltet i databasen
        try:
            with psycopg2.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                     UPDATE imported_table
                     SET "Status" = %s
                     WHERE "Org_nr" = %s
                """, (Status, org_nr))
                conn.commit()
                print(f"Status oppdatert til '{Status}' for orgNr {org_nr}.")

            # Hent e-post hvis ingen kritisk status er funnet
            if not is_konkurs and not under_avvikling and not slettedato:
                epost = data.get("epostadresse")

                if epost:
                    with psycopg2.connect(connection_string) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE imported_table
                            SET "E_post_1" = %s
                            WHERE "Org_nr" = %s
                        """, (epost, org_nr))
                        conn.commit()
                        print(f"Oppdatert e-post for orgNr {org_nr}.")
                    return "updated"

            print(f"Ingen e-post funnet for orgNr {org_nr}.")
            return "no_email"

        except requests.RequestException as e:
            print(f"Feil ved API-forespørsel for orgNr {org_nr}: {e}")
            return "error"
    except Exception as e:
        print(f"Feil under prosessering: {e}")
        return "error"


def extract_company_status(data):
    """
    Ekstraherer statusinformasjon fra API-dataene.
    """
    konkurs = data.get('konkurs', False)
    under_avvikling = data.get('underAvvikling', False)
    slettedato_str = data.get('slettedato', None)
    oppstartsdato_str = data.get('registreringsdatoEnhetsregisteret') or data.get('oppstartsdato')

    slettedato = datetime.fromisoformat(slettedato_str) if slettedato_str else None
    oppstartsdato = None
    if oppstartsdato_str:
        try:
            oppstartsdato = datetime.fromisoformat(oppstartsdato_str)
        except ValueError:
            print(f"Ugyldig datoformat: {oppstartsdato_str}")

    is_konkurs = konkurs or under_avvikling or slettedato is not None
    return is_konkurs, under_avvikling, slettedato, oppstartsdato


def process_all_in_batches(batch_size=50):
    """
    Behandler organisasjonene i mindre batcher og viser fremdrift.
    """
    updated_count = 0
    no_email_count = 0
    error_count = 0

    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT "Org_nr" FROM imported_table ORDER BY "id" ASC""")
            org_nrs = [row[0].strip() for row in cursor.fetchall()]

        last_processed_org_nr = get_last_processed_org_nr()

        if last_processed_org_nr:
            # Finn batchen som inneholder det siste behandlede org_nr
            start_index = next((i for i, org_nr in enumerate(org_nrs) if org_nr == last_processed_org_nr), None)
            if start_index is not None:
                # Start fra neste batch
                org_nrs = org_nrs[start_index + 1:]
            else:
                print(f"Fant ikke siste org_nr ({last_processed_org_nr}) i listen.")
        else:
            print("Ingen siste behandlet org_nr funnet, starter fra første batch.")

        total = len(org_nrs)
        batches = [org_nrs[i:i + batch_size] for i in range(0, total, batch_size)]

        print(f"Totalt {total} organisasjonsnummer fordelt på {len(batches)} batcher")

        for index, batch in enumerate(batches, start=1):
            print(f"\n🟡 Starter batch {index}/{len(batches)} ({len(batch)} organisasjoner)")

            for org_nr in batch:
                result = process_organization_with_single_call(org_nr)
                if result == "updated":
                    updated_count += 1
                elif result == "no_email":
                    no_email_count += 1
                else:
                    error_count += 1

                # Oppdater siste behandlet org_nr under prosesseringen
                update_last_processed_org_nr(org_nr)

            print(f"✅ Ferdig med batch {index}. Oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")

    except Exception as e:
        print(f"❌ Feil oppstod under prosessering: {e}")
        error_count += 1

    finally:
        print(f"\n🔚 Ferdig! Totalt oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")
        return updated_count, no_email_count, error_count


@api2_blueprint.route('/process_and_clean_organizations', methods=['POST'])
def process_and_clean_endpoint():
    try:
        updated, no_email, errors = process_all_in_batches()
        return jsonify({
            "status": "Behandling fullført.",
            "updated_count": updated,
            "no_email_count": no_email,
            "error_count": errors
        }), 200
    except Exception as e:
        return jsonify({"error": f"Feil oppstod: {str(e)}"}), 500
