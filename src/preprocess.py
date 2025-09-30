import re
import unicodedata

def limpar_texto(texto: str) -> str:
    """
    Remove acentos, caracteres especiais e deixa tudo minúsculo.
    """
    # Remove acentos
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    # Deixa minúsculo e remove caracteres especiais
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    return texto.lower().strip()
