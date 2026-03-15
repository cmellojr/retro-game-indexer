"""Stopwords and console names to filter from game detection."""

STOPWORDS: set[str] = {
    "jogo", "jogos", "game", "games",
    "rpg", "rpgs", "super", "power up",
    "galera", "pessoal", "gente",
    "luta", "luta de box", "jogo de box",
    "jogos de corrida", "jogos de corrida de kart",
    "carrinho", "carrinho de mineração",
    "rotacionam",
}

CONSOLES: set[str] = {
    "super nintendo", "snes", "super famicom",
    "mega drive", "genesis", "sega genesis",
    "nes", "famicom", "nintendo",
    "playstation", "ps1", "ps2", "ps3", "ps4", "ps5",
    "xbox", "game boy", "gameboy",
    "nintendo 64", "n64", "gamecube", "wii", "switch",
}
