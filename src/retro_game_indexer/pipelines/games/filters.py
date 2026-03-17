"""Stopwords and console names to filter from game detection."""

from retro_game_indexer.shared.datasets import load_dataset

_FALLBACK_STOPWORDS: set[str] = {
    "jogo", "jogos", "game", "games",
    "rpg", "rpgs", "super", "power up",
    "galera", "pessoal", "gente",
    "luta", "luta de box", "jogo de box",
    "jogos de corrida", "jogos de corrida de kart",
    "carrinho", "carrinho de mineração",
    "rotacionam",
}

_FALLBACK_CONSOLES: set[str] = {
    "super nintendo", "snes", "super famicom",
    "mega drive", "genesis", "sega genesis",
    "nes", "famicom", "nintendo",
    "playstation", "ps1", "ps2", "ps3", "ps4", "ps5",
    "xbox", "game boy", "gameboy",
    "nintendo 64", "n64", "gamecube", "wii", "switch",
}

_stopwords_data = load_dataset("games", "stopwords")
STOPWORDS: set[str] = set(_stopwords_data) if _stopwords_data else _FALLBACK_STOPWORDS

_consoles_data = load_dataset("games", "consoles")
CONSOLES: set[str] = set(_consoles_data) if _consoles_data else _FALLBACK_CONSOLES
