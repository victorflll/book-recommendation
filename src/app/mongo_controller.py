import json

from bson import json_util
from flask import jsonify
from datetime import timedelta

from src.app import app
from src.app.config import Config
from src.app.mongo.seed_data import SeedData

CACHE_TIMEOUT = timedelta(seconds=15)
CACHE_KEY_TOP_RATED = "mongo:top_rated_books"


class MongoController:
    @staticmethod
    @app.route('/mongo/insert-data', methods=['POST'])
    def mongo_insert_data(limite: int = 10000):
        SeedData(limite)

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
    @app.route('/mongo/books/top-rated', methods=['GET'])
    def mongo_get_top_rated_books():
        try:
            redis_client = Config.get_redis_client()
            cached_data = redis_client.get(CACHE_KEY_TOP_RATED)
            
            if cached_data:
                return jsonify(data=json.loads(cached_data))

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
                {"$sort": {"media_avaliacoes": -1, "total_avaliacoes": -1}}
            ]
        
            result = json.loads(json_util.dumps(livros.aggregate(pipeline)))
            
            redis_client.setex(
                CACHE_KEY_TOP_RATED,
                CACHE_TIMEOUT,
                json.dumps(result)
            )
            
            return jsonify(data=result)
        except Exception as e:
            return jsonify(error=f"Erro ao buscar livros mais bem avaliados: {str(e)}"), 500
