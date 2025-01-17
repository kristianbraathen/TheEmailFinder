from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import urllib.parse
import Db from db

app = Flask(__name__)

# CORS Configuration
CORS(app, origins=["http://localhost:8080, http://emailfinder-h0g7f5hpa4eggcbb.norwayeast-01.azurewebsites.net"])

# Database Configuration (For PostgreSQL)
# Get the connection string from the environment variable
connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")  # The Azure PostgreSQL connection string

# Set up SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
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
    app.run(host="0.0.0.0", port=80)
