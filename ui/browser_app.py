"""
CDE Matcher Browser - Streamlit Application

A modern interface for CDE matching with modular components.
"""

import streamlit as st
import pandas as pd
import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import our pipeline and components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cde_matcher.core.pipeline import CDEMatcherPipeline
from cde_matcher.core.data_adapter import get_data_adapter, get_data_paths
from ui.components import (
    DatasetSelector,
    MatcherConfig,
    ResultsViewer,
    ReportBuilder
)
from ui.auth import check_password, logout

# Configure Streamlit page
st.set_page_config(
    page_title="CDE Matcher Browser",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .match-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .confidence-high { border-left: 5px solid #28a745; }
    .confidence-medium { border-left: 5px solid #ffc107; }
    .confidence-low { border-left: 5px solid #dc3545; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


class CDEBrowserApp:
    """Main CDE Browser Application."""

    def __init__(self):
        self.data_adapter = get_data_adapter()
        self.data_paths = get_data_paths()
        self.pipeline = CDEMatcherPipeline()
        self.dataset_selector = DatasetSelector()
        self.matcher_config = MatcherConfig()
        self.results_viewer = ResultsViewer()
        self.report_builder = ReportBuilder()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'results' not in st.session_state:
            st.session_state.results = None
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = []
        if 'source_data' not in st.session_state:
            st.session_state.source_data = None
        if 'target_data' not in st.session_state:
            st.session_state.target_data = None
        if 'current_dataset' not in st.session_state:
            st.session_state.current_dataset = None

        # Initialize matcher configuration
        MatcherConfig.initialize_session_config()

    def get_cached_outputs(self) -> List[str]:
        """Get list of cached output JSON files."""
        return self.data_adapter.list_files(self.data_paths['output'], "*.json")

    def load_cached_output(self, filename: str) -> tuple:
        """Load a cached output JSON file."""
        try:
            file_path = self.data_adapter.get_full_path(self.data_paths['output'], filename)
            data = self.data_adapter.read_json(file_path)
            return data, None
        except Exception as e:
            return None, str(e)

    def render_sidebar(self) -> str:
        """Render sidebar navigation and configuration."""
        with st.sidebar:
            st.title("🔗 CDE Matcher")
            st.markdown("*Harmonize your data with Common Data Elements*")
            st.divider()

            # Data source selection
            data_source = st.radio(
                "📂 Data Source",
                ["🆕 New Processing", "📂 Cached Results"],
                key="data_source",
                help="Choose to process new data or load existing results"
            )

            if data_source == "📂 Cached Results":
                return self._render_cached_results_selection()
            else:
                return self._render_new_processing_navigation()

    def _render_cached_results_selection(self) -> str:
        """Render cached results selection."""
        st.subheader("📂 Load Cached Results")

        cached_files = self.get_cached_outputs()
        if not cached_files:
            output_path_display = self.data_paths['output']
            st.error(f"No cached results found in `{output_path_display}` directory.")
            return "📊 Select Data"

        selected_file = st.selectbox(
            "Select cached results:",
            options=cached_files,
            help="Choose previously processed results to view"
        )

        if st.button("📥 Load Results", type="primary"):
            results, error = self.load_cached_output(selected_file)
            if error:
                st.error(f"Error loading results: {error}")
                return "📊 Select Data"

            if results:
                st.session_state.results = results
                st.session_state.processing_complete = True
                st.session_state.selected_matches = []  # Reset selections
                st.success(f"✅ Loaded results from {selected_file}")
                st.rerun()

        return "📊 Select Data"

    def _render_new_processing_navigation(self) -> str:
        """Render navigation for new processing."""
        if st.session_state.processing_complete:
            # Show matcher configuration
            st.subheader("⚙️ Configuration")
            MatcherConfig.render_matcher_configuration()

            # Show change dataset option
            if st.session_state.current_dataset:
                st.divider()
                st.write(f"**Current Dataset:** `{st.session_state.current_dataset}`")

                if self.dataset_selector.render_change_dataset_button(has_results=True):
                    # Reset to data selection
                    st.session_state.processing_complete = False
                    st.session_state.results = None
                    st.session_state.selected_matches = []
                    st.session_state.source_data = None
                    st.session_state.target_data = None
                    st.session_state.current_dataset = None
                    st.rerun()

            st.divider()

            # Navigation
            st.subheader("📋 Navigation")

            # Count selected matches for badge
            selected_count = len(st.session_state.selected_matches)

            options = [
                "📊 Overview",
                "🎯 Exact Matches",
                "🔍 Fuzzy Matches",
                "🧠 Semantic Matches",
                f"📝 Manual Report ({selected_count})" if selected_count > 0 else "📝 Manual Report",
                "📈 Analytics",
                "💾 Export"
            ]

            page = st.radio(
                "Select View",
                options,
                key="navigation"
            )

            if selected_count > 0:
                st.info(f"🎯 **{selected_count}** matches selected")

            return page
        else:
            st.info("Select and process data to access results")
            return "📊 Select Data"

    def render_data_selection_page(self):
        """Render the data selection and processing page."""
        st.header("🚀 CDE Matcher - Data Selection")

        # Dataset selection flow
        result = self.dataset_selector.render_dataset_selection_flow()
        df, filename, method, column_name = result

        if df is None:
            return

        # Load DigiPath CDEs
        try:
            cde_path = self.data_adapter.get_full_path(
                self.data_paths['cdes'],
                'digipath_cdes.csv'
            )
            target_df = self.data_adapter.read_csv(cde_path)
            st.success(f"✅ Loaded DigiPath CDEs: {len(target_df)} items")
        except Exception as e:
            st.error(f"❌ Error loading DigiPath CDEs: {e}")
            return

        # Store data in session state
        st.session_state.source_data = df
        st.session_state.target_data = target_df
        st.session_state.current_dataset = filename
        st.session_state.extraction_method = method
        st.session_state.extraction_column = column_name

        st.divider()

        # Configuration and processing
        config = MatcherConfig.render_matcher_configuration()

        st.divider()

        # Start processing button
        if st.button("🚀 Start Matching Process", type="primary"):
            self._run_matching_process(df, target_df, filename, method, column_name, config)

    def _run_matching_process(self, source_df: pd.DataFrame, target_df: pd.DataFrame,
                            source_name: str, method: str, column_name: Optional[str],
                            config: Dict[str, Any]):
        """Run the matching process."""

        with st.spinner("🔄 Processing matches..."):
            try:
                # Configure pipeline
                self.pipeline.configure_matchers(
                    exact_config=config['exact'],
                    fuzzy_config=config['fuzzy'],
                    semantic_config=config['semantic']
                )

                # Run pipeline using DataFrames
                results = self.pipeline.run_pipeline_from_dataframes(
                    source_df=source_df,
                    target_df=target_df,
                    source_name=Path(source_name).stem,
                    target_name="digipath_cdes",
                    source_method=method,
                    source_column=column_name
                )

                # Store results
                st.session_state.results = results
                st.session_state.processing_complete = True
                st.session_state.selected_matches = []  # Reset selections

                st.success("✅ Matching completed successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during processing: {e}")

    def render_main_content(self, current_page: str):
        """Render main content based on current page."""
        if current_page == "📊 Select Data":
            self.render_data_selection_page()
        elif current_page == "📊 Overview":
            if st.session_state.results:
                ResultsViewer.render_overview_dashboard(st.session_state.results)
            else:
                st.warning("No results available. Please process data first.")
        elif "Matches" in current_page:
            if st.session_state.results:
                match_type = current_page.split()[1]  # Extract type from "🎯 Exact Matches"
                ResultsViewer.render_match_details(match_type, st.session_state.results)
            else:
                st.warning("No results available. Please process data first.")
        elif "Manual Report" in current_page:
            ReportBuilder.render_manual_report_page()
        elif current_page == "📈 Analytics":
            if st.session_state.results:
                ResultsViewer.render_analytics_dashboard(st.session_state.results)
            else:
                st.warning("No results available. Please process data first.")
        elif current_page == "💾 Export":
            if st.session_state.results:
                ReportBuilder.render_export_page(st.session_state.results)
            else:
                st.warning("No results available. Please export.")

    def run(self):
        """Run the main application."""
        # Check authentication first
        if not check_password():
            return

        # Render sidebar and get current page
        current_page = self.render_sidebar()

        # Render main content
        self.render_main_content(current_page)


def main():
    """Main application entry point."""
    app = CDEBrowserApp()
    app.run()


if __name__ == "__main__":
    main()