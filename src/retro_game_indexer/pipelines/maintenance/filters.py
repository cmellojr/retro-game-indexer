"""Stopwords to filter from maintenance detection."""

from retro_game_indexer.shared.datasets import load_dataset

_FALLBACK_STOPWORDS: set[str] = {
    "coisa", "negócio", "parte", "pedaço", "lado",
    "problema", "defeito", "erro", "teste",
    "vídeo", "canal", "galera", "pessoal", "gente",
    "cara", "aqui", "isso", "esse", "essa",
    "tipo", "forma", "jeito", "ponto",
}

_stopwords_data = load_dataset("maintenance", "stopwords")
STOPWORDS: set[str] = set(_stopwords_data) if _stopwords_data else _FALLBACK_STOPWORDS
