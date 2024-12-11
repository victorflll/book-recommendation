from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'book-recommendation'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432))
    )
    return conn

#rota para testar o banco de dados
@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM usuarios LIMIT 5;")
        users = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(users=users)
    except Exception as e:
        return jsonify(error=f"Erro ao conectar ao banco de dados: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
