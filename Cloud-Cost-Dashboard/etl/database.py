import psycopg

from common.logger import logger
from config.settings import DB_CONFIG


def get_connection():
    """
    Create and return a PostgreSQL connection.
    """

    try:
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )

        logger.info(
            "Connected to PostgreSQL (%s:%s)",
            DB_CONFIG["host"],
            DB_CONFIG["port"],
        )

        return conn

    except Exception as ex:

        logger.exception("Failed to connect to PostgreSQL")

        raise Exception(
            f"Failed to connect to PostgreSQL: {ex}"
        )