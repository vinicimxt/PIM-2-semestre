import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .preprocess import limpar_texto

class SimilaritySearch:
    def __init__(self, caminho_base="data/faq.json"):
        with open(caminho_base, "r", encoding="utf-8") as f:
            self.base = json.load(f)

        # Pré-processar perguntas
        self.perguntas = [limpar_texto(item["pergunta"]) for item in self.base]

        # Vetorização TF-IDF
        self.vectorizer = TfidfVectorizer()
        self.matriz = self.vectorizer.fit_transform(self.perguntas)

    def buscar_resposta(self, pergunta_usuario: str):
        pergunta_proc = limpar_texto(pergunta_usuario)
        vetor_usuario = self.vectorizer.transform([pergunta_proc])

        similaridades = cosine_similarity(vetor_usuario, self.matriz)
        indice_mais_proximo = similaridades.argmax()

        return self.base[indice_mais_proximo]["resposta"]
