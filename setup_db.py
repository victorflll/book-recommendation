import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Função para conectar ao banco de dados."""
    return psycopg2.connect(
        dbname="book-recommendation",
        user="admin",
        password="admin",
        host="localhost", 
        port=5432
    )

def setup_database():
    """Criação das tabelas do banco de dados."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            preferencias VARCHAR(100)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            autor VARCHAR(100),
            genero VARCHAR(100),
            descricao TEXT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
            livro_id INT REFERENCES livros(id) ON DELETE CASCADE,
            nota INT CHECK(nota >= 1 AND nota <= 5),
            comentario TEXT
        );
        """)

        conn.commit()
        print("Tabelas criadas com sucesso!")

    except Exception as e:
        print(f"Erro ao configurar o banco de dados: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
