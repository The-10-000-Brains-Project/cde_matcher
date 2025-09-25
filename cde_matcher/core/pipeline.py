"""
General CDE matcher pipeline.

This script demonstrates the new modular architecture for matching
variable names to Common Data Elements (CDEs) using multiple algorithms
with the new BaseMatcher interface and implementations.
"""

import pandas as pd
import json
import os
import datetime
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import asdict

from cde_matcher.core.matchers import (
    create_matcher, create_ensemble, MatchResult
)
from cde_matcher.core.data_adapter import get_data_adapter, get_data_paths


def extract_variables_flexible(df: pd.DataFrame,
                             method: str = "columns",
                             column_name: Optional[str] = None) -> List[str]:
    """
    Flexible variable extraction that works with different data formats.

    Args:
        df: DataFrame to extract variables from
        method: "columns" to use column headers, "column_values" to use specific column
        column_name: Name of column to extract from (required if method="column_values")

    Returns:
        List of variable names

    Raises:
        ValueError: If method is invalid or required parameters are missing
    """
    if method == "columns":
        # Extract from column headers (for raw clinical data)
        variables = df.columns.tolist()
    elif method == "column_values":
        if column_name is None:
            raise ValueError("column_name is required when method='column_values'")
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Extract from values in specified column (for data dictionaries)
        variables = df[column_name].dropna().astype(str).unique().tolist()
    else:
        raise ValueError(f"Invalid method '{method}'. Use 'columns' or 'column_values'")

    # Clean and validate variables
    cleaned_variables = []
    for var in variables:
        var_str = str(var).strip()
        if var_str and not var_str.startswith('Unnamed:'):
            cleaned_variables.append(var_str)

    return cleaned_variables


def generate_config_hash(exact_config: Dict[str, Any],
                        fuzzy_config: Dict[str, Any],
                        semantic_config: Dict[str, Any],
                        source_method: str,
                        source_column: Optional[str],
                        target_method: str,
                        target_column: str) -> str:
    """
    Generate a short hash based on configuration parameters.

    This ensures that identical configurations produce the same filename,
    while different configurations get different files.
    """
    config_data = {
        'exact': exact_config,
        'fuzzy': fuzzy_config,
        'semantic': semantic_config,
        'source_method': source_method,
        'source_column': source_column,
        'target_method': target_method,
        'target_column': target_column
    }

    # Create a stable string representation
    config_str = json.dumps(config_data, sort_keys=True)

    # Generate short hash
    hash_obj = hashlib.md5(config_str.encode())
    return hash_obj.hexdigest()[:8]  # Use first 8 characters


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
        self.data_adapter = get_data_adapter()
        self.data_paths = get_data_paths()

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
        source_df = self.data_adapter.read_csv(source_path)
        target_df = self.data_adapter.read_csv(target_path)

        print(f"Loaded source data: {source_df.shape}")
        print(f"Loaded target data: {target_df.shape}")

        return source_df, target_df

    def extract_fields(self,
                      source_df: pd.DataFrame,
                      target_df: pd.DataFrame,
                      source_method: str = "columns",
                      source_column: Optional[str] = None,
                      target_method: str = "column_values",
                      target_column: str = "Item") -> Tuple[List[str], List[str]]:
        """
        Extract field names from both datasets using flexible methods.

        Args:
            source_df: Source dataframe containing variable names
            target_df: Target dataframe containing CDE items
            source_method: How to extract from source ("columns" or "column_values")
            source_column: Column name for source extraction (if method="column_values")
            target_method: How to extract from target ("columns" or "column_values")
            target_column: Column name for target extraction (default: "Item")

        Returns:
            Tuple of (source_fields, target_items)
        """
        # Extract source variables
        source_fields = extract_variables_flexible(source_df, source_method, source_column)

        # Extract target variables (usually DigiPath CDEs from "Item" column)
        target_items = extract_variables_flexible(target_df, target_method, target_column)

        print(f"Source extraction: {source_method}" + (f" (column: {source_column})" if source_column else ""))
        print(f"Source fields: {len(source_fields)}")
        print(f"Target extraction: {target_method} (column: {target_column})")
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
                    source_path: Optional[str] = None,
                    target_path: Optional[str] = None,
                    output_file: Optional[str] = None,
                    source_method: str = "columns",
                    source_column: Optional[str] = None,
                    target_method: str = "column_values",
                    target_column: str = "Item") -> Dict[str, Any]:
        """
        Run the complete matching pipeline with flexible variable extraction.

        Args:
            source_path: Path to source CSV file containing variable names
            target_path: Path to target CSV file containing CDE items
            output_file: Output JSON file path (auto-generated if None)
            source_method: How to extract variables from source ("columns" or "column_values")
            source_column: Column name for source extraction (if method="column_values")
            target_method: How to extract variables from target ("columns" or "column_values")
            target_column: Column name for target extraction (default: "Item")

        Returns:
            Dictionary containing all match results
        """
        print("🚀 Starting CDE Matcher Pipeline")
        print("=" * 50)

        # Use default paths if not provided
        if source_path is None:
            source_path = self.data_adapter.get_full_path(
                self.data_paths['clinical_data'],
                'SEA-AD_Cohort_Metadata.csv'
            )
        if target_path is None:
            target_path = self.data_adapter.get_full_path(
                self.data_paths['cdes'],
                'digipath_cdes.csv'
            )

        # Configure matchers if not already done
        if not self.exact_matcher:
            self.configure_matchers()

        # Load data
        source_df, target_df = self.load_data(source_path, target_path)

        # Extract fields using flexible methods
        source_fields, target_items = self.extract_fields(
            source_df, target_df,
            source_method, source_column,
            target_method, target_column
        )

        # Run matching algorithms
        exact_matches = self.run_exact_matching(source_fields, target_items)
        fuzzy_matches = self.run_fuzzy_matching(source_fields, target_items)
        semantic_matches = self.run_semantic_matching(source_fields, target_items)

        # Generate output filename with smart caching
        if output_file is None:
            # Generate config hash for intelligent file naming
            config_hash = generate_config_hash(
                self.exact_matcher.get_configuration(),
                self.fuzzy_matcher.get_configuration(),
                self.semantic_matcher.get_configuration(),
                source_method,
                source_column,
                target_method,
                target_column
            )

            source_name = Path(source_path).stem
            method_suffix = source_method if source_method == "columns" else source_column
            output_file = self.data_adapter.get_full_path(
                self.data_paths['output'],
                f"{source_name}_{method_suffix}_{config_hash}.json"
            )

        # Check if file already exists with same configuration
        if self.data_adapter.file_exists(output_file):
            print(f"📋 Found existing results with same configuration: {output_file}")
            print("🔄 Loading cached results instead of reprocessing...")

            try:
                cached_results = self.data_adapter.read_json(output_file)

                # Verify the cached results have the expected structure
                if all(key in cached_results for key in ['exact_matches', 'fuzzy_matches', 'semantic_matches', 'summary']):
                    self.results = cached_results
                    print("✅ Successfully loaded cached results!")
                    return cached_results
                else:
                    print("⚠️ Cached file format invalid, reprocessing...")
            except Exception as e:
                print(f"⚠️ Error reading cached file, reprocessing: {e}")

        print(f"🆕 Processing new configuration, will save to: {output_file}")

        # Compile results with enhanced metadata
        results = {
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'semantic_matches': semantic_matches,
            'summary': {
                'total_exact_matches': len(exact_matches),
                'total_fuzzy_matches': len(fuzzy_matches),
                'total_semantic_matches': len(semantic_matches),
                'unique_source_fields': len(source_fields),
                'unique_target_items': len(target_items),
                'processing_timestamp': datetime.datetime.now().isoformat()
            },
            'source_info': {
                'file_path': source_path,
                'file_name': Path(source_path).name,
                'extraction_method': source_method,
                'extraction_column': source_column,
                'variables_extracted': len(source_fields),
                'dataset_shape': list(source_df.shape)
            },
            'target_info': {
                'file_path': target_path,
                'file_name': Path(target_path).name,
                'extraction_method': target_method,
                'extraction_column': target_column,
                'variables_extracted': len(target_items),
                'dataset_shape': list(target_df.shape)
            },
            'configuration': {
                'exact_matcher': self.exact_matcher.get_configuration(),
                'fuzzy_matcher': self.fuzzy_matcher.get_configuration(),
                'semantic_matcher': self.semantic_matcher.get_configuration()
            }
        }

        # Save results
        self.data_adapter.write_json(output_file, results)

        # Print summary
        print("\n" + "=" * 50)
        print("📊 PIPELINE SUMMARY:")
        print(f"  - Source: {results['source_info']['file_name']} ({source_method}" +
              (f" → {source_column}" if source_column else "") + ")")
        print(f"  - Target: {results['target_info']['file_name']} ({target_method} → {target_column})")
        print(f"  - Source fields extracted: {results['summary']['unique_source_fields']}")
        print(f"  - Target items extracted: {results['summary']['unique_target_items']}")
        print(f"  - Exact matches: {results['summary']['total_exact_matches']}")
        print(f"  - Fuzzy matches: {results['summary']['total_fuzzy_matches']}")
        print(f"  - Semantic matches: {results['summary']['total_semantic_matches']}")
        print(f"\n💾 Results saved to: {output_file}")

        self.results = results
        return results

    def run_pipeline_from_dataframes(self,
                                    source_df: pd.DataFrame,
                                    target_df: pd.DataFrame,
                                    source_name: str = "source_data",
                                    target_name: str = "target_data",
                                    output_file: Optional[str] = None,
                                    source_method: str = "columns",
                                    source_column: Optional[str] = None,
                                    target_method: str = "column_values",
                                    target_column: str = "Item") -> Dict[str, Any]:
        """
        Run the complete matching pipeline using DataFrames directly (no file I/O).

        Args:
            source_df: Source DataFrame containing variable names
            target_df: Target DataFrame containing CDE items
            source_name: Descriptive name for source dataset
            target_name: Descriptive name for target dataset
            output_file: Output JSON file path (auto-generated if None)
            source_method: How to extract variables from source ("columns" or "column_values")
            source_column: Column name for source extraction (if method="column_values")
            target_method: How to extract variables from target ("columns" or "column_values")
            target_column: Column name for target extraction (default: "Item")

        Returns:
            Dictionary containing all match results
        """
        print("🚀 Starting CDE Matcher Pipeline (DataFrame Mode)")
        print("=" * 50)

        # Configure matchers if not already done
        if not self.exact_matcher:
            self.configure_matchers()

        # Use DataFrames directly (no file loading)
        print(f"Source data: {source_df.shape}")
        print(f"Target data: {target_df.shape}")

        # Extract fields using flexible methods
        source_fields, target_items = self.extract_fields(
            source_df, target_df,
            source_method, source_column,
            target_method, target_column
        )

        # Run matching algorithms
        exact_matches = self.run_exact_matching(source_fields, target_items)
        fuzzy_matches = self.run_fuzzy_matching(source_fields, target_items)
        semantic_matches = self.run_semantic_matching(source_fields, target_items)

        # Generate output filename with smart caching
        if output_file is None:
            # Generate config hash for intelligent file naming
            config_hash = generate_config_hash(
                self.exact_matcher.get_configuration(),
                self.fuzzy_matcher.get_configuration(),
                self.semantic_matcher.get_configuration(),
                source_method,
                source_column,
                target_method,
                target_column
            )

            method_suffix = source_method if source_method == "columns" else source_column
            output_file = self.data_adapter.get_full_path(
                self.data_paths['output'],
                f"{source_name}_{method_suffix}_{config_hash}.json"
            )

        # Check if file already exists with same configuration
        if self.data_adapter.file_exists(output_file):
            print(f"📋 Found existing results with same configuration: {output_file}")
            print("🔄 Loading cached results instead of reprocessing...")

            try:
                cached_results = self.data_adapter.read_json(output_file)

                # Verify the cached results have the expected structure
                if all(key in cached_results for key in ['exact_matches', 'fuzzy_matches', 'semantic_matches', 'summary']):
                    self.results = cached_results
                    print("✅ Successfully loaded cached results!")
                    return cached_results
                else:
                    print("⚠️ Cached file format invalid, reprocessing...")
            except Exception as e:
                print(f"⚠️ Error reading cached file, reprocessing: {e}")

        print(f"🆕 Processing new configuration, will save to: {output_file}")

        # Compile results with enhanced metadata
        results = {
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'semantic_matches': semantic_matches,
            'summary': {
                'total_exact_matches': len(exact_matches),
                'total_fuzzy_matches': len(fuzzy_matches),
                'total_semantic_matches': len(semantic_matches),
                'unique_source_fields': len(source_fields),
                'unique_target_items': len(target_items),
                'processing_timestamp': datetime.datetime.now().isoformat()
            },
            'source_info': {
                'dataset_name': source_name,
                'extraction_method': source_method,
                'extraction_column': source_column,
                'variables_extracted': len(source_fields),
                'dataset_shape': list(source_df.shape)
            },
            'target_info': {
                'dataset_name': target_name,
                'extraction_method': target_method,
                'extraction_column': target_column,
                'variables_extracted': len(target_items),
                'dataset_shape': list(target_df.shape)
            },
            'configuration': {
                'exact_matcher': self.exact_matcher.get_configuration(),
                'fuzzy_matcher': self.fuzzy_matcher.get_configuration(),
                'semantic_matcher': self.semantic_matcher.get_configuration()
            }
        }

        # Save results
        self.data_adapter.write_json(output_file, results)

        # Print summary
        print("\n" + "=" * 50)
        print("📊 PIPELINE SUMMARY:")
        print(f"  - Source: {source_name} ({source_method}" +
              (f" → {source_column}" if source_column else "") + ")")
        print(f"  - Target: {target_name} ({target_method} → {target_column})")
        print(f"  - Source fields extracted: {results['summary']['unique_source_fields']}")
        print(f"  - Target items extracted: {results['summary']['unique_target_items']}")
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