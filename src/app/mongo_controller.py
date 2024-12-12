import json
import random

from bson import json_util
from flask import jsonify, request
from datetime import timedelta

from src.app import app
from src.app.config import Config
from src.app.mongo.seed_data import SeedData

CACHE_TIMEOUT = timedelta(seconds=15)
CACHE_KEY_TOP_RATED = "mongo:top_rated_books"
CACHE_KEY_RECOMMENDATIONS = "mongo:recommendations:{}"


class MongoController:
    @staticmethod
    @app.route('/mongo/insert-data', methods=['POST'])
    def mongo_insert_data():
        limite = request.args.get('limite', 10000)
        SeedData(int(limite))

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

    @staticmethod
    @app.route('/mongo/books/recommendations/<user_id>', methods=['GET'])
    def mongo_get_personalized_recommendations(user_id):
        try:
            redis_client = Config.get_redis_client()
            cache_key = CACHE_KEY_RECOMMENDATIONS.format(user_id)
            cached_data = redis_client.get(cache_key)

            if cached_data:
                return jsonify(json.loads(cached_data))

            client = Config.get_mongo_database()
            db = client["book_recommendation"]
            usuarios = db["usuarios"]
            livros = db["livros"]

            user = usuarios.find_one({"_id": user_id})
            
            if not user or not user.get("livros_avaliados"):
                pipeline = [
                    {
                        "$match": {
                            "avaliacoes": {"$exists": True, "$not": {"$size": 0}}
                        }
                    },
                    {
                        "$project": {
                            "titulo": 1,
                            "autor": 1,
                            "genero": 1,
                            "descricao": 1,
                            "rating_medio": {"$avg": "$avaliacoes.nota"},
                            "total_avaliacoes": {"$size": "$avaliacoes"}
                        }
                    },
                    {
                        "$match": {
                            "total_avaliacoes": {"$gte": 3}
                        }
                    },
                    {
                        "$sort": {
                            "rating_medio": -1,
                            "total_avaliacoes": -1
                        }
                    },
                    {"$limit": 10}
                ]
                recommendations = list(livros.aggregate(pipeline))
                recommendation_type = "popular"
            else:
                rated_books = list(livros.find({"_id": {"$in": user["livros_avaliados"]}}))
                user_genres = set()
                
                for book in rated_books:
                    for avaliacao in book["avaliacoes"]:
                        if avaliacao["usuario_id"] == user_id and avaliacao["nota"] >= 4:
                            user_genres.add(book["genero"])
                            break

                if not user_genres:
                    user_genres = set([random.choice(["Fantasia", "Ficção Científica", "Romance", "Aventura", "Mistério", "História"])])

                pipeline = [
                    {
                        "$match": {
                            "genero": {"$in": list(user_genres)},
                            "_id": {"$nin": user["livros_avaliados"]},
                            "avaliacoes": {"$exists": True, "$not": {"$size": 0}}
                        }
                    },
                    {
                        "$project": {
                            "titulo": 1,
                            "autor": 1,
                            "genero": 1,
                            "descricao": 1,
                            "rating_medio": {"$avg": "$avaliacoes.nota"},
                            "total_avaliacoes": {"$size": "$avaliacoes"}
                        }
                    },
                    {
                        "$match": {
                            "rating_medio": {"$gte": 4}
                        }
                    },
                    {
                        "$sort": {
                            "rating_medio": -1,
                            "total_avaliacoes": -1
                        }
                    },
                    {"$limit": 10}
                ]
                recommendations = list(livros.aggregate(pipeline))
                recommendation_type = "personalized"

            response_data = {
                "type": recommendation_type,
                "recommendations": json.loads(json_util.dumps(recommendations)),
                "count": len(recommendations)
            }

            redis_client.setex(
                cache_key,
                CACHE_TIMEOUT,
                json.dumps(response_data)
            )

            return jsonify(response_data)

        except Exception as e:
            return jsonify(error=f"Erro ao gerar recomendações: {str(e)}"), 500
