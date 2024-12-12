from flask import jsonify

from src.app import app
from src.app.mongo.seed_data import SeedData


class MongoController:
    @staticmethod
    @app.route('/mongo/insert-data', methods=['POST'])
    def mongo_insert_data():
        SeedData()

        return jsonify(), 204

    @staticmethod
    @app.route('/mongo/users', methods=['GET'])
    def mongo_get_users():
        return jsonify(), 200
