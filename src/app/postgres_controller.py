from operator import length_hint

from flask import jsonify
from psycopg2.extras import RealDictCursor

from src.app import app
from src.app.config import Config
from src.app.postgres.seed_data import SeedData
from src.app.postgres.setup_db import SetupDB


class PostgresController:
    @staticmethod
    @app.before_request
    def create_tables():
        SetupDB().setup_database()

    @staticmethod
    @app.route('/postgres/insert-data', methods=['POST'])
    def insert_data():
        SeedData()

        return jsonify(), 204

    @staticmethod
    @app.route('/postgres/users', methods=['GET'])
    def get_users():
        try:
            conn = Config.get_postgres_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT * FROM usuarios;")
            users = cur.fetchall()

            cur.close()
            conn.close()

            return jsonify(data=users, length=len(users))
        except Exception as e:
            return jsonify(error=f"Erro ao conectar ao banco de dados: {str(e)}"), 500