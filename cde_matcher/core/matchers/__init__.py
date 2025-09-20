"""
Matching algorithms package.

Contains the base matcher interface and implementations for various
matching strategies including exact, fuzzy, and semantic matching.
"""

from .base import BaseMatcher, MatchResult, MatcherError, ConfigurationError, MatchingError
from .exact import ExactMatcher
from .fuzzy import FuzzyMatcher
from .semantic import SemanticMatcher
from .factory import MatcherFactory, create_matcher, create_ensemble

__all__ = [
    "BaseMatcher", "MatchResult", "MatcherError", "ConfigurationError", "MatchingError",
    "ExactMatcher", "FuzzyMatcher", "SemanticMatcher",
    "MatcherFactory", "create_matcher", "create_ensemble"
]