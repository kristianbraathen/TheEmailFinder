from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
import requests

app = Flask("Email_finder")
CORS(app)
# Funksjon for å koble til databasen
def connect_to_database():
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=master;"
            "Trusted_Connection=yes;"
        )
        return connection
    except pyodbc.Error as e:
        print("Kunne ikke koble til databasen:", e)
        return None

# Funksjon for å søke på organisasjonsnummeret via API-et
def search_organization(org_nr):
    url = f"https://services.api1881.no/lookup/organizationnumber/{org_nr}"
    headers = {
        "Ocp-Apim-Subscription-Key": "7b4e753ef731471784eab6a298d61f61"  # Legg til din Subscription Key her
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"En feil oppstod under forespørselen: {e}")
        return None

# Funksjon for å hente e-post fra kontaktpunkter
def extract_email(contact_points):
    for contact in contact_points:
        if contact['type'] == 'Email':
            return contact['value']
    return None

# API-endepunkt for å søke etter e-poster for et organisasjonsnummer
@app.route('/search_email/<org_nr>', methods=['GET'])
def search_email(org_nr):
    connection = connect_to_database()
    if connection is None:
        return jsonify({"error": "Kunne ikke koble til databasen"}), 500

    cursor = connection.cursor()
    cursor.execute("SELECT org_nr FROM [FirmaListe].[dbo].[underenheter] WHERE org_nr = ?", (org_nr,))
    row = cursor.fetchone()

    if row:
        result = search_organization(org_nr)
        if result:
            contact_points = result.get("contactPoints", [])
            email = extract_email(contact_points)
            if email:
                return jsonify({"org_nr": org_nr, "email": email})
            else:
                return jsonify({"org_nr": org_nr, "message": "Ingen e-post funnet"})
        else:
            return jsonify({"org_nr": org_nr, "message": "Ingen data funnet"})
    else:
        return jsonify({"error": "Organisasjonsnummer ikke funnet i databasen"}), 404


