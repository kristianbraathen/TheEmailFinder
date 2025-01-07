# -*- coding: utf-8 -*-
from flask import Flask, jsonify,Blueprint, request
from flask_cors import CORS
import pyodbc
import requests

api1_blueprint = Blueprint('api1', __name__)

# Database connection string
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
)

# Fetch all org_nrs from the database where e_post and e_post2 are NULL
def fetch_org_nrs():
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT org_nr FROM [FirmaListe].[dbo].[FullListe] WHERE [e_post] IS NULL AND [e_post2] IS NULL")
            org_nrs = {row[0].replace(" ", "") for row in cursor.fetchall()}
            return org_nrs
    except Exception as e:
        print(f"Feil ved henting av org_nrs fra databasen: {e}")
        return []

# Update email in DB
def update_email_in_db(org_nr, epost, hjemmeside=None):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            update_query = """
                UPDATE [FirmaListe].[dbo].[FullListe]
                SET e_post = ?, hjemmeside = ?,forretningsadresse = ?
                WHERE org_nr = ?
            """
            cursor.execute(update_query, (epost, hjemmeside, org_nr))
            conn.commit()
            print(f"Oppdatert info for org_nr {org_nr} i databasen.")
    except Exception as e:
        print(f"Feil ved oppdatering av databasen for orgNr {org_nr}: {e}")

# Check email from enheter API
def check_email_from_enheter(org_nr):
    try:
        response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_nr}")
        response.raise_for_status()
        data = response.json()
        epost = data.get("epostadresse")
        hjemmeside = data.get("hjemmeside")
        forretningsadresse = data.get("forretningsadresse")

        if epost:
            if hjemmeside:
                update_email_in_db(org_nr, epost, hjemmeside,forretningsadresse)
            else:
                update_email_in_db(org_nr, epost,forretningsadresse)
        else:
            print(f"Fant ikke e-post for {org_nr} fra enheter.")
    except requests.RequestException as e:
      print(f"Feil ved API-forespørsel til enheter for orgNr {org_nr}: {e}")



# Check email from underenheter API
def check_email_from_underenheter(org_nr):
    try:
        response = requests.get(f"https://data.brreg.no/enhetsregisteret/api/underenheter/{org_nr}")
        response.raise_for_status()
        data = response.json()
        epost = data.get("epostadresse")
        hjemmeside = data.get("hjemmeside") 
        forretningsadresse = data.get("forretningsadresse")

        if epost:
            if hjemmeside:
                update_email_in_db(org_nr, epost, hjemmeside,forretningsadresse)
            else:
                update_email_in_db(org_nr, epost,forretningsadresse)
        else:
            print(f"Fant ikke e-post for {org_nr} fra underenheter.")
    except requests.RequestException as e:
        print(f"Feil ved API-forespørsel til underenheter for orgNr {org_nr}: {e}")

# API-endepunkter
@api1_blueprint.route('/process_all_organizations', methods=['GET'])
def process_all_organizations():
    org_nrs = fetch_org_nrs()
    for org_nr in org_nrs:
        check_email_from_enheter(org_nr)
        check_email_from_underenheter(org_nr)
    return jsonify({"status": "Processing completed."})



   
