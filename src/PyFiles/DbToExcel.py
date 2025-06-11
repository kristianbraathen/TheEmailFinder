import pandas as pd
from flask import Flask, send_file, Blueprint, request
import io
import psycopg2
import openpyxl
import os
from datetime import datetime

download_blueprint = Blueprint('download', __name__)

# Database-tilkobling
def get_db_connection():
    conn = psycopg2.connect(
        os.getenv('DATABASE_CONNECTION_STRING')  # Sikre at denne er satt i Azure
    )
    return conn

@download_blueprint.route('/export_to_excel', methods=['GET'])
def export_to_excel():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # OBS: PostgreSQL-syntaks
        cursor.execute("SELECT * FROM imported_table")

        rows = cursor.fetchall()

        if not rows:
            return {"error": "Ingen data funnet i tabellen."}, 400

        columns = [col[0] for col in cursor.description]

        # Filtrér bort helt tomme rader
        rows = [row for row in rows if any(val is not None and val != "" for val in row)]

        if not rows:
            return {"error": "Ingen gyldige data funnet i tabellen."}, 400

        df = pd.DataFrame(rows, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        output.seek(0)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Behandlet Liste_{timestamp}.xlsx"

        # Drop both tables after successful export
        cursor.execute("DROP TABLE IF EXISTS imported_table")  # Drop imported_table
        cursor.execute("DROP TABLE IF EXISTS email_results")   # Drop email_results table
        conn.commit()  # Bekreft endringene i databasen

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return {"error": str(e)}, 500
