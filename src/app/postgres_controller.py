from flask import jsonify, request
from psycopg2.extras import RealDictCursor
import json
from datetime import timedelta

from src.app import app
from src.app.config import Config
from src.app.postgres.seed_data import SeedData
from src.app.postgres.setup_db import SetupDB


CACHE_TIMEOUT = timedelta(seconds=15)
CACHE_KEY_TOP_RATED = "postgres:top_rated_books"
CACHE_KEY_RECOMMENDATIONS = "postgres:recommendations:{}"


class PostgresController:
    @staticmethod
    @app.before_request
    def create_tables():
        SetupDB().setup_database()

    @staticmethod
    @app.route('/postgres/insert-data', methods=['POST'])
    def postgres_insert_data():
        limite = request.args.get('limite', 10000)
        SeedData(int(limite))

        return jsonify(), 204

    @staticmethod
    @app.route('/postgres/users', methods=['GET'])
    def postgres_get_users():
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

    @staticmethod
    @app.route('/postgres/books', methods=['GET'])
    def postgres_search_books():
        try:
            conn = Config.get_postgres_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    l.*,
                    COALESCE(AVG(a.nota), 0) as media_avaliacoes,
                    COUNT(a.id) as total_avaliacoes
                FROM livros l
                LEFT JOIN avaliacoes a ON l.id = a.livro_id
                GROUP BY l.id
                ORDER BY l.titulo;
            """
            
            cur.execute(query)
            books = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return jsonify(data=books)
        except Exception as e:
            return jsonify(error=f"Erro ao buscar livros: {str(e)}"), 500

    @staticmethod
    @app.route('/postgres/books/top-rated', methods=['GET'])
    def postgres_get_top_rated_books():
        try:
            redis_client = Config.get_redis_client()
            cached_data = redis_client.get(CACHE_KEY_TOP_RATED)
            
            if cached_data:
                return jsonify(data=json.loads(cached_data))

            conn = Config.get_postgres_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    l.*,
                    COALESCE(AVG(a.nota)::float, 0.0) as media_avaliacoes,
                    COUNT(a.id) as total_avaliacoes
                FROM livros l
                LEFT JOIN avaliacoes a ON l.id = a.livro_id
                GROUP BY l.id
                HAVING COUNT(a.id) > 0
                ORDER BY media_avaliacoes DESC, total_avaliacoes DESC;
            """
            
            cur.execute(query)
            top_books = cur.fetchall()
            
            cur.close()
            conn.close()
            
            redis_client.setex(
                CACHE_KEY_TOP_RATED,
                CACHE_TIMEOUT,
                json.dumps(top_books)
            )
            
            return jsonify(data=top_books)
        except Exception as e:
            return jsonify(error=f"Erro ao buscar livros mais bem avaliados: {str(e)}"), 500

    @staticmethod
    @app.route('/postgres/books/recommendations/<int:user_id>', methods=['GET'])
    def postgres_get_personalized_recommendations(user_id):
        try:
            redis_client = Config.get_redis_client()
            cache_key = CACHE_KEY_RECOMMENDATIONS.format(user_id)
            cached_data = redis_client.get(cache_key)

            if cached_data:
                return jsonify(json.loads(cached_data))

            conn = Config.get_postgres_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT livro_id, nota 
                FROM avaliacoes 
                WHERE usuario_id = %s;
            """, (user_id,))
            user_ratings = cur.fetchall()

            if not user_ratings:
                cur.execute("""
                    SELECT l.*, ROUND(AVG(a.nota), 2) as rating_medio, COUNT(a.id) as total_avaliacoes
                    FROM livros l
                    LEFT JOIN avaliacoes a ON l.id = a.livro_id
                    GROUP BY l.id
                    HAVING COUNT(a.id) >= 3
                    ORDER BY rating_medio DESC, total_avaliacoes DESC
                    LIMIT 10;
                """)
                recommendations = cur.fetchall()
                recommendation_type = "popular"
            else:
                cur.execute("""
                    WITH user_genres AS (
                        SELECT DISTINCT l.genero
                        FROM avaliacoes a
                        JOIN livros l ON a.livro_id = l.id
                        WHERE a.usuario_id = %s AND a.nota >= 4
                    )
                    SELECT DISTINCT l.*, 
                           ROUND(AVG(a.nota) OVER (PARTITION BY l.id), 2) as rating_medio,
                           COUNT(a.id) OVER (PARTITION BY l.id) as total_avaliacoes
                    FROM livros l
                    JOIN avaliacoes a ON l.id = a.livro_id
                    WHERE l.genero IN (SELECT genero FROM user_genres)
                    AND l.id NOT IN (
                        SELECT livro_id FROM avaliacoes WHERE usuario_id = %s
                    )
                    AND a.nota >= 4
                    ORDER BY rating_medio DESC, total_avaliacoes DESC
                    LIMIT 10;
                """, (user_id, user_id))
                recommendations = cur.fetchall()
                recommendation_type = "personalized"

            cur.close()
            conn.close()

            response_data = {
                "type": recommendation_type,
                "recommendations": recommendations,
                "count": len(recommendations)
            }

            redis_client.setex(
                cache_key,
                CACHE_TIMEOUT,
                json.dumps(response_data, default=str)
            )

            return jsonify(response_data)
        except Exception as e:
            return jsonify(error=f"Erro ao gerar recomendações: {str(e)}"), 500