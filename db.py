import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )