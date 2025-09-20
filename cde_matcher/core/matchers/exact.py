"""
Exact string matching implementation.

This module provides exact string matching functionality using the BaseMatcher interface.
Supports both case-sensitive and case-insensitive matching.
"""

from typing import List, Dict, Any
from .base import BaseMatcher, MatchResult, ConfigurationError


class ExactMatcher(BaseMatcher):
    """
    Exact string matcher implementation.

    Performs exact string matching with configurable case sensitivity.
    Returns matches with confidence 1.0 for exact matches, 0.0 otherwise.

    Example:
        >>> matcher = ExactMatcher()
        >>> matcher.configure(case_sensitive=False)
        >>> results = matcher.match("Age_at_Death", ["age_at_death", "birth_date"])
        >>> print(results[0].confidence)  # 1.0
    """

    def __init__(self):
        """Initialize the ExactMatcher with default configuration."""
        self._case_sensitive = True
        self._configured = False

    @property
    def name(self) -> str:
        """Return the matcher name."""
        return "exact"

    def configure(self, case_sensitive: bool = True, **kwargs) -> None:
        """
        Configure the exact matcher.

        Args:
            case_sensitive: Whether to perform case-sensitive matching (default: True)
            **kwargs: Additional configuration parameters (ignored)

        Raises:
            ConfigurationError: If invalid configuration parameters are provided
        """
        if not isinstance(case_sensitive, bool):
            raise ConfigurationError(f"case_sensitive must be boolean, got {type(case_sensitive)}")

        self._case_sensitive = case_sensitive
        self._configured = True

    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        """
        Find exact matches between source and targets.

        Args:
            source: Variable name to match
            targets: List of CDE items to match against

        Returns:
            List of MatchResult objects for exact matches (confidence = 1.0)

        Raises:
            RuntimeError: If matcher is not configured
            ValueError: If inputs are invalid
        """
        if not self._configured:
            raise RuntimeError("Matcher must be configured before use. Call configure() first.")

        # Validate inputs
        self.validate_inputs(source, targets)

        results = []

        # Prepare source for comparison
        source_compare = source if self._case_sensitive else source.lower()

        for target in targets:
            # Prepare target for comparison
            target_compare = target if self._case_sensitive else target.lower()

            # Check for exact match
            if source_compare == target_compare:
                result = MatchResult(
                    source=source,
                    target=target,
                    confidence=1.0,
                    match_type=self.name,
                    metadata={
                        "case_sensitive": self._case_sensitive,
                        "source_normalized": source_compare,
                        "target_normalized": target_compare
                    }
                )
                results.append(result)

        return self.sort_results(results)

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Dictionary containing current configuration settings
        """
        return {
            "case_sensitive": self._case_sensitive,
            "configured": self._configured
        }