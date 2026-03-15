"""Detect maintenance items in text segments using GLiNER NER."""

from gliner import GLiNER

from retro_game_indexer.pipelines.maintenance.filters import STOPWORDS

_model: GLiNER | None = None


def _get_model() -> GLiNER:
    """Get or create a cached GLiNER model instance.

    Returns:
        Cached GLiNER model instance.
    """
    global _model
    if _model is None:
        _model = GLiNER.from_pretrained("urchade/gliner_base")
    return _model


class MaintenanceDetector:
    """Detect maintenance items in text using GLiNER NER model.

    Detects repair tools, electronic components, and hardware
    modifications mentioned in transcribed speech.
    """

    def __init__(
        self,
        threshold: float = 0.6,
        blocklist: set[str] | None = None,
        aliases: dict[str, str] | None = None,
    ) -> None:
        """Initialize MaintenanceDetector.

        Args:
            threshold: Minimum confidence score for detection (0.0-1.0).
            blocklist: Extra terms to reject (lowercased, added to stopwords).
            aliases: Map variant spellings (lowercased) to canonical names.
        """
        self.model = _get_model()
        self.threshold = threshold
        self.labels = [
            "repair tool",
            "electronic component",
            "hardware modification",
        ]
        self.blocklist = blocklist or set()
        self.aliases = aliases or {}

    def _is_valid(self, name: str) -> bool:
        """Check if a detected name is a valid maintenance item.

        Args:
            name: Detected entity name.

        Returns:
            True if valid, False if in stopwords/blocklist or too short.
        """
        key = name.lower().strip()
        if key in STOPWORDS or key in self.blocklist:
            return False
        return len(key) >= 3

    def detect(self, segments: list[dict]) -> list[dict]:
        """Detect maintenance mentions in transcript segments.

        Args:
            segments: List of dicts with "text" and "start" keys.

        Returns:
            List of unique mentions with "name", "category",
            "timestamp", and "confidence" keys.
        """
        mentions: list[dict] = []
        seen: set[str] = set()

        for seg in segments:
            entities = self.model.predict_entities(
                seg["text"], self.labels, threshold=self.threshold
            )
            for ent in entities:
                name = ent["text"]
                key = name.lower()
                if not self._is_valid(name):
                    continue
                canonical = self.aliases.get(key, name)
                dedup_key = canonical.lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                mentions.append(
                    {
                        "name": canonical,
                        "category": ent["label"],
                        "timestamp": seg["start"],
                        "confidence": float(ent["score"]),
                    }
                )

        return mentions
