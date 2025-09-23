"""
Report Builder Component for CDE Matcher UI.

Handles manual report creation, conflict resolution, and export functionality.
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Any, Tuple


class ReportBuilder:
    """Component for building and managing manual reports."""

    @staticmethod
    def render_manual_report_page():
        """Render the complete manual report building page."""
        st.header("📝 Manual Report Builder")

        # Check if we have any selected matches
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = []

        total_selected = len(st.session_state.selected_matches)

        if total_selected == 0:
            ReportBuilder._render_empty_report_message()
            return

        # Show selection summary
        ReportBuilder._render_selection_summary()

        # Check for conflicts and handle resolution
        conflicts = ReportBuilder._detect_conflicts()
        if conflicts:
            ReportBuilder._render_conflict_resolution(conflicts)

        # Show final report
        ReportBuilder._render_final_report(conflicts)

    @staticmethod
    def _render_empty_report_message():
        """Render message when no matches are selected."""
        st.info("🔍 **No matches selected yet**")
        st.markdown("""
        **To build your report:**
        1. Navigate to the match type tabs (Exact, Fuzzy, Semantic)
        2. Use the checkboxes or selection buttons to choose matches
        3. Return here to review and download your report

        **Tips:**
        - Use bulk selection buttons for efficiency
        - Higher confidence scores generally indicate better matches
        - Semantic matches may capture conceptual relationships exact/fuzzy miss
        """)

    @staticmethod
    def _render_selection_summary():
        """Render summary of current selections."""
        st.subheader("📊 Selection Summary")

        selected_matches = st.session_state.selected_matches
        total_selected = len(selected_matches)

        # Count by match type
        exact_count = len([s for s in selected_matches if s['match_type'] == 'exact'])
        fuzzy_count = len([s for s in selected_matches if s['match_type'] == 'fuzzy'])
        semantic_count = len([s for s in selected_matches if s['match_type'] == 'semantic'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🎯 Exact", exact_count)
        with col2:
            st.metric("🔍 Fuzzy", fuzzy_count)
        with col3:
            st.metric("🧠 Semantic", semantic_count)
        with col4:
            st.metric("📋 Total", total_selected)

        # Show average confidence
        if selected_matches:
            avg_confidence = sum(match['confidence'] for match in selected_matches) / len(selected_matches)
            st.info(f"📈 Average confidence score: {avg_confidence:.3f}")

    @staticmethod
    def _detect_conflicts() -> List[str]:
        """Detect variables mapped to multiple CDEs."""
        variable_mappings = {}
        conflicts = []

        for match in st.session_state.selected_matches:
            var = match['variable']
            cde = match['cde']

            if var in variable_mappings:
                if variable_mappings[var] != cde:
                    if var not in conflicts:
                        conflicts.append(var)
            else:
                variable_mappings[var] = cde

        return conflicts

    @staticmethod
    def _render_conflict_resolution(conflicts: List[str]):
        """Render conflict resolution interface."""
        st.subheader("⚠️ Conflict Resolution")
        st.warning(f"**{len(conflicts)} variables are mapped to multiple CDEs** - Please resolve before exporting")

        with st.expander("🔍 Resolve Conflicts", expanded=True):
            for var in conflicts:
                st.write(f"**Variable: `{var}`**")
                conflicting_matches = [s for s in st.session_state.selected_matches if s['variable'] == var]

                # Sort by confidence (highest first)
                conflicting_matches.sort(key=lambda x: x['confidence'], reverse=True)

                st.write("Choose which mapping to keep:")

                for i, match in enumerate(conflicting_matches):
                    col1, col2, col3, col4 = st.columns([4, 2, 1, 1])

                    with col1:
                        confidence_color = "🟢" if match['confidence'] >= 0.8 else "🟡" if match['confidence'] >= 0.6 else "🔴"
                        st.write(f"  {confidence_color} **{match['cde']}**")

                    with col2:
                        st.write(f"Conf: {match['confidence']:.3f} ({match['match_type']})")

                    with col3:
                        if st.button("✅ Keep", key=f"keep_{match['match_id']}", help="Keep this mapping and remove others"):
                            ReportBuilder._resolve_conflict_keep(var, match['match_id'])

                    with col4:
                        if st.button("❌ Remove", key=f"remove_{match['match_id']}", help="Remove this mapping"):
                            ReportBuilder._resolve_conflict_remove(match['match_id'])

                st.divider()

    @staticmethod
    def _resolve_conflict_keep(variable: str, keep_match_id: str):
        """Keep one match and remove others for the same variable."""
        st.session_state.selected_matches = [
            match for match in st.session_state.selected_matches
            if not (match['variable'] == variable and match['match_id'] != keep_match_id)
        ]
        st.rerun()

    @staticmethod
    def _resolve_conflict_remove(match_id: str):
        """Remove a specific match."""
        st.session_state.selected_matches = [
            match for match in st.session_state.selected_matches
            if match['match_id'] != match_id
        ]
        st.rerun()

    @staticmethod
    def _render_final_report(conflicts: List[str]):
        """Render the final report table and export options."""
        st.subheader("📝 Final Report Data")

        # Create clean report data (excluding conflicts)
        report_data = []
        for match in st.session_state.selected_matches:
            # Skip variables that still have conflicts
            if match['variable'] not in conflicts:
                report_data.append({
                    'CDE': match['cde'],
                    'Variable': match['variable'],
                    'Confidence': match['confidence'],
                    'Match Type': match['match_type']
                })

        if not report_data:
            if conflicts:
                st.warning("⚠️ No valid mappings after conflict resolution. Please resolve conflicts above.")
            else:
                st.info("No mappings available for export.")
            return

        # Sort by CDE name for consistency
        report_df = pd.DataFrame(report_data).sort_values('CDE')

        # Show summary
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{len(report_df)} mappings ready for export**")
        with col2:
            if conflicts:
                st.warning(f"{len(conflicts)} conflicts remaining")

        # Editable table for final adjustments
        edited_report = st.data_editor(
            report_df,
            width='stretch',
            hide_index=True,
            column_config={
                "CDE": st.column_config.TextColumn(
                    "CDE",
                    help="DigiPath Common Data Element name",
                    required=True
                ),
                "Variable": st.column_config.TextColumn(
                    "Variable",
                    help="Source variable name",
                    required=True
                ),
                "Confidence": st.column_config.NumberColumn(
                    "Confidence",
                    help="Match confidence score (read-only)",
                    format="%.3f",
                    disabled=True
                ),
                "Match Type": st.column_config.SelectboxColumn(
                    "Match Type",
                    help="Type of matching algorithm",
                    options=["exact", "fuzzy", "semantic"],
                    disabled=True
                )
            },
            key="report_editor"
        )

        # Management and export buttons
        ReportBuilder._render_report_actions(edited_report, conflicts)

    @staticmethod
    def _render_report_actions(edited_report: pd.DataFrame, conflicts: List[str]):
        """Render action buttons for the report."""
        st.divider()
        st.subheader("🎛️ Report Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Clear All Selections", help="Remove all selected matches"):
                st.session_state.selected_matches = []
                st.rerun()

        with col2:
            if st.button("🔄 Refresh Report", help="Reload report data"):
                st.rerun()

        with col3:
            export_enabled = len(edited_report) > 0 and len(conflicts) == 0
            if st.button("📥 Export Report", disabled=not export_enabled, help="Export as CSV (resolve conflicts first)"):
                ReportBuilder._export_report_csv(edited_report)

        # Show final preview
        if len(conflicts) == 0 and len(edited_report) > 0:
            st.subheader("📋 Final Export Preview")
            st.markdown("**This is exactly what will be exported:**")
            st.dataframe(
                edited_report[['CDE', 'Variable']],
                width='stretch',
                hide_index=True
            )

    @staticmethod
    def _export_report_csv(report_df: pd.DataFrame):
        """Export the report as CSV."""
        # Create final CSV with just CDE and Variable columns
        export_df = report_df[['CDE', 'Variable']].copy()

        # Generate filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cde_manual_report_{timestamp}.csv"

        # Convert to CSV
        csv_data = export_df.to_csv(index=False)

        # Provide download
        st.download_button(
            label="💾 Download CSV Report",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help="Download the final 2-column CSV report"
        )

        st.success(f"✅ Report ready for download: {len(export_df)} mappings in {filename}")

    @staticmethod
    def render_export_page(results: Dict[str, Any]):
        """Render comprehensive export options page."""
        st.header("💾 Export Results")

        if not results:
            st.warning("No results available to export.")
            return

        # Export options
        col1, col2 = st.columns(2)

        with col1:
            ReportBuilder._render_full_results_export(results)

        with col2:
            ReportBuilder._render_manual_report_export()

    @staticmethod
    def _render_full_results_export(results: Dict[str, Any]):
        """Render full results export options."""
        st.subheader("📄 Full Results Export")

        # JSON export
        if st.button("📋 Download Complete Results (JSON)", type="primary"):
            json_str = json.dumps(results, indent=2)

            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cde_matching_results_{timestamp}.json"

            st.download_button(
                label="💾 Download JSON",
                data=json_str,
                file_name=filename,
                mime="application/json",
                help="Download complete results with all matches and metadata"
            )

        # All matches CSV export
        if st.button("📊 Download All Matches (CSV)"):
            all_matches_df = ReportBuilder._create_all_matches_dataframe(results)

            if not all_matches_df.empty:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cde_all_matches_{timestamp}.csv"

                csv_data = all_matches_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    help="Download all matches from all algorithms"
                )
            else:
                st.warning("No matches found to export")

        # Summary statistics
        ReportBuilder._render_export_summary(results)

    @staticmethod
    def _render_manual_report_export():
        """Render manual report export section."""
        st.subheader("📝 Manual Report Export")

        selected_count = len(st.session_state.get('selected_matches', []))
        conflicts = ReportBuilder._detect_conflicts()

        if selected_count == 0:
            st.info("No matches selected for manual report")
        elif conflicts:
            st.warning(f"Resolve {len(conflicts)} conflicts before exporting manual report")
        else:
            st.success(f"Manual report ready: {selected_count} mappings")

        if st.button("📝 Go to Manual Report Builder"):
            # This would typically navigate to the manual report page
            st.info("Navigate to 'Manual Report' in the sidebar to build your custom report")

    @staticmethod
    def _create_all_matches_dataframe(results: Dict[str, Any]) -> pd.DataFrame:
        """Create DataFrame with all matches from all algorithms."""
        all_matches = []

        for match_type in ['exact', 'fuzzy', 'semantic']:
            matches = results.get(f"{match_type}_matches", [])
            for match in matches:
                all_matches.append({
                    'Variable Name': match['source_field'],
                    'DigiPath CDE': match['target_item'],
                    'Confidence': match['confidence'],
                    'Match Type': match['match_type'],
                    'Algorithm': match_type.title()
                })

        return pd.DataFrame(all_matches) if all_matches else pd.DataFrame()

    @staticmethod
    def _render_export_summary(results: Dict[str, Any]):
        """Render export summary statistics."""
        st.subheader("📊 Export Summary")

        summary = results.get('summary', {})

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Variables", summary.get('unique_source_fields', 0))
            st.metric("Total Matches",
                     summary.get('total_exact_matches', 0) +
                     summary.get('total_fuzzy_matches', 0) +
                     summary.get('total_semantic_matches', 0))

        with col2:
            st.metric("Target CDEs", summary.get('unique_target_items', 0))
            coverage = 0
            if summary.get('unique_source_fields', 0) > 0:
                total_matches = (summary.get('total_exact_matches', 0) +
                               summary.get('total_fuzzy_matches', 0) +
                               summary.get('total_semantic_matches', 0))
                coverage = (total_matches / summary['unique_source_fields']) * 100
            st.metric("Coverage", f"{coverage:.1f}%")