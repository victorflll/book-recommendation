import os

import psycopg2


class Config:
    @staticmethod
    def get_db_connection():
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'book-recommendation'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', 'admin'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        return conn