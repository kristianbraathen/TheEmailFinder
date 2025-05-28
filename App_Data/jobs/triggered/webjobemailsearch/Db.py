import os
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2 import sql

# Initialiser SQLAlchemy
db = SQLAlchemy()

def get_database_uri():
    """Bygger en database-URI med vanlig bruker/pass-tilkobling."""
    user = "appbruker"  # Bruker du opprettet
    password = "SterktPassord123"  # Passordet for brukeren
    host = "theemailfinderserver.postgres.database.azure.com"
    database = "theemailfinder_database"
    
    # Bygg URI for tilkobling
    return f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"

def get_db_connection():
    """Oppretter en psycopg2-forbindelse med database-URI."""
    try:
        conn = psycopg2.connect(get_database_uri())
        return conn
    except psycopg2.Error as e:
        print(f"Feil ved tilkobling til databasen: {e}")
        raise
