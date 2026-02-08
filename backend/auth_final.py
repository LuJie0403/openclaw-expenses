
import os
import pymysql
from dotenv import load_dotenv
from config import settings

# Load environment variables
load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        port=settings.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        print("Successfully connected to the database!")
        conn.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
