import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
try:
    connection = psycopg2.connect(DATABASE_URL)
    print("✅ Connection successful!")
    connection.close()
except Exception as e:
    print("❌ Connection failed:")
    print(e)