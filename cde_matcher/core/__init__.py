"""
Core package containing the business logic for CDE matching.

This package is UI-agnostic and contains the core functionality
for matching algorithms, data adapters, and corpus management.
"""

from .pipeline import CDEMatcherPipeline, extract_variables_flexible

__all__ = [
    'CDEMatcherPipeline',
    'extract_variables_flexible'
]