from flask import jsonify

from src.app import app
from src.app.config import Config


class MongoController:
    @staticmethod
    def create_documents():
        return None

    @staticmethod
    @app.route('/mongo/insert-data', methods=['POST'])
    def insert_data():
        return jsonify(), 204

    @staticmethod
    @app.route('/mongo/users', methods=['GET'])
    def get_users():
        return jsonify(), 200
