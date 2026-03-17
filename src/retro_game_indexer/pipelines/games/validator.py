"""Validate and normalize detected game entities against known titles."""

from difflib import SequenceMatcher

from retro_game_indexer.shared.datasets import load_dataset


class GameValidator:
    """Validate game detections using fuzzy matching against known titles.

    Compares each candidate entity from the detector against a dataset
    of known game titles. Exact matches are confirmed immediately;
    close matches are confirmed with an adjusted confidence score;
    unknown entities are kept but marked as unvalidated.

    Attributes:
        known: Dict mapping lowercased title to canonical form.
        similarity_threshold: Minimum fuzzy match ratio (0.0-1.0).
    """

    def __init__(
        self,
        known_titles: list[str] | None = None,
        similarity_threshold: float = 0.8,
    ) -> None:
        """Initialize GameValidator.

        Args:
            known_titles: Override list of known game titles.
                Defaults to loading from ``data/datasets/games/known_titles.json``.
            similarity_threshold: Minimum SequenceMatcher ratio to
                consider a fuzzy match valid.
        """
        titles = known_titles or load_dataset("games", "known_titles")
        self.known: dict[str, str] = {t.lower(): t for t in titles}
        self.similarity_threshold = similarity_threshold

    def _best_match(self, name: str) -> tuple[str, float]:
        """Find the best matching known title for a candidate name.

        Args:
            name: Lowercased candidate entity name.

        Returns:
            Tuple of (canonical_name, similarity_score). Returns
            ("", 0.0) if no known titles exist.
        """
        best_title = ""
        best_score = 0.0
        for key, canonical in self.known.items():
            score = SequenceMatcher(None, name, key).ratio()
            if score > best_score:
                best_score = score
                best_title = canonical
        return best_title, best_score

    def validate(self, candidates: list[dict]) -> list[dict]:
        """Validate and normalize candidate game entities.

        Args:
            candidates: Raw detector output.

        Returns:
            Validated entities with "validated" key added.
        """
        results: list[dict] = []
        for c in candidates:
            entry = dict(c)
            key = entry["name"].lower()

            # Exact match → confirmed with canonical name
            if key in self.known:
                entry["name"] = self.known[key]
                entry["validated"] = True
                results.append(entry)
                continue

            # Fuzzy match → confirmed with adjusted score
            best_title, score = self._best_match(key)
            if score >= self.similarity_threshold:
                entry["name"] = best_title
                entry["confidence"] = entry["confidence"] * score
                entry["validated"] = True
                results.append(entry)
                continue

            # No match → keep but mark uncertain
            entry["validated"] = False
            results.append(entry)

        return results
