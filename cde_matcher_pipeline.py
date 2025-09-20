"""
General CDE matcher pipeline.

This script demonstrates the new modular architecture for matching
variable names to Common Data Elements (CDEs) using multiple algorithms
with the new BaseMatcher interface and implementations.
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import asdict

from cde_matcher.core.matchers import (
    create_matcher, create_ensemble, MatchResult
)


class CDEMatcherPipeline:
    """
    Pipeline for matching CDE fields using multiple algorithms.

    Provides a unified interface for running exact, fuzzy, and semantic
    matching on CDE datasets using the modular matcher architecture.
    """

    def __init__(self):
        """Initialize the pipeline with default matcher configurations."""
        self.exact_matcher = None
        self.fuzzy_matcher = None
        self.semantic_matcher = None
        self.results = {}

    def configure_matchers(self,
                          exact_config: Dict[str, Any] = None,
                          fuzzy_config: Dict[str, Any] = None,
                          semantic_config: Dict[str, Any] = None):
        """
        Configure the matchers for the pipeline.

        Args:
            exact_config: Configuration for exact matcher
            fuzzy_config: Configuration for fuzzy matcher
            semantic_config: Configuration for semantic matcher
        """
        # Default configurations
        exact_config = exact_config or {"case_sensitive": False}
        fuzzy_config = fuzzy_config or {"threshold": 0.7, "algorithm": "ratio"}
        semantic_config = semantic_config or {"case_sensitive": False, "exact_only": False}

        # Create matchers
        self.exact_matcher = create_matcher("exact", **exact_config)
        self.fuzzy_matcher = create_matcher("fuzzy", **fuzzy_config)
        self.semantic_matcher = create_matcher("semantic", **semantic_config)

    def load_data(self, source_path: str, target_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load source and target datasets.

        Args:
            source_path: Path to source CSV file containing variable names
            target_path: Path to target CSV file containing CDE items

        Returns:
            Tuple of (source_df, target_df)
        """
        source_df = pd.read_csv(source_path)
        target_df = pd.read_csv(target_path)

        print(f"Loaded source data: {source_df.shape}")
        print(f"Loaded target data: {target_df.shape}")

        return source_df, target_df

    def extract_fields(self, source_df: pd.DataFrame, target_df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Extract field names from both datasets.

        Args:
            source_df: Source dataframe containing variable names
            target_df: Target dataframe containing CDE items

        Returns:
            Tuple of (source_fields, target_items)
        """
        source_fields = [col.strip() for col in source_df.columns]
        target_items = target_df['Item'].dropna().str.strip().unique().tolist()

        print(f"Source fields: {len(source_fields)}")
        print(f"Target items: {len(target_items)}")

        return source_fields, target_items

    def run_exact_matching(self, source_fields: List[str], target_items: List[str]) -> List[Dict[str, Any]]:
        """
        Run exact matching between source fields and target items.

        Args:
            source_fields: List of source field names
            target_items: List of target item names

        Returns:
            List of match dictionaries
        """
        print("\n🎯 Running exact matching...")

        all_matches = []

        for source_field in source_fields:
            results = self.exact_matcher.match(source_field, target_items)

            for result in results:
                match_dict = {
                    'source_field': result.source,
                    'target_item': result.target,
                    'confidence': result.confidence,
                    'match_type': result.match_type,
                    'metadata': result.metadata
                }
                all_matches.append(match_dict)

        print(f"Found {len(all_matches)} exact matches")
        return all_matches

    def run_fuzzy_matching(self, source_fields: List[str], target_items: List[str]) -> List[Dict[str, Any]]:
        """
        Run fuzzy matching between source fields and target items.

        Args:
            source_fields: List of source field names
            target_items: List of target item names

        Returns:
            List of match dictionaries
        """
        print("\n🔍 Running fuzzy matching...")

        all_matches = []

        for source_field in source_fields:
            results = self.fuzzy_matcher.match(source_field, target_items)

            for result in results:
                match_dict = {
                    'source_field': result.source,
                    'target_item': result.target,
                    'confidence': result.confidence,
                    'similarity_score': result.confidence,  # For compatibility
                    'match_type': result.match_type,
                    'metadata': result.metadata
                }
                all_matches.append(match_dict)

        print(f"Found {len(all_matches)} fuzzy matches")
        return all_matches

    def run_semantic_matching(self, source_fields: List[str], target_items: List[str]) -> List[Dict[str, Any]]:
        """
        Run semantic matching between source fields and target items.

        Args:
            source_fields: List of source field names
            target_items: List of target item names

        Returns:
            List of match dictionaries
        """
        print("\n🧠 Running semantic matching...")

        all_matches = []

        for source_field in source_fields:
            results = self.semantic_matcher.match(source_field, target_items)

            for result in results:
                match_dict = {
                    'source_field': result.source,
                    'target_item': result.target,
                    'confidence': result.confidence,
                    'match_type': result.match_type,
                    'metadata': result.metadata
                }
                all_matches.append(match_dict)

        print(f"Found {len(all_matches)} semantic matches")
        return all_matches

    def run_pipeline(self,
                    source_path: str = "data/cdes/SEA-AD_Cohort_Metadata.csv",
                    target_path: str = "data/cdes/digipath_cdes.csv",
                    output_file: str = "cde_matches_modular.json") -> Dict[str, Any]:
        """
        Run the complete matching pipeline.

        Args:
            source_path: Path to source CSV file containing variable names
            target_path: Path to target CSV file containing CDE items
            output_file: Output JSON file path

        Returns:
            Dictionary containing all match results
        """
        print("🚀 Starting CDE Matcher Pipeline")
        print("=" * 50)

        # Configure matchers if not already done
        if not self.exact_matcher:
            self.configure_matchers()

        # Load data
        source_df, target_df = self.load_data(source_path, target_path)

        # Extract fields
        source_fields, target_items = self.extract_fields(source_df, target_df)

        # Run matching algorithms
        exact_matches = self.run_exact_matching(source_fields, target_items)
        fuzzy_matches = self.run_fuzzy_matching(source_fields, target_items)
        semantic_matches = self.run_semantic_matching(source_fields, target_items)

        # Compile results
        results = {
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'semantic_matches': semantic_matches,
            'summary': {
                'total_exact_matches': len(exact_matches),
                'total_fuzzy_matches': len(fuzzy_matches),
                'total_semantic_matches': len(semantic_matches),
                'unique_source_fields': len(source_fields),
                'unique_target_items': len(target_items)
            },
            'configuration': {
                'exact_matcher': self.exact_matcher.get_configuration(),
                'fuzzy_matcher': self.fuzzy_matcher.get_configuration(),
                'semantic_matcher': self.semantic_matcher.get_configuration()
            }
        }

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        print("\n" + "=" * 50)
        print("📊 PIPELINE SUMMARY:")
        print(f"  - Total source fields: {results['summary']['unique_source_fields']}")
        print(f"  - Total target items: {results['summary']['unique_target_items']}")
        print(f"  - Exact matches: {results['summary']['total_exact_matches']}")
        print(f"  - Fuzzy matches: {results['summary']['total_fuzzy_matches']}")
        print(f"  - Semantic matches: {results['summary']['total_semantic_matches']}")
        print(f"\n💾 Results saved to: {output_file}")

        self.results = results
        return results

    def display_sample_matches(self, match_type: str = "exact", limit: int = 5):
        """
        Display sample matches from the results.

        Args:
            match_type: Type of matches to display ('exact', 'fuzzy', 'semantic')
            limit: Number of matches to display
        """
        if not self.results:
            print("No results available. Run the pipeline first.")
            return

        matches_key = f"{match_type}_matches"
        if matches_key not in self.results:
            print(f"No {match_type} matches found.")
            return

        matches = self.results[matches_key][:limit]
        print(f"\n📋 Sample {match_type.title()} Matches (showing {len(matches)}):")
        print("-" * 60)

        for i, match in enumerate(matches, 1):
            source = match['source_field']
            target = match['target_item']
            conf = match['confidence']
            print(f"{i}. Source: '{source}' ↔ Target: '{target}' (conf: {conf:.3f})")


def main():
    """Main function to run the pipeline."""
    pipeline = CDEMatcherPipeline()

    # Custom configuration example
    pipeline.configure_matchers(
        exact_config={"case_sensitive": False},
        fuzzy_config={"threshold": 0.7, "algorithm": "token_sort_ratio"},
        semantic_config={"case_sensitive": False, "exact_only": False}
    )

    # Run the pipeline
    results = pipeline.run_pipeline()

    # Display sample matches
    pipeline.display_sample_matches("exact", limit=5)
    pipeline.display_sample_matches("fuzzy", limit=5)
    pipeline.display_sample_matches("semantic", limit=5)

    return results


if __name__ == "__main__":
    results = main()