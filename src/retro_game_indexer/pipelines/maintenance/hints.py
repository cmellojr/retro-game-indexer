"""Default transcription hints for retro hardware maintenance terms."""

from retro_game_indexer.shared.datasets import load_dataset

_FALLBACK_HINTS: str = (
    "capacitor, resistor, transistor, diodo, LED, "
    "ferro de solda, solda, estanho, flux, multímetro, "
    "osciloscópio, fonte de alimentação, regulador de tensão, "
    "mod RGB, recap, retrobrighting, shell swap, "
    "placa mãe, trilha, via, curto circuito, "
    "cartucho, conector, flat cable, CI, chip, "
    "troca de capacitor, limpeza, álcool isopropílico, "
    "chave torx, chave gamebit, dessoldar, refluxo"
)

_hints_data = load_dataset("maintenance", "hints")
DEFAULT_HINTS: str = ", ".join(_hints_data) if _hints_data else _FALLBACK_HINTS
