"""Base protocols for detection and validation pipelines."""

from typing import Protocol


class Detector(Protocol):
    """Interface that all detection pipelines must implement.

    Each detector receives transcript segments and returns a list of
    candidate mentions with a standardized format.
    """

    def detect(self, segments: list[dict]) -> list[dict]:
        """Detect mentions in transcript segments.

        Args:
            segments: List of dicts with "text" and "start" keys.

        Returns:
            List of dicts with "name", "category", "timestamp",
            and "confidence" keys.
        """
        ...


class Validator(Protocol):
    """Interface for post-detection validation.

    Validators receive candidate entities from a detector and return
    confirmed entities after filtering, normalizing, and re-scoring.
    """

    def validate(self, candidates: list[dict]) -> list[dict]:
        """Validate and normalize candidate entities.

        Args:
            candidates: Raw detector output — list of dicts with
                "name", "category", "timestamp", "confidence" keys.

        Returns:
            Validated entities with an added "validated" (bool) key.
            Names may be normalized to canonical forms. Confidence
            scores may be adjusted based on dataset matching.
        """
        ...
