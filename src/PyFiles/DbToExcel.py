import pandas as pd
from flask import Flask, send_file, Blueprint, request
import io
import psycopg2
import openpyxl
import os

download_blueprint = Blueprint('download', __name__)

# Database-tilkobling
def get_db_connection():
    conn = psycopg2.connect(
        os.getenv('DATABASE_CONNECTION_STRING')  # Hent verdien fra miljøvariabelen
    )
    return conn
@download_blueprint.route('/export_to_excel', methods=['GET'])
def export_to_excel():
    try:
        # Hente data fra databasen
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQL-spørring for å hente alle rader og kolonner fra tabellen
        cursor.execute("SELECT * FROM [dbo].[imported_table]")  # Bytt ut med riktig tabellnavn

        # Hent alle resultatene
        rows = cursor.fetchall()

        # Sjekk om vi fikk noen data
        if not rows:
            return {"error": "Ingen data funnet i tabellen."}, 400

        # Hent kolonnenavn
        columns = [column[0] for column in cursor.description]

        # Filtrer bort tomme rader (radene som kun inneholder None eller tomme strenger)
        rows = [row for row in rows if any(value is not None and value != "" for value in row)]

        # Hvis det ikke er noen rader igjen etter filtrering
        if not rows:
            return {"error": "Ingen gyldige data funnet i tabellen."}, 400

        # Logg kolonnene og de første radene for debugging
        print(f"Kolonner: {columns}")
        print(f"De første radene: {rows[:5]}")

        # Lag en DataFrame fra records
        df = pd.DataFrame.from_records(rows, columns=columns)


        # Lagre til en Excel-fil i minnet
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Data")

        # Gå tilbake til starten av minnet
        output.seek(0)

        # Returner filen som en nedlastbar ressurs
        return send_file(
            output,
            as_attachment=True,
            download_name="exported_data.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return {"error": str(e)}, 500
