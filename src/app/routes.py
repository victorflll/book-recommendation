from flask import jsonify

from src.app import app


class AppController:
    @staticmethod
    @app.route('/')
    def index():
        return jsonify(message='Hello World!')