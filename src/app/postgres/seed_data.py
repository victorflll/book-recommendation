import random

from faker import Faker

from src.app.config import Config


class SeedData:
    def __init__(self, limite=10000):
        fake = Faker()

        try:
            conn = Config.get_postgres_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM avaliacoes;")
            cur.execute("DELETE FROM usuarios;")
            cur.execute("DELETE FROM livros;")

            for _ in range(limite):
                email = fake.email()

                cur.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s;", (email,))
                count = cur.fetchone()[0]

                if count == 0:
                    cur.execute(
                        "INSERT INTO usuarios (nome, email, preferencias) VALUES (%s, %s, %s)",
                        (fake.name(), email, fake.word())
                    )

            for _ in range(limite):
                cur.execute(
                    "INSERT INTO livros (titulo, autor, genero, descricao) VALUES (%s, %s, %s, %s)",
                    (fake.sentence(), fake.name(), fake.word(), fake.text())
                )

            for _ in range(limite / 2):
                cur.execute("SELECT id FROM usuarios ORDER BY RANDOM() LIMIT 1;")
                usuario_id = cur.fetchone()[0]
                cur.execute("SELECT id FROM livros ORDER BY RANDOM() LIMIT 1;")
                livro_id = cur.fetchone()[0]

                nota = random.randint(1, 5)

                cur.execute(
                    "INSERT INTO avaliacoes (usuario_id, livro_id, nota, comentario) VALUES (%s, %s, %s, %s)",
                    (usuario_id, livro_id, nota, fake.text())
                )

            conn.commit()

            print("Dados inseridos com sucesso!")

        except Exception as e:
            print(f"Erro ao inserir dados: {e}")

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
