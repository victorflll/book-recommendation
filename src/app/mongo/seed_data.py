import random

from faker import Faker

from src.app.config import Config


class SeedData:
    def __init__(self):
        client = Config.get_mongo_database()
        db = client["book_recommendation"]
        usuarios = db["usuarios"]
        livros = db["livros"]

        usuarios.delete_many({})
        livros.delete_many({})

        fake = Faker()

        def criar_usuario():
            usuario = {
                "_id": fake.uuid4(),
                "nome": fake.name(),
                "email": fake.email(),
                "preferencias": [random.choice(["ficção", "aventura", "romance", "mistério", "história", "biografia"])
                                 for _ in range(random.randint(1, 3))],
                "livros_avaliados": []
            }
            return usuario

        def criar_livro():
            livro = {
                "_id": fake.uuid4(),
                "titulo": fake.sentence(nb_words=5),
                "autor": fake.name(),
                "genero": random.choice(
                    ["Fantasia", "Ficção Científica", "Romance", "Aventura", "Mistério", "História"]),
                "descricao": fake.paragraph(nb_sentences=3),
                "avaliacoes": []
            }
            return livro

        def criar_avaliacao(usuario_id, livro_id):
            avaliacao = {
                "usuario_id": usuario_id,
                "nota": random.randint(1, 5),
                "comentario": fake.sentence(nb_words=10)
            }
            livros.update_one(
                {"_id": livro_id},
                {"$push": {"avaliacoes": avaliacao}}
            )
            usuarios.update_one(
                {"_id": usuario_id},
                {"$push": {"livros_avaliados": livro_id}}
            )

        for _ in range(10000):
            usuario = criar_usuario()
            usuarios.insert_one(usuario)

        for _ in range(10000):
            livro = criar_livro()
            livros.insert_one(livro)

        total_avaliacoes = 0
        todos_usuarios = list(usuarios.find())
        todos_livros = list(livros.find())
        
        while total_avaliacoes < 5000:
            usuario = random.choice(todos_usuarios)
            livro = random.choice(todos_livros)

            if livro["_id"] not in usuario["livros_avaliados"]:
                criar_avaliacao(usuario["_id"], livro["_id"])
                total_avaliacoes += 1
