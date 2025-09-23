"""
CDE Matcher - A tool for matching variables to Common Data Elements (CDEs).

This package provides a modular framework for matching variable names
to standardized Common Data Elements using various algorithms including
exact matching, fuzzy string matching, and semantic matching.
"""

__version__ = "0.1.0"
__author__ = "CDE Matcher Team"

from .core.matchers.base import BaseMatcher, MatchResult
from .core.pipeline import CDEMatcherPipeline, extract_variables_flexible

__all__ = [
    "BaseMatcher",
    "MatchResult",
    "CDEMatcherPipeline",
    "extract_variables_flexible"
]