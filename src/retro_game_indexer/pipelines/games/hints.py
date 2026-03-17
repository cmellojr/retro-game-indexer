"""Default transcription hints for common game titles."""

from retro_game_indexer.shared.datasets import load_dataset

_FALLBACK_HINTS: str = (
    "Super Mario World, Yoshi's Island, Yoshi, Castlevania, Bloodlines, "
    "Mega Man X, Mega Man, Chrono Trigger, Final Fantasy VI, Live A Live, "
    "The Legend of Zelda, A Link to the Past, Super Metroid, Metroid, "
    "Donkey Kong Country, Star Fox, Stunt Race FX, Super Mario Kart, "
    "Super Punch-Out, Pilot Wings, Super Mario RPG, F-Zero"
)

_hints_data = load_dataset("games", "hints")
DEFAULT_HINTS: str = ", ".join(_hints_data) if _hints_data else _FALLBACK_HINTS
