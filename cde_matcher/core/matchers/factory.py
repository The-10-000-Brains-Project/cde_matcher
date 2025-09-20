"""
Matcher factory for creating and configuring matchers.

This module provides a factory pattern implementation for creating
matcher instances with consistent configuration.
"""

from typing import Dict, Any, Type, List
from .base import BaseMatcher, MatcherError
from .exact import ExactMatcher
from .fuzzy import FuzzyMatcher
from .semantic import SemanticMatcher


class MatcherFactory:
    """
    Factory for creating and configuring matcher instances.

    Provides a centralized way to create matchers with configuration
    and supports registration of new matcher types.

    Example:
        >>> factory = MatcherFactory()
        >>> matcher = factory.create_matcher('fuzzy', threshold=0.8)
        >>> results = matcher.match("age_death", ["age_at_death"])
    """

    def __init__(self):
        """Initialize the factory with default matcher types."""
        self._matchers: Dict[str, Type[BaseMatcher]] = {
            'exact': ExactMatcher,
            'fuzzy': FuzzyMatcher,
            'semantic': SemanticMatcher,
        }

    def register_matcher(self, name: str, matcher_class: Type[BaseMatcher]) -> None:
        """
        Register a new matcher type.

        Args:
            name: Name identifier for the matcher
            matcher_class: Matcher class that inherits from BaseMatcher

        Raises:
            MatcherError: If matcher class is invalid
        """
        if not issubclass(matcher_class, BaseMatcher):
            raise MatcherError(f"Matcher class must inherit from BaseMatcher")

        self._matchers[name] = matcher_class

    def create_matcher(self, matcher_type: str, **config) -> BaseMatcher:
        """
        Create a configured matcher instance.

        Args:
            matcher_type: Type of matcher to create ('exact', 'fuzzy', 'semantic')
            **config: Configuration parameters to pass to the matcher

        Returns:
            Configured matcher instance

        Raises:
            MatcherError: If matcher type is unknown or configuration fails

        Example:
            >>> matcher = factory.create_matcher('fuzzy', threshold=0.8, algorithm='ratio')
        """
        if matcher_type not in self._matchers:
            available = ', '.join(self._matchers.keys())
            raise MatcherError(f"Unknown matcher type '{matcher_type}'. Available: {available}")

        try:
            matcher_class = self._matchers[matcher_type]
            matcher = matcher_class()
            matcher.configure(**config)
            return matcher
        except Exception as e:
            raise MatcherError(f"Failed to create {matcher_type} matcher: {e}")

    def create_ensemble(self, matcher_configs: List[Dict[str, Any]]) -> List[BaseMatcher]:
        """
        Create multiple configured matchers for ensemble matching.

        Args:
            matcher_configs: List of dictionaries containing 'type' and configuration

        Returns:
            List of configured matcher instances

        Raises:
            MatcherError: If any matcher creation fails

        Example:
            >>> configs = [
            ...     {'type': 'exact', 'case_sensitive': False},
            ...     {'type': 'fuzzy', 'threshold': 0.8, 'algorithm': 'ratio'},
            ...     {'type': 'semantic'}
            ... ]
            >>> matchers = factory.create_ensemble(configs)
        """
        matchers = []

        for i, config in enumerate(matcher_configs):
            if 'type' not in config:
                raise MatcherError(f"Configuration {i} missing required 'type' field")

            matcher_type = config.pop('type')  # Remove type from config
            try:
                matcher = self.create_matcher(matcher_type, **config)
                matchers.append(matcher)
            except Exception as e:
                raise MatcherError(f"Failed to create matcher {i} ({matcher_type}): {e}")

        return matchers

    def get_available_matchers(self) -> List[str]:
        """
        Get list of available matcher types.

        Returns:
            List of available matcher type names
        """
        return list(self._matchers.keys())

    def get_matcher_info(self, matcher_type: str) -> Dict[str, Any]:
        """
        Get information about a specific matcher type.

        Args:
            matcher_type: Type of matcher to get info for

        Returns:
            Dictionary containing matcher information

        Raises:
            MatcherError: If matcher type is unknown
        """
        if matcher_type not in self._matchers:
            available = ', '.join(self._matchers.keys())
            raise MatcherError(f"Unknown matcher type '{matcher_type}'. Available: {available}")

        matcher_class = self._matchers[matcher_type]

        # Create a temporary instance to get default configuration
        try:
            temp_matcher = matcher_class()
            # Try to get configuration if available
            if hasattr(temp_matcher, 'get_configuration'):
                default_config = temp_matcher.get_configuration()
            else:
                default_config = {}
        except:
            default_config = {}

        return {
            'name': matcher_type,
            'class': matcher_class.__name__,
            'module': matcher_class.__module__,
            'docstring': matcher_class.__doc__,
            'default_config': default_config
        }


# Global factory instance for convenience
default_factory = MatcherFactory()


def create_matcher(matcher_type: str, **config) -> BaseMatcher:
    """
    Convenience function to create a matcher using the default factory.

    Args:
        matcher_type: Type of matcher to create
        **config: Configuration parameters

    Returns:
        Configured matcher instance
    """
    return default_factory.create_matcher(matcher_type, **config)


def create_ensemble(matcher_configs: List[Dict[str, Any]]) -> List[BaseMatcher]:
    """
    Convenience function to create matcher ensemble using the default factory.

    Args:
        matcher_configs: List of matcher configurations

    Returns:
        List of configured matcher instances
    """
    return default_factory.create_ensemble(matcher_configs)