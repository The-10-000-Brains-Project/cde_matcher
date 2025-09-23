"""
Matcher Configuration Component for CDE Matcher UI.

Handles configuration of exact, fuzzy, and semantic matching algorithms.
"""

import streamlit as st
from typing import Dict, Any


class MatcherConfig:
    """Component for configuring matcher algorithms."""

    @staticmethod
    def get_default_config() -> Dict[str, Dict[str, Any]]:
        """Get default configuration for all matchers."""
        return {
            'exact': {
                'case_sensitive': False
            },
            'fuzzy': {
                'threshold': 0.7,
                'algorithm': 'token_sort_ratio'
            },
            'semantic': {
                'case_sensitive': False,
                'exact_only': False
            }
        }

    @staticmethod
    def initialize_session_config():
        """Initialize matcher configuration in session state."""
        if 'matcher_config' not in st.session_state:
            st.session_state.matcher_config = MatcherConfig.get_default_config()

    @staticmethod
    def render_exact_matcher_config() -> Dict[str, Any]:
        """Render exact matcher configuration panel."""
        with st.expander("🎯 Exact Matcher", expanded=False):
            st.markdown("""
            **Exact string matching** - finds identical matches with optional case sensitivity.

            Best for: Field names that are identical or differ only in case.
            """)

            case_sensitive = st.checkbox(
                "Case Sensitive",
                value=st.session_state.matcher_config['exact']['case_sensitive'],
                key="exact_case_sensitive",
                help="Enable case-sensitive exact string matching"
            )
            st.session_state.matcher_config['exact']['case_sensitive'] = case_sensitive

            # Show example
            with st.expander("💡 Examples"):
                if case_sensitive:
                    st.code("'Age' matches 'Age' but NOT 'age' or 'AGE'")
                else:
                    st.code("'Age' matches 'age', 'AGE', 'Age'")

        return st.session_state.matcher_config['exact']

    @staticmethod
    def render_fuzzy_matcher_config() -> Dict[str, Any]:
        """Render fuzzy matcher configuration panel."""
        with st.expander("🔍 Fuzzy Matcher", expanded=False):
            st.markdown("""
            **Fuzzy string matching** - finds similar strings using edit distance algorithms.

            Best for: Field names that are similar but not identical (typos, abbreviations).
            """)

            threshold = st.slider(
                "Similarity Threshold",
                min_value=0.0, max_value=1.0,
                value=st.session_state.matcher_config['fuzzy']['threshold'],
                step=0.05,
                key="fuzzy_threshold",
                help="Minimum similarity score to consider a match (0.0 = any similarity, 1.0 = exact match)"
            )

            algorithm = st.selectbox(
                "Algorithm",
                options=['ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'],
                index=['ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'].index(
                    st.session_state.matcher_config['fuzzy']['algorithm']
                ),
                key="fuzzy_algorithm",
                help="Choose the fuzzy matching algorithm"
            )

            # Algorithm explanations
            with st.expander("📚 Algorithm Details"):
                st.markdown("""
                - **ratio**: Basic Levenshtein distance ratio
                  - Good for: Overall string similarity
                  - Example: 'age_at_death' vs 'age_death' → High score

                - **partial_ratio**: Best partial substring match
                  - Good for: One string contained in another
                  - Example: 'age' vs 'age_at_death' → High score

                - **token_sort_ratio**: Ratio after sorting words
                  - Good for: Different word order
                  - Example: 'death_age' vs 'age_death' → High score

                - **token_set_ratio**: Set operations on words
                  - Good for: Extra/missing words
                  - Example: 'age_at_death' vs 'age_death_years' → High score
                """)

            # Show example based on threshold
            with st.expander("💡 Examples with Current Settings"):
                if algorithm == 'ratio':
                    example_pairs = [
                        ("'age_at_death'", "'age_death'", 0.85),
                        ("'subject_id'", "'participant_id'", 0.42),
                        ("'mmse_score'", "'mmse'", 0.73)
                    ]
                elif algorithm == 'token_sort_ratio':
                    example_pairs = [
                        ("'age_at_death'", "'death_age'", 0.92),
                        ("'subject_id'", "'id_subject'", 0.89),
                        ("'cognitive_score'", "'score_cognitive'", 0.95)
                    ]
                else:
                    example_pairs = [
                        ("'age_at_death'", "'age_death'", 0.87),
                        ("'subject_id'", "'participant_id'", 0.45),
                        ("'mmse_total'", "'mmse'", 0.76)
                    ]

                for src, tgt, score in example_pairs:
                    color = "🟢" if score >= threshold else "🔴"
                    st.write(f"{color} {src} ↔ {tgt} = {score:.2f}")

            st.session_state.matcher_config['fuzzy']['threshold'] = threshold
            st.session_state.matcher_config['fuzzy']['algorithm'] = algorithm

        return st.session_state.matcher_config['fuzzy']

    @staticmethod
    def render_semantic_matcher_config() -> Dict[str, Any]:
        """Render semantic matcher configuration panel."""
        with st.expander("🧠 Semantic Matcher", expanded=False):
            st.markdown("""
            **Semantic matching** - finds conceptually related terms using domain knowledge.

            Best for: Different terms that refer to the same concept.
            """)

            case_sensitive = st.checkbox(
                "Case Sensitive",
                value=st.session_state.matcher_config['semantic']['case_sensitive'],
                key="semantic_case_sensitive",
                help="Enable case-sensitive semantic matching"
            )

            exact_only = st.checkbox(
                "Exact Semantic Only",
                value=st.session_state.matcher_config['semantic']['exact_only'],
                key="semantic_exact_only",
                help="Only return exact concept matches, not partial ones"
            )

            st.session_state.matcher_config['semantic']['case_sensitive'] = case_sensitive
            st.session_state.matcher_config['semantic']['exact_only'] = exact_only

            # Show available concepts
            with st.expander("📋 Available Semantic Concepts"):
                st.markdown("""
                Built-in biomedical concept mappings include:

                **Patient Identifiers:**
                - `donor_id`, `participant_id`, `subject_id`, `patient_id`

                **Demographics:**
                - `age_at_death`, `sex`, `gender`, `race`, `ethnicity`, `education`

                **Clinical Measures:**
                - `MMSE`, `CASI`, `cognitive_status`, `dementia_diagnosis`

                **Pathology Scores:**
                - `Braak`, `Thal`, `CERAD`, `ABC_score`

                **Genetics:**
                - `APOE_genotype`, `APOE4_status`

                **And many more biomedical concepts...**
                """)

            # Show examples
            with st.expander("💡 Semantic Matching Examples"):
                examples = [
                    ("'donor_id'", "['subject_id', 'participant_id', 'patient_id']"),
                    ("'age_death'", "['age_at_death', 'death_age']"),
                    ("'mmse_total'", "['MMSE', 'mini_mental_state']"),
                    ("'apoe_status'", "['APOE_genotype', 'APOE4_status']")
                ]

                for source, targets in examples:
                    st.write(f"🔗 {source} → {targets}")

        return st.session_state.matcher_config['semantic']

    @staticmethod
    def render_configuration_summary() -> Dict[str, Dict[str, Any]]:
        """Render a summary of current configuration."""
        with st.expander("⚙️ Current Configuration Summary"):
            config = st.session_state.matcher_config

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Exact Matcher**")
                st.write(f"• Case sensitive: {config['exact']['case_sensitive']}")

            with col2:
                st.write("**Fuzzy Matcher**")
                st.write(f"• Threshold: {config['fuzzy']['threshold']}")
                st.write(f"• Algorithm: {config['fuzzy']['algorithm']}")

            with col3:
                st.write("**Semantic Matcher**")
                st.write(f"• Case sensitive: {config['semantic']['case_sensitive']}")
                st.write(f"• Exact only: {config['semantic']['exact_only']}")

        return config

    @staticmethod
    def render_matcher_configuration() -> Dict[str, Dict[str, Any]]:
        """Render complete matcher configuration interface."""
        st.subheader("⚙️ Matcher Configuration")

        # Initialize config if needed
        MatcherConfig.initialize_session_config()

        # Render individual matcher configs
        exact_config = MatcherConfig.render_exact_matcher_config()
        fuzzy_config = MatcherConfig.render_fuzzy_matcher_config()
        semantic_config = MatcherConfig.render_semantic_matcher_config()

        # Show summary
        all_config = MatcherConfig.render_configuration_summary()

        return all_config

    @staticmethod
    def reset_to_defaults():
        """Reset configuration to defaults."""
        st.session_state.matcher_config = MatcherConfig.get_default_config()
        st.rerun()

    @staticmethod
    def render_config_actions():
        """Render configuration action buttons."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Reset to Defaults", help="Reset all matcher settings to default values"):
                MatcherConfig.reset_to_defaults()

        with col2:
            if st.button("💾 Save Configuration", help="Save current configuration (feature coming soon)"):
                st.info("Configuration saving feature coming soon!")