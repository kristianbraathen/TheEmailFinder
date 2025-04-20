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

Base = declarative_base()
upload_blueprint = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def create_dynamic_model(table_name, headers):
    """
    Create a SQLAlchemy model dynamically based on the headers from the Excel file.
    """
    engine = db.engine  # Use db from the app context
    metadata = MetaData()
    metadata.bind = engine
    
    # Check if the table already exists
    inspector = inspect(engine)
    
    # If the table doesn't exist, create it
    if table_name not in inspector.get_table_names():
        # Dynamically create columns based on the headers
        columns = {
            '__tablename__': table_name,
            'id': Column(Integer, primary_key=True, autoincrement=True),  # Auto-generated primary key
        }
        for header in headers:
            if header:  # Ensure header is not empty
                columns[header] = Column(String(255), nullable=True)

        # Create a dynamic model class
        DynamicModel = type(table_name, (db.Model,), columns)

        # Create the table in the database
        DynamicModel.__table__.create(bind=engine)
        
        return DynamicModel
    else:
        # If the table exists, just return the model that is mapped to it
        table = Table(table_name, metadata, autoload_with=engine)
        return type(table_name, (db.Model,), {'__table__': table})

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
        headers = [
            str(cell.value).strip().lower().replace('.', '_') 
            if cell.value else f"column_{i}" 
            for i, cell in enumerate(sheet[1], start=1)
        ]

        
        # Exclude headers that start with "Column"
        headers = [header for header in headers if not header.startswith("Column")]

        # Create a dynamic model
        table_name = 'imported_table'
        DynamicModel = create_dynamic_model(table_name, headers)

        # Insert data into the table
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
            row_data = {headers[i]: row[i] for i in range(len(headers))}
            
            # Filter out None or empty values
            row_data = {key: value for key, value in row_data.items() if value is not None and value != ""}
            
            # Dynamically create an instance and add to session
            try:
                instance = DynamicModel(**row_data)
                db.session.add(instance)
            except Exception as e:
                print(f"Error adding row data: {e}")
                traceback.print_exc()
        
        # Commit the session
        db.session.commit()

        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({'success': True, 'table_name': table_name})

    except Exception as e:
        print(f'Error processing file: {e}')
        traceback.print_exc()
        return jsonify({'error': 'Failed to process the Excel file'}), 500
