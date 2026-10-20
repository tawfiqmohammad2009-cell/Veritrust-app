import os
import urllib.parse as urlparse
import pg8000.dbapi

# Grab the DATABASE_URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL is not set. Run: export DATABASE_URL='your_connection_string'")
    exit(1)

print("Parsing database URL...")
url = urlparse.urlparse(DATABASE_URL)
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port or 5432

print(f"Connecting to PostgreSQL at {host}:{port}...")
try:
    # Connect using pg8000 (pure Python)
    conn = pg8000.dbapi.connect(
        database=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cursor = conn.cursor()
    
    print("Reading schema.sql...")
    with open("schema.sql", "r") as f:
        schema_sql = f.read()
        
    print("Executing database schema...")
    cursor.execute(schema_sql)
    conn.commit()
    
    cursor.close()
    conn.close()
    print("✅ Success! All database tables created successfully.")

except Exception as e:
    print(f"❌ An error occurred: {e}")

