import os

import psycopg2
from pymongo import MongoClient


class Config:
    @staticmethod
    def get_postgres_connection():
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'book-recommendation'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', 'admin'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        return conn

    @staticmethod
    def get_mongo_database():
        user = os.getenv("MONGO_USER", 'admin')
        pwd = os.getenv("MONGO_PASSWORD", 'admin')
        host = os.getenv("MONGO_HOST", 'localhost')
        port = os.getenv("MONGO_PORT", '27017')

        mongo_uri = f"mongodb://{user}:{pwd}@{host}:{port}"
        client =  MongoClient(mongo_uri)

        return client