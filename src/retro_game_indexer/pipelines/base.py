"""Base protocol for detection pipelines."""

from typing import Protocol


class Detector(Protocol):
    """Interface that all detection pipelines must implement.

    Each detector receives transcript segments and returns a list of
    mentions with a standardized format.
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
