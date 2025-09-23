"""
CDE Matcher Browser - Modern Streamlit Interface

A general-purpose interface for browsing CDE matching results with real-time
processing using the new modular architecture. Provides upload, processing,
and validation workflows as outlined in the project plan.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import time
import os
import glob

# Import our modular matching components
from cde_matcher_pipeline import CDEMatcherPipeline
from cde_matcher.core.matchers import create_matcher

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
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


class CDEBrowserApp:
    """Main application class for the CDE Matcher Browser."""

    def __init__(self):
        """Initialize the application with session state management."""
        self.init_session_state()
        self.pipeline = CDEMatcherPipeline()
        self.load_digipath_cdes()

    def load_digipath_cdes(self):
        """Load DigiPath CDEs as the standard source data."""
        try:
            digipath_path = "data/cdes/digipath_cdes.csv"
            self.digipath_data = pd.read_csv(digipath_path)

            if 'Item' not in self.digipath_data.columns:
                st.error("DigiPath CDEs file must contain an 'Item' column")
                return

            # Store as session state for consistency
            if 'source_data' not in st.session_state or st.session_state.source_data is None:
                st.session_state.source_data = self.digipath_data

        except FileNotFoundError:
            st.error("DigiPath CDEs file not found at data/cdes/digipath_cdes.csv")
            self.digipath_data = None
        except Exception as e:
            st.error(f"Error loading DigiPath CDEs: {e}")
            self.digipath_data = None

    def get_clinical_data_files(self):
        """Get list of available clinical data files."""
        clinical_data_dir = "data/clinical_data"

        if not os.path.exists(clinical_data_dir):
            return []

        # Get all CSV files in the clinical data directory
        csv_files = glob.glob(os.path.join(clinical_data_dir, "*.csv"))

        # Return just the filenames (not full paths) for display
        return [os.path.basename(f) for f in csv_files]

    def load_clinical_data_file(self, filename: str):
        """Load a specific clinical data file."""
        try:
            file_path = os.path.join("data/clinical_data", filename)
            df = pd.read_csv(file_path)
            return df, None
        except Exception as e:
            return None, str(e)

    def analyze_dataset_structure(self, df: pd.DataFrame):
        """Analyze dataset structure to suggest extraction methods."""
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'unique_counts': df.nunique().to_dict(),
            'suggested_method': 'columns',
            'potential_variable_columns': []
        }

        # Look for columns that might contain variable names
        for col in df.columns:
            col_lower = col.lower()
            unique_count = df[col].nunique()
            total_count = len(df)

            # Check for common variable name columns
            if any(keyword in col_lower for keyword in ['variable', 'field', 'item', 'name']):
                if unique_count > total_count * 0.5:  # More than 50% unique values
                    analysis['potential_variable_columns'].append({
                        'column': col,
                        'unique_values': unique_count,
                        'sample_values': df[col].dropna().head(5).tolist(),
                        'reason': f'Column name suggests variables ({col_lower})'
                    })

        # If we found potential variable columns, suggest column_values method
        if analysis['potential_variable_columns']:
            analysis['suggested_method'] = 'column_values'
            analysis['suggested_column'] = analysis['potential_variable_columns'][0]['column']

        return analysis

    def preview_variable_extraction(self, df: pd.DataFrame, method: str, column: str = None):
        """Preview what variables would be extracted with given method."""
        try:
            from cde_matcher_pipeline import extract_variables_flexible
            variables = extract_variables_flexible(df, method, column)
            return variables[:20], len(variables), None  # Show first 20, total count, no error
        except Exception as e:
            return [], 0, str(e)

    def get_cached_outputs(self):
        """Get list of cached output JSON files."""
        output_dir = "output"
        if not os.path.exists(output_dir):
            return []

        json_files = glob.glob(os.path.join(output_dir, "*.json"))
        return [os.path.basename(f) for f in json_files]

    def load_cached_output(self, filename: str):
        """Load a cached output JSON file."""
        try:
            file_path = os.path.join("output", filename)
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check if this is new format (with summary) or old format
            if 'summary' in data:
                # New format from current pipeline
                return data, None
            else:
                # Old format - convert to new format structure
                converted_data = self._convert_old_format(data)
                return converted_data, None

        except Exception as e:
            return None, str(e)

    def _convert_old_format(self, old_data):
        """Convert old cached format to new pipeline format."""
        # Create new format structure
        new_format = {
            'exact_matches': [],
            'fuzzy_matches': [],
            'semantic_matches': [],
            'summary': {
                'total_exact_matches': 0,
                'total_fuzzy_matches': 0,
                'total_semantic_matches': 0,
                'unique_source_fields': 0,
                'processing_time': 0.0
            }
        }

        # Convert old format matches
        if 'exact_matches' in old_data:
            for match in old_data['exact_matches']:
                new_match = {
                    'source_field': match.get('seaad_field', match.get('source_field', '')),
                    'target_item': match.get('digipath_item', match.get('target_item', '')),
                    'confidence': match.get('similarity_score', match.get('confidence', 1.0)),
                    'match_type': 'exact',
                    'metadata': {k: v for k, v in match.items() if k not in ['seaad_field', 'digipath_item', 'similarity_score']}
                }
                new_format['exact_matches'].append(new_match)

        if 'fuzzy_matches' in old_data:
            for match in old_data['fuzzy_matches']:
                new_match = {
                    'source_field': match.get('seaad_field', match.get('source_field', '')),
                    'target_item': match.get('digipath_item', match.get('target_item', '')),
                    'confidence': match.get('similarity_score', match.get('confidence', 0.0)),
                    'match_type': 'fuzzy',
                    'metadata': {k: v for k, v in match.items() if k not in ['seaad_field', 'digipath_item', 'similarity_score']}
                }
                new_format['fuzzy_matches'].append(new_match)

        if 'semantic_matches' in old_data:
            for match in old_data['semantic_matches']:
                new_match = {
                    'source_field': match.get('seaad_field', match.get('source_field', '')),
                    'target_item': match.get('digipath_item', match.get('target_item', '')),
                    'confidence': match.get('similarity_score', match.get('confidence', 1.0)),
                    'match_type': 'semantic',
                    'metadata': {k: v for k, v in match.items() if k not in ['seaad_field', 'digipath_item', 'similarity_score']}
                }
                new_format['semantic_matches'].append(new_match)

        # Update summary counts
        new_format['summary']['total_exact_matches'] = len(new_format['exact_matches'])
        new_format['summary']['total_fuzzy_matches'] = len(new_format['fuzzy_matches'])
        new_format['summary']['total_semantic_matches'] = len(new_format['semantic_matches'])

        # Count unique source fields
        all_sources = set()
        for matches in [new_format['exact_matches'], new_format['fuzzy_matches'], new_format['semantic_matches']]:
            for match in matches:
                all_sources.add(match['source_field'])
        new_format['summary']['unique_source_fields'] = len(all_sources)

        return new_format

    def init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'results' not in st.session_state:
            st.session_state.results = None
        if 'source_data' not in st.session_state:
            st.session_state.source_data = None
        if 'target_data' not in st.session_state:
            st.session_state.target_data = None
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'matcher_config' not in st.session_state:
            st.session_state.matcher_config = {
                'exact': {'case_sensitive': False},
                'fuzzy': {'threshold': 0.7, 'algorithm': 'token_sort_ratio'},
                'semantic': {'case_sensitive': False, 'exact_only': False}
            }
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = []
        if 'manual_report' not in st.session_state:
            st.session_state.manual_report = {
                'matches': [],
                'filename': None,
                'timestamp': None
            }

    def render_header(self):
        """Render the application header."""
        st.title("🔗 CDE Matcher Browser")
        st.markdown("""
        **Match your variable names to DigiPath Common Data Elements (CDEs)**

        DigiPath CDEs are pre-loaded as the source. Upload your dataset with variable names
        to find matches using exact, fuzzy, and semantic matching algorithms.
        """)

        # Show DigiPath CDE info
        if hasattr(self, 'digipath_data') and self.digipath_data is not None:
            unique_items = self.digipath_data['Item'].dropna().nunique()
            st.info(f"📋 **{unique_items} DigiPath CDEs loaded and ready for matching**")

        st.divider()

    def render_sidebar(self):
        """Render the sidebar with configuration and navigation."""
        with st.sidebar:
            # Dataset status section
            st.header("📁 Current Dataset")
            if st.session_state.get('target_data') is not None:
                selected_file = st.session_state.get('selected_file', 'Unknown')
                method = st.session_state.get('extraction_method', 'columns')
                total_vars = st.session_state.get('total_variables', 0)

                st.success(f"**Loaded:** {selected_file}")
                st.write(f"**Method:** {method}")
                st.write(f"**Variables:** {total_vars}")

                # Change dataset button in sidebar
                if st.button("🔄 Change Dataset", key="sidebar_change", help="Select a different dataset"):
                    # Check if there are results that would be lost
                    has_results = st.session_state.get('processing_complete', False)
                    if has_results:
                        st.session_state.confirm_dataset_change = True
                        st.rerun()
                    else:
                        # Safe to change immediately
                        keys_to_clear = [
                            'target_data', 'selected_file', 'extraction_method',
                            'extraction_column', 'total_variables'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
            else:
                st.info("No dataset selected")

            # Handle confirmation dialog from sidebar
            if st.session_state.get('confirm_dataset_change', False):
                st.warning("⚠️ **Warning:** This will clear all results!")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Yes", key="sidebar_confirm"):
                        keys_to_clear = [
                            'target_data', 'selected_file', 'extraction_method',
                            'extraction_column', 'total_variables', 'results',
                            'processing_complete', 'selected_matches', 'confirm_dataset_change'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                with col_b:
                    if st.button("❌ No", key="sidebar_cancel"):
                        del st.session_state.confirm_dataset_change
                        st.rerun()

            st.divider()
            st.header("⚙️ Configuration")

            # Matcher configuration
            st.subheader("Matching Algorithms")

            # Exact matcher config
            with st.expander("🎯 Exact Matcher", expanded=False):
                case_sensitive = st.checkbox(
                    "Case Sensitive",
                    value=st.session_state.matcher_config['exact']['case_sensitive'],
                    key="exact_case_sensitive"
                )
                st.session_state.matcher_config['exact']['case_sensitive'] = case_sensitive

            # Fuzzy matcher config
            with st.expander("🔍 Fuzzy Matcher", expanded=False):
                threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.0, max_value=1.0,
                    value=st.session_state.matcher_config['fuzzy']['threshold'],
                    step=0.05,
                    key="fuzzy_threshold"
                )
                algorithm = st.selectbox(
                    "Algorithm",
                    options=['ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'],
                    index=['ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio'].index(
                        st.session_state.matcher_config['fuzzy']['algorithm']
                    ),
                    key="fuzzy_algorithm"
                )
                st.session_state.matcher_config['fuzzy']['threshold'] = threshold
                st.session_state.matcher_config['fuzzy']['algorithm'] = algorithm

            # Semantic matcher config
            with st.expander("🧠 Semantic Matcher", expanded=False):
                exact_only = st.checkbox(
                    "Exact Semantic Only",
                    value=st.session_state.matcher_config['semantic']['exact_only'],
                    key="semantic_exact_only"
                )
                st.session_state.matcher_config['semantic']['exact_only'] = exact_only

            st.divider()

            # Navigation
            st.subheader("📋 Navigation")

            # Data source selection
            data_source = st.radio(
                "Data Source",
                ["🆕 New Processing", "📂 Cached Results"],
                key="data_source"
            )

            if data_source == "📂 Cached Results":
                return "📂 Cached Results"
            elif st.session_state.processing_complete:
                # Keep stable option labels to prevent radio reset
                options = ["📊 Overview", "🎯 Exact Matches", "🔍 Fuzzy Matches",
                          "🧠 Semantic Matches", "📝 Manual Report", "📈 Analytics", "💾 Export"]

                page = st.radio(
                    "Select View",
                    options,
                    key="navigation"
                )

                # Show selection count separately to avoid radio state issues
                selected_count = len(st.session_state.selected_matches)
                if selected_count > 0:
                    st.sidebar.info(f"🎯 **{selected_count}** matches selected for manual report")

                return page
            else:
                st.info("Select and process data to access results")
                return "📊 Select Data"

    def render_upload_page(self):
        """Render the data selection and processing page."""
        st.header("📊 Clinical Data Selection")

        # Show DigiPath CDEs info
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🎯 DigiPath CDEs (Reference)")
            if hasattr(self, 'digipath_data') and self.digipath_data is not None:
                unique_items = self.digipath_data['Item'].dropna().nunique()
                st.success(f"✅ {unique_items} DigiPath CDEs loaded automatically")

                with st.expander("📋 Preview DigiPath CDEs"):
                    st.dataframe(self.digipath_data.head(10))
                    st.write(f"**Available columns:** {list(self.digipath_data.columns)}")

                    # Show sample CDE items
                    sample_items = self.digipath_data['Item'].dropna().head(10).tolist()
                    st.write("**Sample CDE items:**")
                    for item in sample_items:
                        st.write(f"  • {item}")

                # Set as source data for consistency with pipeline
                st.session_state.source_data = self.digipath_data
            else:
                st.error("❌ DigiPath CDEs not loaded. Check data/cdes/digipath_cdes.csv")

        with col2:
            st.subheader("📊 CDE Statistics")
            if hasattr(self, 'digipath_data') and self.digipath_data is not None:
                # Show collection distribution
                if 'Collection' in self.digipath_data.columns:
                    collections = self.digipath_data['Collection'].value_counts()
                    st.write("**Collections:**")
                    for collection, count in collections.head(5).items():
                        st.write(f"  • {collection}: {count}")

        st.divider()

        # Select clinical data file
        st.subheader("📁 Select Clinical Dataset")
        st.markdown("""
        Choose a clinical dataset from the available files. We'll analyze the structure
        and help you choose how to extract variables for matching.
        """)

        # Get available clinical data files
        available_files = self.get_clinical_data_files()

        if not available_files:
            st.error("❌ No clinical data files found in `data/clinical_data/`")
            st.info("Please add CSV files to the `data/clinical_data/` directory")
            return

        # File selection
        selected_file = st.selectbox(
            "Available Clinical Data Files:",
            available_files,
            index=0,
            help="Select a CSV file from the clinical data directory"
        )

        # Load and preview dataset
        with st.spinner(f"Analyzing {selected_file}..."):
            df, error = self.load_clinical_data_file(selected_file)

            if error:
                st.error(f"Error loading {selected_file}: {error}")
                return

            # Analyze dataset structure
            analysis = self.analyze_dataset_structure(df)

        # Dataset preview
        st.subheader("📊 Dataset Preview")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", f"{analysis['shape'][0]:,}")
        with col2:
            st.metric("Columns", analysis['shape'][1])
        with col3:
            st.metric("Total Cells", f"{analysis['shape'][0] * analysis['shape'][1]:,}")
        with col4:
            file_path = os.path.join("data/clinical_data", selected_file)
            file_size_mb = os.stat(file_path).st_size / (1024 * 1024)
            st.metric("File Size", f"{file_size_mb:.1f} MB")

        # Show sample data
        st.write("**Sample Data (first 5 rows):**")
        st.dataframe(df.head(), width='stretch')

        st.divider()

        # Variable extraction method selection
        st.subheader("🔧 Variable Extraction Method")

        # Show suggestion based on analysis
        if analysis['suggested_method'] == 'column_values':
            st.info(f"💡 **Suggested Method**: Use specific column (detected potential variable columns)")
        else:
            st.info(f"💡 **Suggested Method**: Use column headers (typical for raw clinical data)")

        # Method selection
        extraction_method = st.radio(
            "How should we extract variables from this dataset?",
            options=["columns", "column_values"],
            format_func=lambda x: {
                "columns": "📋 Use Column Headers",
                "column_values": "📝 Use Specific Column"
            }[x],
            index=0 if analysis['suggested_method'] == 'columns' else 1,
            help="Choose how to identify the variables to match against CDEs"
        )

        # Column selection (if using column_values method)
        selected_column = None
        if extraction_method == "column_values":
            if analysis['potential_variable_columns']:
                st.write("**Detected potential variable columns:**")
                for pot_col in analysis['potential_variable_columns']:
                    st.write(f"• **{pot_col['column']}**: {pot_col['unique_values']} unique values")
                    st.write(f"  Sample: {', '.join(map(str, pot_col['sample_values'][:3]))}...")

            selected_column = st.selectbox(
                "Select column containing variable names:",
                options=df.columns.tolist(),
                index=df.columns.tolist().index(analysis.get('suggested_column', df.columns[0]))
                      if analysis.get('suggested_column') in df.columns else 0,
                help="Choose the column that contains the variable names to match"
            )

        # Preview extraction results
        st.subheader("🔍 Variable Extraction Preview")
        preview_vars, total_vars, preview_error = self.preview_variable_extraction(
            df, extraction_method, selected_column
        )

        if preview_error:
            st.error(f"Extraction error: {preview_error}")
        else:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**{total_vars} variables will be extracted:**")
                if preview_vars:
                    # Show first 10 variables in a nice format
                    for i, var in enumerate(preview_vars[:10], 1):
                        st.write(f"{i}. {var}")
                    if total_vars > 10:
                        st.write(f"... and {total_vars - 10} more")

            with col2:
                if total_vars > 0:
                    # Ready to process button
                    if st.button("🚀 Process with These Variables", type="primary"):
                        # Store the dataset and extraction settings
                        st.session_state.target_data = df
                        st.session_state.selected_file = selected_file
                        st.session_state.extraction_method = extraction_method
                        st.session_state.extraction_column = selected_column
                        st.session_state.total_variables = total_vars
                        st.success(f"✅ Ready to process {total_vars} variables!")
                        st.rerun()
                else:
                    st.warning("No variables found with current settings")

        # Show loaded data if available
        if st.session_state.target_data is not None:
            st.divider()

            # Header with change dataset option
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("📊 Loaded Dataset Preview")
            with col2:
                # Check if there are results that would be lost
                has_results = st.session_state.get('processing_complete', False)

                if has_results:
                    # Show confirmation for users with existing results
                    if st.button("🔄 Change Dataset", type="secondary", help="⚠️ This will clear current results"):
                        if 'confirm_dataset_change' not in st.session_state:
                            st.session_state.confirm_dataset_change = True
                            st.rerun()

                    # Show confirmation dialog
                    if st.session_state.get('confirm_dataset_change', False):
                        st.warning("⚠️ **Warning:** Changing datasets will clear all current results and selections.")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Yes, Change Dataset", type="primary"):
                                # Clear dataset-related session state
                                keys_to_clear = [
                                    'target_data', 'selected_file', 'extraction_method',
                                    'extraction_column', 'total_variables', 'results',
                                    'processing_complete', 'selected_matches', 'confirm_dataset_change'
                                ]
                                for key in keys_to_clear:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.success("Dataset cleared! Select a new dataset below.")
                                st.rerun()
                        with col_b:
                            if st.button("❌ Cancel"):
                                del st.session_state.confirm_dataset_change
                                st.rerun()
                else:
                    # No results to lose, safe to change
                    if st.button("🔄 Change Dataset", type="secondary", help="Select a different dataset"):
                        keys_to_clear = [
                            'target_data', 'selected_file', 'extraction_method',
                            'extraction_column', 'total_variables'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

            num_variables = st.session_state.target_data.shape[1]
            num_rows = st.session_state.target_data.shape[0]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📁 File", st.session_state.get('selected_file', 'Unknown'))
            with col2:
                st.metric("📊 Rows", f"{num_rows:,}")
            with col3:
                total_vars = st.session_state.get('total_variables', num_variables)
                st.metric("📝 Variables", total_vars)
            with col4:
                method = st.session_state.get('extraction_method', 'columns')
                column = st.session_state.get('extraction_column')
                method_display = "Columns" if method == "columns" else f"Column: {column}"
                st.metric("🔧 Method", method_display)

            # Data preview tabs
            tab1, tab2 = st.tabs(["📊 Data Preview", "📝 Variables List"])

            with tab1:
                st.dataframe(st.session_state.target_data.head(10), width='stretch')

            with tab2:
                variables = list(st.session_state.target_data.columns)

                # Search functionality
                search_var = st.text_input("🔍 Search variables:", placeholder="Type to filter...")
                if search_var:
                    filtered_vars = [v for v in variables if search_var.lower() in v.lower()]
                else:
                    filtered_vars = variables

                st.write(f"**Showing {len(filtered_vars)} of {len(variables)} variables:**")

                # Display in columns for better layout
                cols = st.columns(3)
                for i, var in enumerate(filtered_vars[:60]):  # Limit to 60 for performance
                    with cols[i % 3]:
                        st.write(f"• {var}")

                if len(filtered_vars) > 60:
                    st.write(f"... and {len(filtered_vars) - 60} more")

        # Processing section
        if (hasattr(self, 'digipath_data') and self.digipath_data is not None and
            st.session_state.target_data is not None):

            st.divider()
            st.subheader("🚀 Start Matching Process")

            # Show what will be matched
            source_items = self.digipath_data['Item'].dropna().nunique()
            target_vars = st.session_state.target_data.shape[1]
            total_comparisons = source_items * target_vars

            st.info(f"""
            **Ready to match:**
            - 🎯 **{source_items}** DigiPath CDEs (reference)
            - 📝 **{target_vars}** variables from `{st.session_state.get('selected_file', 'selected file')}`
            - 🔍 **{total_comparisons:,}** total comparisons to perform
            """)

            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("🔍 Start Matching Process", type="primary", width='stretch'):
                    self.process_matching()

    def process_matching(self):
        """Process the matching with progress tracking."""
        with st.spinner("Processing matches..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Configure pipeline
                status_text.text("Configuring matchers...")
                progress_bar.progress(20)

                self.pipeline.configure_matchers(
                    exact_config=st.session_state.matcher_config['exact'],
                    fuzzy_config=st.session_state.matcher_config['fuzzy'],
                    semantic_config=st.session_state.matcher_config['semantic']
                )

                # Run pipeline directly with DataFrames (no temp files!)
                status_text.text("Running matching algorithms...")
                progress_bar.progress(60)

                # Get extraction settings from session state
                source_method = st.session_state.get('extraction_method', 'columns')
                source_column = st.session_state.get('extraction_column', None)
                source_file = st.session_state.get('selected_file', 'clinical_data')

                # Use DataFrame-based pipeline (no file I/O needed)
                results = self.pipeline.run_pipeline_from_dataframes(
                    source_df=st.session_state.target_data,  # Clinical data
                    target_df=st.session_state.source_data,  # DigiPath CDEs
                    source_name=Path(source_file).stem,  # Clean filename for output
                    target_name="digipath_cdes",
                    source_method=source_method,
                    source_column=source_column,
                    target_method="column_values",
                    target_column="Item"
                )

                progress_bar.progress(80)
                status_text.text("Processing results...")

                # Store results
                st.session_state.results = results
                st.session_state.processing_complete = True

                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")

                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Error during processing: {e}")
                progress_bar.progress(0)
                status_text.text("❌ Processing failed")

    def render_overview_page(self):
        """Render the results overview page."""
        st.header("📊 Matching Results Overview")

        if not st.session_state.results:
            st.warning("No results available. Please upload and process data first.")
            return

        results = st.session_state.results

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>Your Variables</p>
            </div>
            """.format(results['summary']['unique_source_fields']), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>DigiPath CDEs</p>
            </div>
            """.format(results['summary']['unique_target_items']), unsafe_allow_html=True)

        with col3:
            total_matches = (results['summary']['total_exact_matches'] +
                           results['summary']['total_fuzzy_matches'] +
                           results['summary']['total_semantic_matches'])
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>Total Matches</p>
            </div>
            """.format(total_matches), unsafe_allow_html=True)

        with col4:
            coverage = (total_matches / results['summary']['unique_source_fields'] * 100) if results['summary']['unique_source_fields'] > 0 else 0
            st.markdown("""
            <div class="metric-card">
                <h3>{:.1f}%</h3>
                <p>Coverage</p>
            </div>
            """.format(coverage), unsafe_allow_html=True)

        st.divider()

        # Match type breakdown
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📈 Match Distribution")

            match_data = {
                'Match Type': ['Exact', 'Fuzzy', 'Semantic'],
                'Count': [
                    results['summary']['total_exact_matches'],
                    results['summary']['total_fuzzy_matches'],
                    results['summary']['total_semantic_matches']
                ]
            }

            fig = px.bar(
                match_data,
                x='Match Type',
                y='Count',
                color='Match Type',
                title="Matches by Algorithm Type"
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, width='stretch')

        with col2:
            st.subheader("🎯 Match Quality")

            # Confidence distribution for fuzzy matches
            if results['fuzzy_matches']:
                confidences = [match['confidence'] for match in results['fuzzy_matches']]

                fig = px.histogram(
                    x=confidences,
                    nbins=20,
                    title="Fuzzy Match Confidence Distribution",
                    labels={'x': 'Confidence Score', 'y': 'Count'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No fuzzy matches to display confidence distribution")

        # Configuration summary
        st.subheader("⚙️ Current Configuration")
        config_col1, config_col2, config_col3 = st.columns(3)

        with config_col1:
            st.write("**Exact Matcher**")
            exact_config = results['configuration']['exact_matcher']
            st.write(f"- Case sensitive: {exact_config['case_sensitive']}")

        with config_col2:
            st.write("**Fuzzy Matcher**")
            fuzzy_config = results['configuration']['fuzzy_matcher']
            st.write(f"- Threshold: {fuzzy_config['threshold']}")
            st.write(f"- Algorithm: {fuzzy_config['algorithm']}")

        with config_col3:
            st.write("**Semantic Matcher**")
            semantic_config = results['configuration']['semantic_matcher']
            st.write(f"- Exact only: {semantic_config['exact_only']}")
            st.write(f"- Case sensitive: {semantic_config['case_sensitive']}")

    def render_match_details(self, match_type: str):
        """Render detailed view for a specific match type."""
        if not st.session_state.results:
            st.warning("No results available.")
            return

        results = st.session_state.results
        matches_key = f"{match_type.lower()}_matches"
        matches = results.get(matches_key, [])

        if not matches:
            st.info(f"No {match_type.lower()} matches found.")
            return

        st.header(f"{match_type} Matches ({len(matches)} found)")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            if match_type == "Fuzzy":
                min_confidence = st.slider(
                    "Minimum Confidence",
                    min_value=0.0, max_value=1.0,
                    value=0.7, step=0.05
                )
                matches = [m for m in matches if m['confidence'] >= min_confidence]

        with col2:
            search_term = st.text_input("Search matches:", placeholder="Enter source or target name")
            if search_term:
                search_lower = search_term.lower()
                matches = [
                    m for m in matches
                    if search_lower in m['source_field'].lower() or
                       search_lower in m['target_item'].lower()
                ]

        with col3:
            st.write(f"**Showing {len(matches)} matches**")

        # Display matches with selection capability
        if matches:
            # Convert matches to DataFrame with selection column
            df_data = []
            for i, match in enumerate(matches):
                # Create unique match ID
                match_id = f"{match['source_field']}_{match['target_item']}_{match['match_type']}"

                # Check if this match is already selected
                is_selected = any(
                    selected['match_id'] == match_id
                    for selected in st.session_state.selected_matches
                )

                df_data.append({
                    'Select': is_selected,
                    'Variable': match['source_field'],
                    'DigiPath CDE': match['target_item'],
                    'Confidence': match['confidence'],
                    'Match Type': match['match_type'],
                    'match_id': match_id,  # Hidden column for tracking
                    'metadata': match.get('metadata', {})  # Hidden column for metadata
                })

            df = pd.DataFrame(df_data)

            # Selection controls
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                if st.button("✅ Select All", key=f"select_all_{match_type}"):
                    for _, row in df.iterrows():
                        match_data = {
                            'match_id': row['match_id'],
                            'variable': row['Variable'],
                            'cde': row['DigiPath CDE'],
                            'confidence': row['Confidence'],
                            'match_type': row['Match Type'],
                            'metadata': row['metadata']
                        }
                        # Add if not already selected
                        if not any(s['match_id'] == match_data['match_id'] for s in st.session_state.selected_matches):
                            st.session_state.selected_matches.append(match_data)
                    st.rerun()

            with col2:
                if st.button("❌ Deselect All", key=f"deselect_all_{match_type}"):
                    # Remove all matches of this type
                    st.session_state.selected_matches = [
                        s for s in st.session_state.selected_matches
                        if s['match_type'] != match_type.lower()
                    ]
                    st.rerun()

            with col3:
                if st.button("⭐ High Confidence", key=f"select_high_{match_type}"):
                    for _, row in df.iterrows():
                        if row['Confidence'] >= 0.8:
                            match_data = {
                                'match_id': row['match_id'],
                                'variable': row['Variable'],
                                'cde': row['DigiPath CDE'],
                                'confidence': row['Confidence'],
                                'match_type': row['Match Type'],
                                'metadata': row['metadata']
                            }
                            # Add if not already selected
                            if not any(s['match_id'] == match_data['match_id'] for s in st.session_state.selected_matches):
                                st.session_state.selected_matches.append(match_data)
                    st.rerun()

            with col4:
                # Show current selection count
                current_selections = len([s for s in st.session_state.selected_matches if s['match_type'] == match_type.lower()])
                st.metric("Selected", current_selections)

            # Interactive data editor
            edited_df = st.data_editor(
                df[['Select', 'Variable', 'DigiPath CDE', 'Confidence', 'Match Type']],
                width='stretch',
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select matches to include in manual report",
                        default=False
                    ),
                    "Confidence": st.column_config.NumberColumn(
                        "Confidence",
                        help="Match confidence score",
                        format="%.3f",
                        min_value=0.0,
                        max_value=1.0
                    ),
                    "Variable": st.column_config.TextColumn(
                        "Variable",
                        help="Source variable name"
                    ),
                    "DigiPath CDE": st.column_config.TextColumn(
                        "DigiPath CDE",
                        help="Target CDE name"
                    )
                },
                key=f"match_editor_{match_type}"
            )

            # Update selections based on checkbox changes
            for i, (_, row) in enumerate(edited_df.iterrows()):
                match_id = df.iloc[i]['match_id']
                is_currently_selected = any(s['match_id'] == match_id for s in st.session_state.selected_matches)
                should_be_selected = row['Select']

                if should_be_selected and not is_currently_selected:
                    # Add to selections
                    match_data = {
                        'match_id': match_id,
                        'variable': row['Variable'],
                        'cde': row['DigiPath CDE'],
                        'confidence': row['Confidence'],
                        'match_type': row['Match Type'],
                        'metadata': df.iloc[i]['metadata']
                    }
                    st.session_state.selected_matches.append(match_data)
                elif not should_be_selected and is_currently_selected:
                    # Remove from selections
                    st.session_state.selected_matches = [
                        s for s in st.session_state.selected_matches
                        if s['match_id'] != match_id
                    ]

            # Optional: Show detailed metadata
            if st.checkbox("🔍 Show detailed metadata", key=f"metadata_{match_type}"):
                st.json(matches[:10])  # Show first 10 matches with full metadata
        else:
            st.info(f"No {match_type.lower()} matches found.")

    def render_manual_report_page(self):
        """Render the manual report building page."""
        st.header("📝 Manual Report Builder")

        # Show overall selection summary
        total_selected = len(st.session_state.selected_matches)

        if total_selected == 0:
            st.info("🔍 **No matches selected yet**")
            st.markdown("""
            **To build your report:**
            1. Navigate to the match type tabs (Exact, Fuzzy, Semantic)
            2. Use the checkboxes or selection buttons to choose matches
            3. Return here to review and download your report
            """)
            return

        # Selection summary
        st.subheader("📊 Selection Summary")

        col1, col2, col3, col4 = st.columns(4)

        # Count by match type
        exact_count = len([s for s in st.session_state.selected_matches if s['match_type'] == 'exact'])
        fuzzy_count = len([s for s in st.session_state.selected_matches if s['match_type'] == 'fuzzy'])
        semantic_count = len([s for s in st.session_state.selected_matches if s['match_type'] == 'semantic'])

        with col1:
            st.metric("🎯 Exact", exact_count)
        with col2:
            st.metric("🔍 Fuzzy", fuzzy_count)
        with col3:
            st.metric("🧠 Semantic", semantic_count)
        with col4:
            st.metric("📋 Total", total_selected)

        # Report preview and editing
        st.subheader("📋 Report Preview & Editing")

        # Check for conflicts (same variable mapped to multiple CDEs)
        variable_mappings = {}
        conflicts = []

        for match in st.session_state.selected_matches:
            var = match['variable']
            cde = match['cde']

            if var in variable_mappings:
                if variable_mappings[var] != cde:
                    conflicts.append(var)
            else:
                variable_mappings[var] = cde

        if conflicts:
            st.warning(f"⚠️ **Conflicts detected:** {len(conflicts)} variables are mapped to multiple CDEs")

            with st.expander("🔍 View Conflicts", expanded=True):
                for var in conflicts:
                    conflicting_matches = [s for s in st.session_state.selected_matches if s['variable'] == var]
                    st.write(f"**{var}** is mapped to:")
                    for match in conflicting_matches:
                        col_a, col_b, col_c = st.columns([3, 1, 1])
                        with col_a:
                            st.write(f"  • {match['cde']} (confidence: {match['confidence']:.3f}, type: {match['match_type']})")
                        with col_b:
                            if st.button("Keep", key=f"keep_{match['match_id']}"):
                                # Remove other conflicting matches for this variable
                                st.session_state.selected_matches = [
                                    s for s in st.session_state.selected_matches
                                    if not (s['variable'] == var and s['match_id'] != match['match_id'])
                                ]
                                st.rerun()
                        with col_c:
                            if st.button("Remove", key=f"remove_{match['match_id']}"):
                                st.session_state.selected_matches = [
                                    s for s in st.session_state.selected_matches
                                    if s['match_id'] != match['match_id']
                                ]
                                st.rerun()
                    st.divider()

        # Report table editing
        st.subheader("📝 Final Report Data")

        # Convert to editable DataFrame
        report_data = []
        for match in st.session_state.selected_matches:
            # Skip if this variable has conflicts and isn't the preferred one
            if match['variable'] in conflicts:
                continue

            report_data.append({
                'CDE': match['cde'],
                'Variable': match['variable'],
                'Confidence': match['confidence'],
                'Match Type': match['match_type']
            })

        if report_data:
            # Sort by CDE name for consistency
            report_df = pd.DataFrame(report_data).sort_values('CDE')

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

            # Management buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🗑️ Clear All Selections"):
                    st.session_state.selected_matches = []
                    st.rerun()

            with col2:
                if st.button("🔄 Reset to Original"):
                    # Reset any manual edits
                    st.rerun()

            with col3:
                # Download functionality
                final_report_df = edited_report[['CDE', 'Variable']].copy()
                csv_data = final_report_df.to_csv(index=False)

                # Generate filename with timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cde_variable_mapping_{timestamp}.csv"

                st.download_button(
                    label="📥 Download Report (CSV)",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="primary"
                )

            # Report statistics
            st.subheader("📈 Report Statistics")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🎯 Total Mappings", len(edited_report))

            with col2:
                unique_cdes = edited_report['CDE'].nunique()
                st.metric("📋 Unique CDEs", unique_cdes)

            with col3:
                unique_vars = edited_report['Variable'].nunique()
                st.metric("📊 Unique Variables", unique_vars)

            # Preview final 2-column format
            with st.expander("👀 Preview Final Report Format"):
                st.dataframe(
                    edited_report[['CDE', 'Variable']],
                    width='stretch',
                    hide_index=True
                )
        else:
            st.warning("⚠️ No valid mappings after conflict resolution. Please resolve conflicts above.")

    def render_export_page(self):
        """Render the export page."""
        st.header("💾 Export Results")

        if not st.session_state.results:
            st.warning("No results available to export.")
            return

        results = st.session_state.results

        # Export options
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 Export Formats")

            # JSON export
            if st.button("📋 Download Full Results (JSON)", type="primary"):
                json_str = json.dumps(results, indent=2)
                st.download_button(
                    label="💾 Download JSON",
                    data=json_str,
                    file_name="cde_matching_results.json",
                    mime="application/json"
                )

            # CSV export for matches
            if st.button("📊 Download Matches Table (CSV)"):
                # Combine all matches into a single DataFrame
                all_matches = []

                for match_type in ['exact', 'fuzzy', 'semantic']:
                    matches = results.get(f"{match_type}_matches", [])
                    for match in matches:
                        all_matches.append({
                            'Variable Name': match['source_field'],
                            'DigiPath CDE': match['target_item'],
                            'Confidence': match['confidence'],
                            'Match Type': match['match_type']
                        })

                if all_matches:
                    df = pd.DataFrame(all_matches)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name="cde_matches.csv",
                        mime="text/csv"
                    )

        with col2:
            st.subheader("📈 Summary Statistics")

            summary_df = pd.DataFrame([
                ["Total Variables", results['summary']['unique_source_fields']],
                ["Total DigiPath CDEs", results['summary']['unique_target_items']],
                ["Exact Matches", results['summary']['total_exact_matches']],
                ["Fuzzy Matches", results['summary']['total_fuzzy_matches']],
                ["Semantic Matches", results['summary']['total_semantic_matches']],
            ], columns=["Metric", "Value"])

            st.dataframe(summary_df, hide_index=True)

    def render_cached_results_page(self):
        """Render the cached results loading page."""
        st.header("📂 Load Cached Results")

        st.markdown("""
        Load previously saved matching results from the `output/` directory.
        These files contain pre-computed matches that can be explored without re-processing.
        """)

        # Get available cached files
        cached_files = self.get_cached_outputs()

        if not cached_files:
            st.warning("🔍 No cached result files found in the `output/` directory.")
            st.markdown("""
            **To create cached results:**
            1. Switch to "🆕 New Processing" in the sidebar
            2. Select clinical data and run matching
            3. Results will be automatically cached for future use
            """)
            return

        # File selection
        st.subheader("📋 Available Cached Results")

        selected_file = st.selectbox(
            "Select a cached result file:",
            cached_files,
            key="cached_file_selector"
        )

        if selected_file:
            # Show file info
            file_path = os.path.join("output", selected_file)
            file_stat = os.stat(file_path)
            file_size_mb = file_stat.st_size / (1024 * 1024)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 File", selected_file)
            with col2:
                st.metric("📊 Size", f"{file_size_mb:.2f} MB")
            with col3:
                import datetime
                mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                st.metric("🕒 Modified", mod_time.strftime("%Y-%m-%d %H:%M"))

            # Load button
            if st.button("🔄 Load Results", type="primary"):
                with st.spinner("Loading cached results..."):
                    results, error = self.load_cached_output(selected_file)

                    if error:
                        st.error(f"❌ Error loading cached results: {error}")
                    else:
                        # Store results in session state
                        st.session_state.results = results
                        st.session_state.processing_complete = True

                        # Show success message with summary
                        st.success("✅ Cached results loaded successfully!")

                        # Display quick summary
                        summary = results['summary']
                        total_matches = (
                            summary['total_exact_matches'] +
                            summary['total_fuzzy_matches'] +
                            summary['total_semantic_matches']
                        )

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("🎯 Exact", summary['total_exact_matches'])
                        with col2:
                            st.metric("🔍 Fuzzy", summary['total_fuzzy_matches'])
                        with col3:
                            st.metric("🧠 Semantic", summary['total_semantic_matches'])
                        with col4:
                            st.metric("📊 Total", total_matches)

                        st.info("💡 **Tip:** Use the sidebar navigation to explore the loaded results in detail.")

            # Preview section
            if st.checkbox("👀 Preview File Contents"):
                try:
                    results, error = self.load_cached_output(selected_file)
                    if not error and results:
                        with st.expander("📄 File Structure", expanded=True):
                            # Show basic structure
                            st.json({
                                "exact_matches": f"{len(results.get('exact_matches', []))} matches",
                                "fuzzy_matches": f"{len(results.get('fuzzy_matches', []))} matches",
                                "semantic_matches": f"{len(results.get('semantic_matches', []))} matches",
                                "summary": results.get('summary', {})
                            })

                        # Show sample matches
                        for match_type in ['exact_matches', 'fuzzy_matches', 'semantic_matches']:
                            matches = results.get(match_type, [])
                            if matches:
                                with st.expander(f"Sample {match_type.replace('_', ' ').title()} ({len(matches)} total)"):
                                    # Show first 3 matches
                                    sample_matches = matches[:3]
                                    for i, match in enumerate(sample_matches):
                                        st.markdown(f"**{i+1}.** `{match['source_field']}` → `{match['target_item']}` (confidence: {match['confidence']:.3f})")

                    else:
                        st.error(f"Error previewing file: {error}")
                except Exception as e:
                    st.error(f"Error previewing file: {str(e)}")

    def run(self):
        """Main application runner."""
        self.render_header()

        # Sidebar navigation
        current_page = self.render_sidebar()

        # Main content based on navigation
        if current_page == "📂 Cached Results":
            self.render_cached_results_page()
        elif current_page == "📊 Select Data" or not st.session_state.processing_complete:
            self.render_upload_page()
        elif current_page == "📊 Overview":
            self.render_overview_page()
        elif current_page == "🎯 Exact Matches":
            self.render_match_details("Exact")
        elif current_page == "🔍 Fuzzy Matches":
            self.render_match_details("Fuzzy")
        elif current_page == "🧠 Semantic Matches":
            self.render_match_details("Semantic")
        elif current_page == "📝 Manual Report":
            self.render_manual_report_page()
        elif current_page == "📈 Analytics":
            st.header("📈 Analytics Dashboard")
            st.info("Advanced analytics coming soon! This will include pattern analysis, success rates, and recommendations.")
        elif current_page == "💾 Export":
            self.render_export_page()


def main():
    """Main application entry point."""
    app = CDEBrowserApp()
    app.run()


if __name__ == "__main__":
    main()