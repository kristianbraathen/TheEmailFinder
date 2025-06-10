import psycopg2

def get_database_uri():
    user = "appbruker"
    password = "SterktPassord123"
    host = "theemailfinderserver.postgres.database.azure.com"
    database = "theemailfinder_database"
    return f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"

try:
    conn = psycopg2.connect(get_database_uri())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM email_results")
    count = cursor.fetchone()[0]
    print(f"Number of entries in email_results table: {count}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close() 