import json

from bson import json_util
from flask import jsonify

from src.app import app
from src.app.config import Config
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
        client = Config.get_mongo_database()
        db = client["book_recommendation"]
        usuarios = db["usuarios"]
        result = json.loads(json_util.dumps(usuarios.find()))

        return jsonify(data=result, length=len(result))

    @staticmethod
    @app.route('/mongo/books', methods=['GET'])
    def mongo_get_books():
        client = Config.get_mongo_database()
        db = client["book_recommendation"]
        livros = db["livros"]
        result = json.loads(json_util.dumps(livros.find()))

        return jsonify(data=result, length=len(result))

    @staticmethod
    @app.route('/mongo/top-rated-books', methods=['GET'])
    def mongo_get_top_rated_books():
        client = Config.get_mongo_database()
        db = client["book_recommendation"]
        livros = db["livros"]
        
        pipeline = [
            {
                "$addFields": {
                    "media_avaliacoes": {
                        "$cond": [
                            {"$eq": [{"$size": "$avaliacoes"}, 0]},
                            0,
                            {"$avg": "$avaliacoes.nota"}
                        ]
                    },
                    "total_avaliacoes": {"$size": "$avaliacoes"}
                }
            },
            {"$sort": {"media_avaliacoes": -1, "total_avaliacoes": -1}},
            {"$limit": 5000}
        ]
        
        result = json.loads(json_util.dumps(livros.aggregate(pipeline)))
        return jsonify(data=result)
