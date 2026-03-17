"""Validate and normalize detected maintenance entities against known terms."""

from difflib import SequenceMatcher

from retro_game_indexer.shared.datasets import load_dataset


class MaintenanceValidator:
    """Validate maintenance detections using fuzzy matching against known terms.

    Compares each candidate entity from the detector against a dataset
    of known maintenance tools, components, and techniques. Exact matches
    are confirmed immediately; close matches are confirmed with an adjusted
    confidence score; unknown entities are kept but marked as unvalidated.

    Attributes:
        known: Dict mapping lowercased term to canonical form.
        similarity_threshold: Minimum fuzzy match ratio (0.0-1.0).
    """

    def __init__(
        self,
        known_terms: list[str] | None = None,
        similarity_threshold: float = 0.8,
    ) -> None:
        """Initialize MaintenanceValidator.

        Args:
            known_terms: Override list of known maintenance terms.
                Defaults to loading from
                ``data/datasets/maintenance/known_terms.json``.
            similarity_threshold: Minimum SequenceMatcher ratio to
                consider a fuzzy match valid.
        """
        terms = known_terms or load_dataset("maintenance", "known_terms")
        self.known: dict[str, str] = {t.lower(): t for t in terms}
        self.similarity_threshold = similarity_threshold

    def _best_match(self, name: str) -> tuple[str, float]:
        """Find the best matching known term for a candidate name.

        Args:
            name: Lowercased candidate entity name.

        Returns:
            Tuple of (canonical_name, similarity_score). Returns
            ("", 0.0) if no known terms exist.
        """
        best_term = ""
        best_score = 0.0
        for key, canonical in self.known.items():
            score = SequenceMatcher(None, name, key).ratio()
            if score > best_score:
                best_score = score
                best_term = canonical
        return best_term, best_score

    def validate(self, candidates: list[dict]) -> list[dict]:
        """Validate and normalize candidate maintenance entities.

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
            best_term, score = self._best_match(key)
            if score >= self.similarity_threshold:
                entry["name"] = best_term
                entry["confidence"] = entry["confidence"] * score
                entry["validated"] = True
                results.append(entry)
                continue

            # No match → keep but mark uncertain
            entry["validated"] = False
            results.append(entry)

        return results
