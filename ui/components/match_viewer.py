"""
Match Viewer Components for Streamlit UI.

Reusable components for displaying and interacting with CDE matching results.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional


class MatchViewer:
    """Component for viewing and interacting with match results."""

    @staticmethod
    def render_match_card(match: Dict[str, Any], index: int = 0, show_details: bool = True) -> None:
        """
        Render a single match as a styled card.

        Args:
            match: Match dictionary with source_field, target_item, confidence, etc.
            index: Unique index for the match (for button keys)
            show_details: Whether to show expandable details section
        """
        confidence = match['confidence']

        # Determine confidence styling
        if confidence >= 0.9:
            conf_color = "#28a745"  # Green
            conf_emoji = "🟢"
        elif confidence >= 0.7:
            conf_color = "#ffc107"  # Yellow
            conf_emoji = "🟡"
        else:
            conf_color = "#dc3545"  # Red
            conf_emoji = "🔴"

        # Create columns for layout
        col1, col2, col3 = st.columns([3, 3, 1])

        with col1:
            st.markdown(f"**Source:** <span style='color: #1f77b4; background-color: #f0f8ff; padding: 2px 6px; border-radius: 3px; font-family: monospace;'>{match['source_field']}</span>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"**Target:** <span style='color: #ff7f0e; background-color: #fff5e6; padding: 2px 6px; border-radius: 3px; font-family: monospace;'>{match['target_item']}</span>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"<span style='color: {conf_color}; font-weight: bold;'>{conf_emoji} {confidence:.3f}</span>", unsafe_allow_html=True)

        # Show match type and details
        if show_details:
            details_col1, details_col2 = st.columns([2, 1])

            with details_col1:
                st.markdown(f"<small style='color: #666666; font-style: italic;'>Match type: <strong>{match['match_type']}</strong></small>", unsafe_allow_html=True)

            with details_col2:
                if st.button("📋 Details", key=f"details_{index}"):
                    with st.expander("Match Metadata", expanded=True):
                        st.json(match.get('metadata', {}))

        st.divider()

    @staticmethod
    def render_confidence_distribution(matches: List[Dict[str, Any]], title: str = "Confidence Distribution") -> None:
        """
        Render a confidence score distribution chart.

        Args:
            matches: List of match dictionaries
            title: Chart title
        """
        if not matches:
            st.info("No matches to display")
            return

        confidences = [match['confidence'] for match in matches]

        # Create histogram
        fig = px.histogram(
            x=confidences,
            nbins=20,
            title=title,
            labels={'x': 'Confidence Score', 'y': 'Number of Matches'},
            color_discrete_sequence=['#667eea']
        )

        # Add median line
        median_conf = pd.Series(confidences).median()
        fig.add_vline(
            x=median_conf,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Median: {median_conf:.3f}"
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, width='stretch')

    @staticmethod
    def render_match_summary_table(results: Dict[str, Any]) -> None:
        """
        Render a summary table of all match types.

        Args:
            results: Complete results dictionary from pipeline
        """
        summary_data = []

        # Collect summary statistics
        for match_type in ['exact', 'fuzzy', 'semantic']:
            matches = results.get(f"{match_type}_matches", [])
            if matches:
                confidences = [m['confidence'] for m in matches]
                summary_data.append({
                    'Match Type': match_type.title(),
                    'Count': len(matches),
                    'Avg Confidence': f"{pd.Series(confidences).mean():.3f}",
                    'Min Confidence': f"{min(confidences):.3f}",
                    'Max Confidence': f"{max(confidences):.3f}"
                })
            else:
                summary_data.append({
                    'Match Type': match_type.title(),
                    'Count': 0,
                    'Avg Confidence': 'N/A',
                    'Min Confidence': 'N/A',
                    'Max Confidence': 'N/A'
                })

        # Display as table
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True, width='stretch')

    @staticmethod
    def render_coverage_metrics(results: Dict[str, Any]) -> None:
        """
        Render coverage and matching metrics.

        Args:
            results: Complete results dictionary from pipeline
        """
        summary = results['summary']

        total_matches = (
            summary['total_exact_matches'] +
            summary['total_fuzzy_matches'] +
            summary['total_semantic_matches']
        )

        source_fields = summary['unique_source_fields']
        coverage_pct = (total_matches / source_fields * 100) if source_fields > 0 else 0

        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📊 Total Fields",
                value=source_fields
            )

        with col2:
            st.metric(
                label="✅ Matched Fields",
                value=total_matches
            )

        with col3:
            st.metric(
                label="📈 Coverage",
                value=f"{coverage_pct:.1f}%"
            )

        with col4:
            unmatched = source_fields - total_matches
            st.metric(
                label="❓ Unmatched",
                value=unmatched,
                delta=f"-{unmatched}" if unmatched > 0 else "Perfect!"
            )

    @staticmethod
    def render_algorithm_comparison(results: Dict[str, Any]) -> None:
        """
        Render a comparison chart of algorithm performance.

        Args:
            results: Complete results dictionary from pipeline
        """
        # Prepare data for comparison
        algorithms = []
        counts = []
        avg_confidences = []

        for match_type in ['exact', 'fuzzy', 'semantic']:
            matches = results.get(f"{match_type}_matches", [])
            algorithms.append(match_type.title())
            counts.append(len(matches))

            if matches:
                confidences = [m['confidence'] for m in matches]
                avg_confidences.append(pd.Series(confidences).mean())
            else:
                avg_confidences.append(0)

        # Create subplot with dual y-axis
        fig = go.Figure()

        # Add bar chart for counts
        fig.add_trace(go.Bar(
            name='Match Count',
            x=algorithms,
            y=counts,
            yaxis='y',
            marker_color=['#28a745', '#ffc107', '#17a2b8']
        ))

        # Add line chart for average confidence
        fig.add_trace(go.Scatter(
            name='Avg Confidence',
            x=algorithms,
            y=avg_confidences,
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=10)
        ))

        # Update layout with dual y-axis
        fig.update_layout(
            title='Algorithm Performance Comparison',
            xaxis=dict(title='Algorithm'),
            yaxis=dict(title='Number of Matches', side='left'),
            yaxis2=dict(
                title='Average Confidence',
                side='right',
                overlaying='y',
                range=[0, 1]
            ),
            legend=dict(x=0.02, y=0.98),
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    @staticmethod
    def render_match_filters(matches: List[Dict[str, Any]], match_type: str) -> tuple:
        """
        Render filter controls for match results.

        Args:
            matches: List of match dictionaries
            match_type: Type of matches being filtered

        Returns:
            Tuple of (filtered_matches, filters_applied)
        """
        if not matches:
            return matches, {}

        st.subheader("🔍 Filters")

        col1, col2, col3 = st.columns(3)

        filters_applied = {}

        with col1:
            # Confidence filter (for fuzzy matches)
            if match_type.lower() == 'fuzzy':
                min_conf = st.slider(
                    "Minimum Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    key=f"{match_type}_conf_filter"
                )
                filters_applied['min_confidence'] = min_conf
                matches = [m for m in matches if m['confidence'] >= min_conf]

        with col2:
            # Search filter
            search_term = st.text_input(
                "Search matches",
                placeholder="Enter source or target name",
                key=f"{match_type}_search"
            )
            if search_term:
                search_lower = search_term.lower()
                filters_applied['search_term'] = search_term
                matches = [
                    m for m in matches
                    if search_lower in m['source_field'].lower() or
                       search_lower in m['target_item'].lower()
                ]

        with col3:
            # Results limit
            max_results = st.selectbox(
                "Max Results",
                options=[10, 25, 50, 100, 'All'],
                index=2,  # Default to 50
                key=f"{match_type}_limit"
            )
            if max_results != 'All':
                filters_applied['max_results'] = max_results
                matches = matches[:max_results]

        # Show filter summary
        if filters_applied:
            filter_summary = ", ".join([f"{k}: {v}" for k, v in filters_applied.items()])
            st.caption(f"Filters applied: {filter_summary}")

        st.markdown(f"**Showing {len(matches)} matches**")
        st.divider()

        return matches, filters_applied


class ConfigurationPanel:
    """Component for matcher configuration controls."""

    @staticmethod
    def render_exact_config() -> Dict[str, Any]:
        """Render exact matcher configuration controls."""
        st.subheader("🎯 Exact Matcher")

        case_sensitive = st.checkbox(
            "Case Sensitive Matching",
            value=False,
            help="Enable case-sensitive exact string matching"
        )

        return {'case_sensitive': case_sensitive}

    @staticmethod
    def render_fuzzy_config() -> Dict[str, Any]:
        """Render fuzzy matcher configuration controls."""
        st.subheader("🔍 Fuzzy Matcher")

        threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0, max_value=1.0,
            value=0.7, step=0.05,
            help="Minimum similarity score to consider a match"
        )

        algorithm = st.selectbox(
            "Matching Algorithm",
            options=['ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'],
            index=2,  # Default to token_sort_ratio
            help="Choose the fuzzy matching algorithm"
        )

        # Algorithm help
        with st.expander("ℹ️ Algorithm Details"):
            st.markdown("""
            - **ratio**: Basic Levenshtein distance ratio
            - **partial_ratio**: Best partial substring match
            - **token_sort_ratio**: Ratio after sorting words
            - **token_set_ratio**: Ratio after set operations on words
            """)

        case_sensitive = st.checkbox(
            "Case Sensitive",
            value=False,
            key="fuzzy_case"
        )

        max_results = st.number_input(
            "Max Results per Field",
            min_value=1, max_value=50,
            value=10,
            help="Maximum number of matches to return per source field"
        )

        return {
            'threshold': threshold,
            'algorithm': algorithm,
            'case_sensitive': case_sensitive,
            'max_results': max_results
        }

    @staticmethod
    def render_semantic_config() -> Dict[str, Any]:
        """Render semantic matcher configuration controls."""
        st.subheader("🧠 Semantic Matcher")

        exact_only = st.checkbox(
            "Exact Semantic Matches Only",
            value=False,
            help="Only return exact concept matches, not partial ones"
        )

        case_sensitive = st.checkbox(
            "Case Sensitive",
            value=False,
            key="semantic_case"
        )

        # Show available concepts
        with st.expander("📋 Available Concepts"):
            st.markdown("""
            Built-in biomedical concepts include:
            - Patient identifiers (donor_id, participant_id, subject_id)
            - Demographics (age, sex, race, education)
            - Clinical measures (MMSE, CASI, cognitive status)
            - Pathology (Braak, Thal, CERAD scores)
            - Genetics (APOE genotype)
            - And many more...
            """)

        return {
            'case_sensitive': case_sensitive,
            'exact_only': exact_only
        }


class DataPreview:
    """Component for data preview and validation."""

    @staticmethod
    def render_csv_preview(df: pd.DataFrame, title: str, max_rows: int = 10) -> None:
        """
        Render a preview of uploaded CSV data.

        Args:
            df: DataFrame to preview
            title: Title for the preview section
            max_rows: Maximum number of rows to show
        """
        st.subheader(title)

        # Basic info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Rows", df.shape[0])

        with col2:
            st.metric("Columns", df.shape[1])

        with col3:
            memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("Memory", f"{memory_mb:.1f} MB")

        # Data preview
        with st.expander("📊 Data Preview", expanded=True):
            st.dataframe(df.head(max_rows), width='stretch')

        # Column info
        with st.expander("📋 Column Information"):
            col_info = []
            for col in df.columns:
                col_info.append({
                    'Column': col,
                    'Type': str(df[col].dtype),
                    'Non-null': df[col].notna().sum(),
                    'Null %': f"{(df[col].isna().sum() / len(df) * 100):.1f}%"
                })

            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, hide_index=True, width='stretch')