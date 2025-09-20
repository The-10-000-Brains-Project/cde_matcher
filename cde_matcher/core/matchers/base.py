"""
Base matcher interface and result structures.

This module defines the abstract base class for all matchers and the
MatchResult dataclass for representing matching results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class MatchResult:
    """
    Represents a single match result between a source variable and target CDE.

    Attributes:
        source: The original variable name being matched
        target: The CDE item that was matched against
        confidence: Match confidence score between 0.0 and 1.0
        match_type: Type of matching algorithm used (e.g., 'exact', 'fuzzy', 'semantic')
        metadata: Additional information about the match (algorithm params, scores, etc.)

    Example:
        >>> result = MatchResult(
        ...     source="age_death",
        ...     target="age_at_death",
        ...     confidence=0.95,
        ...     match_type="fuzzy",
        ...     metadata={"algorithm": "levenshtein", "raw_score": 0.85}
        ... )
    """
    source: str
    target: str
    confidence: float
    match_type: str
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Validate confidence score is within valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class BaseMatcher(ABC):
    """
    Abstract base class for all matching algorithms.

    This class defines the interface that all matchers must implement.
    Subclasses should implement specific matching strategies while
    maintaining consistent behavior and return types.

    Example:
        >>> class ExactMatcher(BaseMatcher):
        ...     @property
        ...     def name(self) -> str:
        ...         return "exact"
        ...
        ...     def configure(self, case_sensitive=True, **kwargs):
        ...         self.case_sensitive = case_sensitive
        ...
        ...     def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        ...         # Implementation here
        ...         pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name/type of this matcher.

        Returns:
            String identifier for the matcher type (e.g., 'exact', 'fuzzy', 'semantic')
        """
        pass

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        Configure the matcher with algorithm-specific parameters.

        Args:
            **kwargs: Configuration parameters specific to the matcher implementation

        Raises:
            ValueError: If invalid configuration parameters are provided

        Example:
            >>> matcher.configure(threshold=0.8, algorithm='levenshtein')
        """
        pass

    @abstractmethod
    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        """
        Match a source variable against a list of target CDEs.

        Args:
            source: Variable name to match
            targets: List of CDE items to match against

        Returns:
            List of MatchResult objects sorted by confidence (highest first).
            Should only include matches above the configured threshold.

        Raises:
            ValueError: If source is empty or targets list is empty
            RuntimeError: If matcher is not properly configured

        Example:
            >>> results = matcher.match("age_death", ["age_at_death", "death_age", "birth_date"])
            >>> for result in results:
            ...     print(f"{result.target}: {result.confidence:.2f}")
            age_at_death: 0.95
            death_age: 0.80
        """
        pass

    def validate_inputs(self, source: str, targets: List[str]) -> None:
        """
        Validate input parameters for matching.

        Args:
            source: Variable name to validate
            targets: List of targets to validate

        Raises:
            ValueError: If inputs are invalid
        """
        if not source or not source.strip():
            raise ValueError("Source variable name cannot be empty")

        if not targets:
            raise ValueError("Targets list cannot be empty")

        if not all(isinstance(target, str) and target.strip() for target in targets):
            raise ValueError("All targets must be non-empty strings")

    def sort_results(self, results: List[MatchResult]) -> List[MatchResult]:
        """
        Sort match results by confidence score (highest first).

        Args:
            results: List of MatchResult objects to sort

        Returns:
            Sorted list of MatchResult objects
        """
        return sorted(results, key=lambda x: x.confidence, reverse=True)


class MatcherError(Exception):
    """Base exception for matcher-related errors."""
    pass


class ConfigurationError(MatcherError):
    """Exception raised for configuration-related errors."""
    pass


class MatchingError(MatcherError):
    """Exception raised during the matching process."""
    pass