from .similarity import SimilaritySearch

class Chatbot:
    def __init__(self):
        self.search = SimilaritySearch()

    def responder(self, pergunta: str) -> str:
        try:
            resposta = self.search.buscar_resposta(pergunta)
            return resposta
        except Exception:
            return "Desculpe, não encontrei uma resposta para isso."
