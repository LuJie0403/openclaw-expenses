
from fastapi import FastAPI
import pymysql
import os
from dotenv import load_dotenv
from config import settings

load_dotenv()

app = FastAPI()

def get_db_connection():
    return pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        port=settings.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
