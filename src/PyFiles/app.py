from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import urllib.parse
import sys
from Db import db
from brregEmails import api1_blueprint
from BrregUpdate import api2_blueprint
from KseApi import api3_blueprint
from SeleniumScrap import api4_blueprint
from Kseapi1881 import api5_blueprint
from ExcelHandler import upload_blueprint
from DbToExcel import download_blueprint

# Global UnicodeDecodeError handling
def handle_unicode_errors(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, UnicodeDecodeError):
        print(f"UnicodeDecodeError caught: {exc_value}")
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_unicode_errors
app = Flask(__name__)

# CORS Configuration
CORS(app, origins=["http://localhost:8080, http://emailfinder-h0g7f5hpa4eggcbb.norwayeast-01.azurewebsites.net"])

   # Retrieve the connection string from the environment variable
database_url = os.getenv('DATABASE_URL') or os.getenv('AZURE_POSTGRESQL_CONNECTIONSTRING')

if not database_url:
    raise ValueError("No database URL provided in environment variables.")

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
app.register_blueprint(download_blueprint, url_prefix="/DbToExcel")

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
    # Hent portnummer fra miljøvariabelen, eller bruk 8000 som standard
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
