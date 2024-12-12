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
    def postgres_insert_data(limite: int = 10000):
        SeedData(limite)

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
                HAVING COUNT(a.id) > 0
                ORDER BY media_avaliacoes DESC, total_avaliacoes DESC;
            """
            
            cur.execute(query)
            top_books = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return jsonify(data=top_books)
        except Exception as e:
            return jsonify(error=f"Erro ao buscar livros mais bem avaliados: {str(e)}"), 500