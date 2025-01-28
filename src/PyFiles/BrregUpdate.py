import requests
from datetime import datetime, timedelta
import pyodbc
from flask import Flask, jsonify, Blueprint
from Db import db
api2_blueprint = Blueprint('api2', __name__)

# SQL Server-tilkobling
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

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
        status = ""
        if is_konkurs:
            status = "konkurs"
        elif under_avvikling:
            status = "under avvikling"
        elif slettedato:
            status = "slettet"
        elif oppstartsdato and (datetime.now() - oppstartsdato).days < 3 * 365:
            status = "oppstart mindre enn 3 år"
        else:
            status = "aktiv selskap"

        # Oppdater statusfeltet i databasen
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE [dbo].[imported_table]
                SET status = ?
                WHERE [org.nr] = ?
            """, (status, org_nr))
            conn.commit()
            print(f"Status oppdatert til '{status}' for orgNr {org_nr}.")

        # Hent e-post hvis ingen kritisk status er funnet
        if not is_konkurs and not under_avvikling and not slettedato:
            epost = data.get("epostadresse")

            if epost:
                with pyodbc.connect(connection_string) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE [dbo].[imported_table]
                        SET [e-post 1] = ?
                        WHERE [org.nr] = ?
                    """, (epost, org_nr))
                    conn.commit()
                    print(f"Oppdatert e-post for orgNr {org_nr}.")
                return "updated"

        print(f"Ingen e-post funnet for orgNr {org_nr}.")
        return "no_email"

    except requests.RequestException as e:
        print(f"Feil ved API-forespørsel for orgNr {org_nr}: {e}")
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

def process_and_clean_organizations():
    """
    Behandler alle organisasjoner i databasen:
    - Oppdaterer statusfeltet for hver organisasjon.
    """
    updated_count = 0
    no_email_count = 0
    error_count = 0

    try:
        # Hent org.nr fra tabellen
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT [Org.nr] FROM [dbo].[imported_table]
            """)
            # Hent resultatene fra andre kolonne
            org_nrs = {row[0].strip() for row in cursor.fetchall()}

        # Behandle hver organisasjon
        for org_nr in org_nrs:
            result = process_organization_with_single_call(org_nr)
            if result == "updated":
                updated_count += 1
            elif result == "no_email":
                no_email_count += 1
            else:
                error_count += 1

    except Exception as e:
        print(f"Feil oppstod under prosessering: {e}")
        error_count += 1

    finally:
        print(f"Oppdatert: {updated_count}, Ingen e-post: {no_email_count}, Feil: {error_count}")
        return updated_count, no_email_count, error_count


@api2_blueprint.route('/process_and_clean_organizations', methods=['POST'])
def process_and_clean_endpoint():
    try:
        updated, no_email, errors = process_and_clean_organizations()
        return jsonify({
            "status": "Behandling fullført.",
            "updated_count": updated,
            "no_email_count": no_email,
            "error_count": errors
        }), 200
    except Exception as e:
        return jsonify({"error": f"Feil oppstod: {str(e)}"}), 500
