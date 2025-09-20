"""
Semantic matching implementation based on domain knowledge mappings.

This module provides semantic matching functionality using predefined
mappings between concepts and their variations in biomedical contexts.
"""

from typing import List, Dict, Any, Set, Optional
from .base import BaseMatcher, MatchResult, ConfigurationError


class SemanticMatcher(BaseMatcher):
    """
    Semantic matcher using predefined domain knowledge mappings.

    Maps biomedical concepts to their various representations and synonyms.
    Particularly useful for matching variables that represent the same concept
    but use different naming conventions.

    Example:
        >>> matcher = SemanticMatcher()
        >>> matcher.configure()
        >>> results = matcher.match("donor id", ["participant_id", "BB_id"])
        >>> print(results[0].target)  # "participant_id"
    """

    def __init__(self):
        """Initialize the SemanticMatcher with default biomedical mappings."""
        self._mappings = self._get_default_mappings()
        self._case_sensitive = False
        self._exact_only = False
        self._custom_mappings = {}
        self._configured = False

    @property
    def name(self) -> str:
        """Return the matcher name."""
        return "semantic"

    def configure(self,
                 case_sensitive: bool = False,
                 exact_only: bool = False,
                 custom_mappings: Optional[Dict[str, List[str]]] = None,
                 **kwargs) -> None:
        """
        Configure the semantic matcher.

        Args:
            case_sensitive: Whether to perform case-sensitive matching
            exact_only: If True, only exact semantic matches are returned.
                       If False, partial matches are also considered.
            custom_mappings: Additional custom semantic mappings to add
            **kwargs: Additional configuration parameters (ignored)

        Raises:
            ConfigurationError: If invalid configuration parameters are provided
        """
        if not isinstance(case_sensitive, bool):
            raise ConfigurationError(f"case_sensitive must be boolean, got {type(case_sensitive)}")

        if not isinstance(exact_only, bool):
            raise ConfigurationError(f"exact_only must be boolean, got {type(exact_only)}")

        if custom_mappings is not None and not isinstance(custom_mappings, dict):
            raise ConfigurationError(f"custom_mappings must be dict or None, got {type(custom_mappings)}")

        self._case_sensitive = case_sensitive
        self._exact_only = exact_only
        self._custom_mappings = custom_mappings or {}

        # Merge custom mappings with defaults
        self._update_mappings()
        self._configured = True

    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        """
        Find semantic matches between source and targets.

        Args:
            source: Variable name to match
            targets: List of CDE items to match against

        Returns:
            List of MatchResult objects for semantic matches

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
        source_compare = source if self._case_sensitive else source.lower().strip()

        # Find semantic mappings for the source
        semantic_concepts = self._find_concepts_for_term(source_compare)

        if not semantic_concepts:
            return results

        for target in targets:
            # Prepare target for comparison
            target_compare = target if self._case_sensitive else target.lower().strip()

            # Check if target matches any of the semantic concepts
            match_info = self._check_semantic_match(source_compare, target_compare, semantic_concepts)

            if match_info:
                result = MatchResult(
                    source=source,
                    target=target,
                    confidence=match_info['confidence'],
                    match_type=self.name,
                    metadata={
                        "concept": match_info['concept'],
                        "match_method": match_info['method'],
                        "case_sensitive": self._case_sensitive,
                        "exact_only": self._exact_only,
                        "source_normalized": source_compare,
                        "target_normalized": target_compare
                    }
                )
                results.append(result)

        return self.sort_results(results)

    def _find_concepts_for_term(self, term: str) -> List[str]:
        """
        Find semantic concepts that the given term could represent.

        Args:
            term: The term to find concepts for

        Returns:
            List of concept keys that this term might represent
        """
        concepts = []

        for concept_key, variations in self._mappings.items():
            term_variations = [term] if self._case_sensitive else [term.lower()]

            for variation in variations:
                var_compare = variation if self._case_sensitive else variation.lower()

                if self._exact_only:
                    # Exact match only
                    if term in term_variations and var_compare in term_variations:
                        concepts.append(concept_key)
                        break
                else:
                    # Allow partial matches
                    if (term in var_compare or var_compare in term or
                        any(tv in var_compare for tv in term_variations)):
                        concepts.append(concept_key)
                        break

        return concepts

    def _check_semantic_match(self, source: str, target: str, concepts: List[str]) -> Optional[Dict[str, Any]]:
        """
        Check if target matches any of the source's semantic concepts.

        Args:
            source: Source term (normalized)
            target: Target term (normalized)
            concepts: List of concepts the source represents

        Returns:
            Match information dict if match found, None otherwise
        """
        for concept in concepts:
            if concept not in self._mappings:
                continue

            variations = self._mappings[concept]

            for variation in variations:
                var_compare = variation if self._case_sensitive else variation.lower()

                if self._exact_only:
                    # Exact semantic match
                    if target == var_compare:
                        return {
                            'concept': concept,
                            'method': 'exact_semantic',
                            'confidence': 1.0,
                            'matched_variation': variation
                        }
                else:
                    # Partial semantic match
                    if target == var_compare:
                        return {
                            'concept': concept,
                            'method': 'exact_semantic',
                            'confidence': 1.0,
                            'matched_variation': variation
                        }
                    elif target in var_compare or var_compare in target:
                        # Calculate confidence based on overlap
                        overlap = len(set(target.split()) & set(var_compare.split()))
                        total_words = len(set(target.split()) | set(var_compare.split()))
                        confidence = 0.7 + (0.3 * overlap / total_words) if total_words > 0 else 0.7

                        return {
                            'concept': concept,
                            'method': 'partial_semantic',
                            'confidence': confidence,
                            'matched_variation': variation
                        }

        return None

    def _update_mappings(self):
        """Update mappings by merging custom mappings with defaults."""
        # Start with default mappings
        updated_mappings = self._get_default_mappings().copy()

        # Add custom mappings
        for concept, variations in self._custom_mappings.items():
            if concept in updated_mappings:
                # Merge with existing concept
                existing_variations = set(updated_mappings[concept])
                new_variations = set(variations)
                updated_mappings[concept] = list(existing_variations | new_variations)
            else:
                # Add new concept
                updated_mappings[concept] = variations

        self._mappings = updated_mappings

    def _get_default_mappings(self) -> Dict[str, List[str]]:
        """
        Get default biomedical semantic mappings.

        Returns:
            Dictionary mapping concepts to their variations
        """
        return {
            # ID-related mappings
            'donor_id': ['participant_id', 'BB_id', 'additional_ID', 'donor_id', 'subject_id', 'patient_id'],

            # Age-related mappings
            'age_at_death': ['age_at_death', 'age_at_onset', 'age_at_diagnosis', 'death_age'],
            'age_of_onset_cognitive_symptoms': ['age_at_onset', 'age_of_onset', 'onset_age'],
            'age_of_dementia_diagnosis': ['age_at_diagnosis', 'diagnosis_age'],

            # Demographics mappings
            'sex': ['sex', 'gender'],
            'race': ['race', 'ethnicity_race'],
            'hispanic_latino': ['ethnicity', 'hispanic', 'latino'],
            'years_of_education': ['education_years', 'education', 'years_education'],

            # Genetics mappings
            'apoe_genotype': ['apoe_genotype', 'genetics_screening', 'apoe', 'apolipoprotein'],

            # Brain/tissue mappings
            'fresh_brain_weight': ['brain_weight', 'fresh_weight'],
            'brain_ph': ['brain_ph', 'ph', 'tissue_ph'],
            'pmi': ['pmi', 'postmortem_interval', 'post_mortem_interval'],
            'rin': ['rin', 'rna_integrity', 'rna_integrity_number'],

            # Pathology mappings
            'braak': ['braak_stage', 'braak_score', 'braak'],
            'thal': ['thal_phase', 'thal_score', 'thal'],
            'cerad_score': ['cerad', 'cerad_score'],

            # Clinical assessment mappings
            'cognitive_status': ['cognitive_status', 'dementia_status', 'cognitive_state'],
            'last_casi_score': ['casi_score', 'casi'],
            'last_mmse_score': ['mmse_score', 'mmse'],
            'last_moca_score': ['moca_score', 'moca'],

            # Study/diagnosis mappings
            'primary_study_name': ['study_name', 'cohort_name', 'primary_study'],
            'secondary_study_name': ['secondary_study', 'additional_study'],

            # Additional biomedical concepts
            'cerebrospinal_fluid': ['csf', 'cerebrospinal_fluid', 'spinal_fluid'],
            'body_mass_index': ['bmi', 'body_mass_index'],
            'blood_pressure': ['bp', 'blood_pressure', 'systolic', 'diastolic'],
            'medication': ['meds', 'medication', 'drugs', 'pharmaceuticals'],
        }

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Dictionary containing current configuration settings
        """
        return {
            "case_sensitive": self._case_sensitive,
            "exact_only": self._exact_only,
            "configured": self._configured,
            "total_concepts": len(self._mappings),
            "custom_mappings_count": len(self._custom_mappings)
        }

    def get_available_concepts(self) -> Dict[str, List[str]]:
        """
        Get all available semantic concepts and their variations.

        Returns:
            Dictionary of all concept mappings
        """
        return self._mappings.copy()

    def add_concept_mapping(self, concept: str, variations: List[str]) -> None:
        """
        Add a new concept mapping.

        Args:
            concept: The concept key
            variations: List of variations for this concept

        Raises:
            ConfigurationError: If inputs are invalid
        """
        if not isinstance(concept, str) or not concept.strip():
            raise ConfigurationError("Concept must be a non-empty string")

        if not isinstance(variations, list) or not all(isinstance(v, str) for v in variations):
            raise ConfigurationError("Variations must be a list of strings")

        self._custom_mappings[concept] = variations
        if self._configured:
            self._update_mappings()