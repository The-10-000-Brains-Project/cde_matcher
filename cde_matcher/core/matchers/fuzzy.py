"""
Fuzzy string matching implementation using rapidfuzz.

This module provides fuzzy string matching functionality with multiple algorithms
and configurable thresholds using the BaseMatcher interface.
"""

from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz, process
from .base import BaseMatcher, MatchResult, ConfigurationError


class FuzzyMatcher(BaseMatcher):
    """
    Fuzzy string matcher using rapidfuzz library.

    Supports multiple algorithms including ratio, partial_ratio, token_sort_ratio,
    and token_set_ratio with configurable similarity thresholds.

    Example:
        >>> matcher = FuzzyMatcher()
        >>> matcher.configure(threshold=0.8, algorithm='ratio')
        >>> results = matcher.match("age_death", ["age_at_death", "death_age"])
        >>> for r in results:
        ...     print(f"{r.target}: {r.confidence:.2f}")
        age_at_death: 0.85
        death_age: 0.75
    """

    # Available fuzzy matching algorithms
    ALGORITHMS = {
        'ratio': fuzz.ratio,
        'partial_ratio': fuzz.partial_ratio,
        'token_sort_ratio': fuzz.token_sort_ratio,
        'token_set_ratio': fuzz.token_set_ratio,
    }

    def __init__(self):
        """Initialize the FuzzyMatcher with default configuration."""
        self._threshold = 0.7
        self._algorithm = 'ratio'
        self._case_sensitive = False
        self._max_results = None  # No limit by default
        self._configured = False

    @property
    def name(self) -> str:
        """Return the matcher name."""
        return "fuzzy"

    def configure(self,
                 threshold: float = 0.7,
                 algorithm: str = 'ratio',
                 case_sensitive: bool = False,
                 max_results: Optional[int] = None,
                 **kwargs) -> None:
        """
        Configure the fuzzy matcher.

        Args:
            threshold: Minimum similarity score (0.0 to 1.0) to consider a match
            algorithm: Fuzzy algorithm to use ('ratio', 'partial_ratio',
                      'token_sort_ratio', 'token_set_ratio')
            case_sensitive: Whether to perform case-sensitive matching
            max_results: Maximum number of results to return (None for all)
            **kwargs: Additional configuration parameters (ignored)

        Raises:
            ConfigurationError: If invalid configuration parameters are provided
        """
        # Validate threshold
        if not 0.0 <= threshold <= 1.0:
            raise ConfigurationError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

        # Validate algorithm
        if algorithm not in self.ALGORITHMS:
            available = ', '.join(self.ALGORITHMS.keys())
            raise ConfigurationError(f"Algorithm must be one of: {available}, got '{algorithm}'")

        # Validate case_sensitive
        if not isinstance(case_sensitive, bool):
            raise ConfigurationError(f"case_sensitive must be boolean, got {type(case_sensitive)}")

        # Validate max_results
        if max_results is not None and (not isinstance(max_results, int) or max_results <= 0):
            raise ConfigurationError(f"max_results must be positive integer or None, got {max_results}")

        self._threshold = threshold
        self._algorithm = algorithm
        self._case_sensitive = case_sensitive
        self._max_results = max_results
        self._configured = True

    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        """
        Find fuzzy matches between source and targets.

        Args:
            source: Variable name to match
            targets: List of CDE items to match against

        Returns:
            List of MatchResult objects sorted by confidence (highest first)

        Raises:
            RuntimeError: If matcher is not configured
            ValueError: If inputs are invalid
        """
        if not self._configured:
            raise RuntimeError("Matcher must be configured before use. Call configure() first.")

        # Validate inputs
        self.validate_inputs(source, targets)

        results = []

        # Get the algorithm function
        algorithm_func = self.ALGORITHMS[self._algorithm]

        # Prepare source for comparison
        source_compare = source if self._case_sensitive else source.lower()

        for target in targets:
            # Prepare target for comparison
            target_compare = target if self._case_sensitive else target.lower()

            # Calculate similarity score (rapidfuzz returns 0-100, normalize to 0-1)
            raw_score = algorithm_func(source_compare, target_compare)
            confidence = raw_score / 100.0

            # Only include matches above threshold
            if confidence >= self._threshold:
                result = MatchResult(
                    source=source,
                    target=target,
                    confidence=confidence,
                    match_type=self.name,
                    metadata={
                        "algorithm": self._algorithm,
                        "threshold": self._threshold,
                        "case_sensitive": self._case_sensitive,
                        "raw_score": raw_score,
                        "source_normalized": source_compare,
                        "target_normalized": target_compare
                    }
                )
                results.append(result)

        # Sort by confidence (highest first)
        results = self.sort_results(results)

        # Apply max_results limit if specified
        if self._max_results is not None:
            results = results[:self._max_results]

        return results

    def get_best_matches(self, source: str, targets: List[str], limit: int = 5) -> List[MatchResult]:
        """
        Get the best fuzzy matches using rapidfuzz's optimized process.

        This method uses rapidfuzz.process.extract for better performance
        when finding top matches from a large list.

        Args:
            source: Variable name to match
            targets: List of CDE items to match against
            limit: Maximum number of matches to return

        Returns:
            List of top MatchResult objects

        Raises:
            RuntimeError: If matcher is not configured
            ValueError: If inputs are invalid
        """
        if not self._configured:
            raise RuntimeError("Matcher must be configured before use. Call configure() first.")

        # Validate inputs
        self.validate_inputs(source, targets)

        # Get the algorithm function
        algorithm_func = self.ALGORITHMS[self._algorithm]

        # Prepare source for comparison
        source_compare = source if self._case_sensitive else source.lower()

        # Prepare targets for comparison
        targets_compare = [target if self._case_sensitive else target.lower()
                          for target in targets]

        # Use rapidfuzz process.extract for optimized top-k search
        matches = process.extract(
            source_compare,
            targets_compare,
            scorer=algorithm_func,
            limit=limit,
            score_cutoff=self._threshold * 100  # Convert back to 0-100 scale
        )

        results = []
        for match_text, raw_score, index in matches:
            confidence = raw_score / 100.0
            original_target = targets[index]

            result = MatchResult(
                source=source,
                target=original_target,
                confidence=confidence,
                match_type=self.name,
                metadata={
                    "algorithm": self._algorithm,
                    "threshold": self._threshold,
                    "case_sensitive": self._case_sensitive,
                    "raw_score": raw_score,
                    "source_normalized": source_compare,
                    "target_normalized": match_text,
                    "method": "process_extract"
                }
            )
            results.append(result)

        return results

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Dictionary containing current configuration settings
        """
        return {
            "threshold": self._threshold,
            "algorithm": self._algorithm,
            "case_sensitive": self._case_sensitive,
            "max_results": self._max_results,
            "configured": self._configured,
            "available_algorithms": list(self.ALGORITHMS.keys())
        }