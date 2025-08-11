from psycopg2 import connect, sql
from dotenv import load_dotenv
import os
load_dotenv()

def create_tables(conn, query):
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        



if __name__ == "__main__":
    # Load environment variables
    with connect(
        dbname=os.getenv('POSTGRES_DB', 'default_db'),
        user=os.getenv('POSTGRES_USER', 'default_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'default_password'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432)
    ) as conn:
    # SQL query to create tables
        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Create tables
        create_tables(conn, create_users_table_query)

        create_user_activity_table_query = """
        CREATE TABLE IF NOT EXISTS user_activity (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            prompt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Create user activity table
        create_tables(conn, create_user_activity_table_query)