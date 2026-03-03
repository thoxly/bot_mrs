import os

import psycopg2
from dotenv import load_dotenv


def main() -> None:
    # Load environment variables from .env (if present)
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is not set")
        return

    try:
        # Connect using the same URL as the main app
        connection = psycopg2.connect(database_url)
        print("Connection successful!")

        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Current time:", result)

        cursor.close()
        connection.close()
        print("Connection closed.")
    except Exception as e:
        print(f"Failed to connect: {e}")


if __name__ == "__main__":
    main()

