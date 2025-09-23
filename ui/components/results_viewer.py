"""
Results Viewer Component for CDE Matcher UI.

Handles display and interaction with matching results across all algorithm types.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional


class ResultsViewer:
    """Component for viewing and interacting with match results."""

    @staticmethod
    def render_overview_dashboard(results: Dict[str, Any]):
        """Render the main overview dashboard."""
        st.header("📊 Matching Results Overview")

        # Summary metrics
        summary = results['summary']
        total_matches = (summary['total_exact_matches'] +
                        summary['total_fuzzy_matches'] +
                        summary['total_semantic_matches'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;">
                <h3>{summary['unique_source_fields']}</h3>
                <p>Your Variables</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;">
                <h3>{summary['unique_target_items']}</h3>
                <p>DigiPath CDEs</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;">
                <h3>{total_matches}</h3>
                <p>Total Matches</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            coverage = (total_matches / summary['unique_source_fields'] * 100) if summary['unique_source_fields'] > 0 else 0
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;">
                <h3>{coverage:.1f}%</h3>
                <p>Coverage</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Visualizations
        col1, col2 = st.columns([1, 1])

        with col1:
            ResultsViewer._render_match_distribution_chart(results)

        with col2:
            ResultsViewer._render_confidence_distribution_chart(results)

        # Configuration summary
        ResultsViewer._render_configuration_summary(results)

    @staticmethod
    def _render_match_distribution_chart(results: Dict[str, Any]):
        """Render match distribution bar chart."""
        st.subheader("📈 Match Distribution")

        summary = results['summary']
        match_data = {
            'Match Type': ['Exact', 'Fuzzy', 'Semantic'],
            'Count': [
                summary['total_exact_matches'],
                summary['total_fuzzy_matches'],
                summary['total_semantic_matches']
            ]
        }

        fig = px.bar(
            match_data,
            x='Match Type',
            y='Count',
            color='Match Type',
            title="Matches by Algorithm Type",
            color_discrete_map={
                'Exact': '#28a745',
                'Fuzzy': '#ffc107',
                'Semantic': '#17a2b8'
            }
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, width='stretch')

    @staticmethod
    def _render_confidence_distribution_chart(results: Dict[str, Any]):
        """Render confidence distribution histogram."""
        st.subheader("🎯 Match Quality")

        if results['fuzzy_matches']:
            confidences = [match['confidence'] for match in results['fuzzy_matches']]

            fig = px.histogram(
                x=confidences,
                nbins=20,
                title="Fuzzy Match Confidence Distribution",
                labels={'x': 'Confidence Score', 'y': 'Count'},
                color_discrete_sequence=['#ffc107']
            )

            # Add median line
            median_conf = pd.Series(confidences).median()
            fig.add_vline(
                x=median_conf,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Median: {median_conf:.3f}"
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No fuzzy matches to display confidence distribution")

    @staticmethod
    def _render_configuration_summary(results: Dict[str, Any]):
        """Render configuration summary."""
        st.subheader("⚙️ Processing Configuration")

        if 'configuration' in results:
            config = results['configuration']

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Exact Matcher**")
                exact_config = config.get('exact_config', {})
                st.write(f"• Case sensitive: {exact_config.get('case_sensitive', 'N/A')}")

            with col2:
                st.write("**Fuzzy Matcher**")
                fuzzy_config = config.get('fuzzy_config', {})
                st.write(f"• Threshold: {fuzzy_config.get('threshold', 'N/A')}")
                st.write(f"• Algorithm: {fuzzy_config.get('algorithm', 'N/A')}")

            with col3:
                st.write("**Semantic Matcher**")
                semantic_config = config.get('semantic_config', {})
                st.write(f"• Case sensitive: {semantic_config.get('case_sensitive', 'N/A')}")
                st.write(f"• Exact only: {semantic_config.get('exact_only', 'N/A')}")

    @staticmethod
    def render_match_details(match_type: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Render detailed view for a specific match type with selection capability."""
        matches_key = f"{match_type.lower()}_matches"
        matches = results.get(matches_key, [])

        if not matches:
            st.info(f"No {match_type.lower()} matches found.")
            return []

        st.header(f"{match_type} Matches ({len(matches)} found)")

        # Apply filters
        filtered_matches = ResultsViewer._apply_match_filters(matches, match_type)

        # Display matches with selection
        selected_matches = ResultsViewer._render_interactive_match_table(filtered_matches, match_type)

        return selected_matches

    @staticmethod
    def _apply_match_filters(matches: List[Dict[str, Any]], match_type: str) -> List[Dict[str, Any]]:
        """Apply filters to match results."""
        col1, col2, col3 = st.columns(3)

        filtered_matches = matches.copy()

        with col1:
            if match_type == "Fuzzy":
                min_confidence = st.slider(
                    "Minimum Confidence",
                    min_value=0.0, max_value=1.0,
                    value=0.7, step=0.05,
                    key=f"{match_type}_confidence_filter"
                )
                filtered_matches = [m for m in filtered_matches if m['confidence'] >= min_confidence]

        with col2:
            search_term = st.text_input(
                "Search matches:",
                placeholder="Enter source or target name",
                key=f"{match_type}_search_filter"
            )
            if search_term:
                search_lower = search_term.lower()
                filtered_matches = [
                    m for m in filtered_matches
                    if search_lower in m['source_field'].lower() or
                       search_lower in m['target_item'].lower()
                ]

        with col3:
            st.write(f"**Showing {len(filtered_matches)} matches**")
            if len(filtered_matches) < len(matches):
                st.caption(f"(filtered from {len(matches)} total)")

        return filtered_matches

    @staticmethod
    def _render_interactive_match_table(matches: List[Dict[str, Any]], match_type: str) -> List[Dict[str, Any]]:
        """Render interactive match table with selection capability."""
        if not matches:
            return []

        # Convert matches to DataFrame with selection column
        df_data = []
        for i, match in enumerate(matches):
            # Create unique match ID
            match_id = f"{match['source_field']}_{match['target_item']}_{match['match_type']}"

            # Check if this match is already selected
            is_selected = any(
                selected['match_id'] == match_id
                for selected in st.session_state.get('selected_matches', [])
            )

            df_data.append({
                'Select': is_selected,
                'Variable': match['source_field'],
                'DigiPath CDE': match['target_item'],
                'Confidence': f"{match['confidence']:.3f}",
                'Match Type': match['match_type'],
                'match_id': match_id,
                'full_match': match
            })

        df = pd.DataFrame(df_data)

        # Interactive data editor
        edited_df = st.data_editor(
            df[['Select', 'Variable', 'DigiPath CDE', 'Confidence', 'Match Type']],
            column_config={
                "Select": st.column_config.CheckboxColumn("Select"),
                "Confidence": st.column_config.NumberColumn("Confidence", format="%.3f"),
            },
            width='stretch',
            hide_index=True,
            key=f"{match_type}_matches_editor"
        )

        # Update session state based on selections
        ResultsViewer._update_selected_matches(edited_df, df)

        # Show bulk selection options
        ResultsViewer._render_bulk_selection_options(matches, match_type)

        # Return currently selected matches for this type
        return [
            row['full_match'] for _, row in df.iterrows()
            if edited_df.iloc[_]['Select']
        ]

    @staticmethod
    def _update_selected_matches(edited_df: pd.DataFrame, original_df: pd.DataFrame):
        """Update session state with current selections."""
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = []

        # Get current selections
        current_selected = {}
        for idx, row in edited_df.iterrows():
            match_id = original_df.iloc[idx]['match_id']
            current_selected[match_id] = row['Select']

        # Update session state - remove deselected, add newly selected
        st.session_state.selected_matches = [
            match for match in st.session_state.selected_matches
            if match['match_id'] not in current_selected or current_selected[match['match_id']]
        ]

        # Add newly selected matches
        for idx, row in original_df.iterrows():
            match_id = row['match_id']
            if current_selected.get(match_id, False):
                # Check if not already in selected matches
                if not any(match['match_id'] == match_id for match in st.session_state.selected_matches):
                    st.session_state.selected_matches.append({
                        'match_id': match_id,
                        'variable': row['full_match']['source_field'],
                        'cde': row['full_match']['target_item'],
                        'confidence': row['full_match']['confidence'],
                        'match_type': row['full_match']['match_type'],
                        'full_match': row['full_match']
                    })

    @staticmethod
    def _render_bulk_selection_options(matches: List[Dict[str, Any]], match_type: str):
        """Render bulk selection action buttons."""
        st.divider()
        st.subheader("🎛️ Bulk Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"✅ Select All {match_type}", key=f"select_all_{match_type}"):
                ResultsViewer._bulk_select_matches(matches, True)

        with col2:
            if st.button(f"❌ Deselect All {match_type}", key=f"deselect_all_{match_type}"):
                ResultsViewer._bulk_select_matches(matches, False)

        with col3:
            if match_type == "Fuzzy" and st.button("⭐ Select High Confidence", key=f"select_high_conf_{match_type}"):
                high_conf_matches = [m for m in matches if m['confidence'] >= 0.8]
                ResultsViewer._bulk_select_matches(high_conf_matches, True)

        with col4:
            selected_count = len([m for m in matches if ResultsViewer._is_match_selected(m)])
            st.metric("Selected", selected_count)

    @staticmethod
    def _bulk_select_matches(matches: List[Dict[str, Any]], select: bool):
        """Bulk select or deselect matches."""
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = []

        for match in matches:
            match_id = f"{match['source_field']}_{match['target_item']}_{match['match_type']}"

            # Remove if exists
            st.session_state.selected_matches = [
                m for m in st.session_state.selected_matches if m['match_id'] != match_id
            ]

            # Add if selecting
            if select:
                st.session_state.selected_matches.append({
                    'match_id': match_id,
                    'variable': match['source_field'],
                    'cde': match['target_item'],
                    'confidence': match['confidence'],
                    'match_type': match['match_type'],
                    'full_match': match
                })

        st.rerun()

    @staticmethod
    def _is_match_selected(match: Dict[str, Any]) -> bool:
        """Check if a match is currently selected."""
        match_id = f"{match['source_field']}_{match['target_item']}_{match['match_type']}"
        return any(
            selected['match_id'] == match_id
            for selected in st.session_state.get('selected_matches', [])
        )

    @staticmethod
    def render_analytics_dashboard(results: Dict[str, Any]):
        """Render advanced analytics dashboard."""
        st.header("📈 Analytics Dashboard")

        # Algorithm performance comparison
        st.subheader("🏆 Algorithm Performance Comparison")
        ResultsViewer._render_algorithm_comparison(results)

        # Match quality analysis
        st.subheader("💎 Match Quality Analysis")
        ResultsViewer._render_quality_analysis(results)

        # Coverage analysis
        st.subheader("📊 Coverage Analysis")
        ResultsViewer._render_coverage_analysis(results)

    @staticmethod
    def _render_algorithm_comparison(results: Dict[str, Any]):
        """Render algorithm performance comparison chart."""
        algorithms = []
        counts = []
        avg_confidences = []

        for match_type in ['exact', 'fuzzy', 'semantic']:
            matches = results.get(f"{match_type}_matches", [])
            algorithms.append(match_type.title())
            counts.append(len(matches))

            if matches:
                confidences = [m['confidence'] for m in matches]
                avg_confidences.append(sum(confidences) / len(confidences))
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
    def _render_quality_analysis(results: Dict[str, Any]):
        """Render match quality analysis."""
        col1, col2 = st.columns(2)

        with col1:
            # Confidence ranges for fuzzy matches
            if results.get('fuzzy_matches'):
                confidences = [m['confidence'] for m in results['fuzzy_matches']]
                ranges = {
                    'High (≥0.8)': sum(1 for c in confidences if c >= 0.8),
                    'Medium (0.6-0.8)': sum(1 for c in confidences if 0.6 <= c < 0.8),
                    'Low (<0.6)': sum(1 for c in confidences if c < 0.6)
                }

                fig = px.pie(
                    values=list(ranges.values()),
                    names=list(ranges.keys()),
                    title="Fuzzy Match Quality Distribution"
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No fuzzy matches for quality analysis")

        with col2:
            # Match type distribution
            summary = results['summary']
            match_counts = {
                'Exact': summary['total_exact_matches'],
                'Fuzzy': summary['total_fuzzy_matches'],
                'Semantic': summary['total_semantic_matches']
            }

            fig = px.pie(
                values=list(match_counts.values()),
                names=list(match_counts.keys()),
                title="Match Type Distribution"
            )
            st.plotly_chart(fig, width='stretch')

    @staticmethod
    def _render_coverage_analysis(results: Dict[str, Any]):
        """Render coverage analysis."""
        summary = results['summary']
        source_fields = summary['unique_source_fields']
        total_matches = (summary['total_exact_matches'] +
                        summary['total_fuzzy_matches'] +
                        summary['total_semantic_matches'])

        matched_fields = total_matches  # Assuming unique matches
        unmatched_fields = source_fields - matched_fields

        coverage_data = {
            'Status': ['Matched', 'Unmatched'],
            'Count': [matched_fields, unmatched_fields]
        }

        fig = px.bar(
            coverage_data,
            x='Status',
            y='Count',
            title=f"Field Coverage ({matched_fields}/{source_fields} = {(matched_fields/source_fields*100):.1f}%)",
            color='Status',
            color_discrete_map={'Matched': '#28a745', 'Unmatched': '#dc3545'}
        )

        st.plotly_chart(fig, width='stretch')