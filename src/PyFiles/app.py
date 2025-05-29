from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import sys
from .Db import db
from .BrregUpdate import api2_blueprint
from .KseApi import api3_blueprint
from .SeleniumScrap import api4_blueprint
#from .Kseapi1881 import api5_blueprint
from .ExcelHandler import upload_blueprint
from .DbToExcel import download_blueprint
from .GoogleKse import api6_blueprint
from .SearchResultHandler import email_result_blueprint
from .trigger_webjobs import trigger_webjobs


# Global UnicodeDecodeError handling
def handle_unicode_errors(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, UnicodeDecodeError):
        print(f"UnicodeDecodeError caught: {exc_value}")
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_unicode_errors
app = Flask(__name__, static_folder='../../dist', static_url_path='/')



# CORS Configuration
CORS(app, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net","http://localhost:8080"])

# Retrieve the connection string from the environment variable
database_url = os.getenv('DATABASE_CONNECTION_STRING')

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
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Create tables in the database (this should happen after db.init_app)
with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(api6_blueprint, url_prefix="/GoogleKse")
app.register_blueprint(api2_blueprint, url_prefix="/BrregUpdate")
app.register_blueprint(api3_blueprint, url_prefix="/KseApi")
app.register_blueprint(api4_blueprint, url_prefix="/SeleniumScrap")
#app.register_blueprint(api5_blueprint, url_prefix="/Kseapi1881")
app.register_blueprint(upload_blueprint, url_prefix="/ExcelHandler")
app.register_blueprint(download_blueprint, url_prefix="/DbToExcel")
app.register_blueprint(email_result_blueprint, url_prefix="/SearchResultHandler")
app.register_blueprint(trigger_webjobs, url_prefix="/trigger_webjobs")

@app.route("/")
def home():
    print(f"Resolved static folder path: {os.path.abspath(app.static_folder)}")
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/health")
def health_check():
    db_connection = None
    if db.session.bind:
        db_connection = db.session.bind.url.database
    return jsonify({
        "status": "OK",
        "db_connection": db_connection
    })



if __name__ == "__main__":
    # Hent portnummer fra miljøvariabelen, eller bruk 8080 som standard
    port = int(os.environ.get("PORT",80))
    app.run(host="0.0.0.0", port=port, debug=True)
