from datetime import date, timedelta
import os

from dotenv import load_dotenv

load_dotenv()

# PostgreSQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TODAY = date.today()

# START_DATE = "2025-08-01"
# END_DATE = "2026-09-24"

START_DATE = (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")
