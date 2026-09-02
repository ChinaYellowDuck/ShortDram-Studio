"""Create the shortdram database if it doesn't exist."""
import psycopg2
from psycopg2 import sql

from app.config import settings


def create_database():
    """Create shortdram database on the PostgreSQL server."""
    # Connect to default database to create our target database
    # Parse the database URL to extract connection params
    import re

    # postgresql+psycopg2://user:password@host:port/dbname
    match = re.match(
        r"postgresql\+psycopg2://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)",
        settings.DATABASE_URL,
    )
    if not match:
        raise ValueError("Could not parse DATABASE_URL")

    user, password, host, port, dbname = match.groups()

    # Connect to default postgres database
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        dbname="postgres",
        autocommit=True,
    )

    try:
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print(f"Database '{dbname}' created successfully.")
        else:
            print(f"Database '{dbname}' already exists.")

        cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
