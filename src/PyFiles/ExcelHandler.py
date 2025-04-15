import time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import openpyxl
import traceback
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from .Db import db

# Initialize the declarative base
Base = declarative_base()
upload_blueprint = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def create_dynamic_model(table_name, headers):
    """
    Create a SQLAlchemy model dynamically based on the headers from the Excel file.
    """
    # Use db's engine to inspect the tables
    engine = db.engine  # Use db from the app context
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    
    # Check if the table already exists; do not drop if it already exists.
    if table_name in inspector.get_table_names():
        table = Table(table_name, metadata, autoload_with=engine, extend_existing=True)
    else:
        # Create columns dynamically based on headers
        columns = {
            '__tablename__': table_name,
            'id': Column(Integer, primary_key=True, autoincrement=True),  # Auto-generated primary key
        }
        for header in headers:
            # Add columns dynamically based on the header names
            columns[header] = Column(String(255), nullable=True)

        # Create and return a dynamic model class
        return type(table_name, (db.Model,), columns)

@upload_blueprint.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or invalid file type'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(file_path)

    try:
        # Load the Excel file
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        # Extract headers
        headers = [str(cell.value).strip() if cell.value else f"Column_{i}" for i, cell in enumerate(sheet[1], start=1)]
        # Exclude headers that start with "Column"
        headers = [header for header in headers if not header.startswith("Column")]

        # Create a dynamic model
        table_name = 'imported_table'
        DynamicModel = create_dynamic_model(table_name, headers)

        # Connect to the database and create the table
        db.create_all()  # Create the table using db.create_all()

        # Insert data into the table
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
            row_data = {headers[i]: row[i] for i in range(len(headers))}
            instance = DynamicModel(**row_data)
            db.session.add(instance)

        db.session.commit()

        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({'success': True, 'table_name': table_name})

    except Exception as e:
        print(f'Error processing file: {e}')
        traceback.print_exc()
        return jsonify({'error': 'Failed to process the Excel file'}), 500
