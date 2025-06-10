import os
from sqlalchemy import create_engine, text

# Set the connection string
os.environ['DATABASE_CONNECTION_STRING'] = "postgresql://appbruker:SterktPassord123@theemailfinderserver.postgres.database.azure.com:5432/theemailfinder_database?sslmode=require"

# Create engine
engine = create_engine(os.environ['DATABASE_CONNECTION_STRING'])

# Add the column
with engine.connect() as connection:
    connection.execute(text('ALTER TABLE imported_table ADD COLUMN IF NOT EXISTS ischecked BOOLEAN DEFAULT FALSE'))
    connection.commit()
    print("Successfully added isChecked column to imported_table") 