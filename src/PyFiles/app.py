from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from Db import db  # Import the db object from db.py
from brregEmails import api1_blueprint
from BrregUpdate import api2_blueprint
from KseApi import api3_blueprint
from SeleniumScrap import api4_blueprint
from ExcelHandler import upload_blueprint
from Kseapi1881 import api5_blueprint
import urllib.parse
import os

app = Flask(__name__)

# CORS Configuration
CORS(app, origins=["http://localhost:8080"])

# Database Configuration
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
)
params = urllib.parse.quote_plus(connection_string)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # For 16MB limit

# Uploads Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Initialize db with app (using init_app)
db.init_app(app)

# Ensure uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Create tables in the database (this should happen after db.init_app)
with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(api1_blueprint, url_prefix="/brregEmails")
app.register_blueprint(api2_blueprint, url_prefix="/BrregUpdate")
app.register_blueprint(api3_blueprint, url_prefix="/KseApi")
app.register_blueprint(api4_blueprint, url_prefix="/SeleniumScrap")
app.register_blueprint(api5_blueprint, url_prefix="/Kseapi1881")
app.register_blueprint(upload_blueprint, url_prefix="/ExcelHandler")

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/health")
def health_check():
    return jsonify({
        "status": "OK",
        "db_connection": db.session.bind.url.database
    })

if __name__ == "__main__":
    app.run(debug=True)
