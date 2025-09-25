"""
Dataset Selection Component for CDE Matcher UI.

Handles dataset selection, preview, and extraction method configuration.
"""

import streamlit as st
import pandas as pd
import os
import sys
from typing import Dict, List, Any, Optional, Tuple

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cde_matcher.core.data_adapter import get_data_adapter, get_data_paths


class DatasetSelector:
    """Component for selecting and configuring datasets."""

    def __init__(self):
        self.data_adapter = get_data_adapter()
        self.data_paths = get_data_paths()
        self.clinical_data_dir = self.data_paths['clinical_data']

    def get_clinical_data_files(self) -> List[str]:
        """Get list of available clinical data files."""
        return self.data_adapter.list_files(self.clinical_data_dir, "*.csv")

    def load_clinical_data_file(self, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load a specific clinical data file."""
        try:
            file_path = self.data_adapter.get_full_path(self.clinical_data_dir, filename)
            df = self.data_adapter.read_csv(file_path)
            return df, None
        except Exception as e:
            return None, str(e)

    def analyze_dataset_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
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

    def preview_variable_extraction(self, df: pd.DataFrame, method: str, column: str = None) -> Tuple[List[str], int, Optional[str]]:
        """Preview what variables would be extracted with given method."""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from cde_matcher.core.pipeline import extract_variables_flexible
            variables = extract_variables_flexible(df, method, column)
            return variables[:20], len(variables), None  # Show first 20, total count, no error
        except Exception as e:
            return [], 0, str(e)

    def render_file_selection(self) -> Optional[str]:
        """Render file selection interface."""
        st.subheader("📁 Select Clinical Data File")

        files = self.get_clinical_data_files()
        if not files:
            data_path_display = self.clinical_data_dir
            st.error(f"No CSV files found in `{data_path_display}` directory.")
            st.info(f"Please add your clinical data CSV files to the `{data_path_display}` directory.")
            return None

        selected_file = st.selectbox(
            "Choose a clinical data file:",
            options=[None] + files,
            index=0,
            format_func=lambda x: "-- Select a file --" if x is None else x,
            help="Select the clinical data file you want to process"
        )

        return selected_file

    def render_dataset_preview(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Render dataset preview with structure analysis."""
        st.subheader(f"📊 Dataset Preview: {filename}")

        # Basic info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Rows", df.shape[0])
        with col2:
            st.metric("📋 Columns", df.shape[1])
        with col3:
            memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("💾 Memory", f"{memory_mb:.1f} MB")

        # Data preview
        with st.expander("👀 Data Preview", expanded=True):
            st.dataframe(df.head(10), width='stretch')

        # Analyze structure
        analysis = self.analyze_dataset_structure(df)

        # Show column information
        with st.expander("📋 Column Information"):
            col_info = []
            for col in df.columns:
                col_info.append({
                    'Column': col,
                    'Type': str(df[col].dtype),
                    'Non-null': df[col].notna().sum(),
                    'Null %': f"{(df[col].isna().sum() / len(df) * 100):.1f}%",
                    'Unique': df[col].nunique()
                })

            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, hide_index=True, width='stretch')

        return analysis

    def render_extraction_method_selection(self, analysis: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Render extraction method selection interface."""
        st.subheader("🎯 Variable Extraction Method")

        # Show suggested method
        if analysis['suggested_method'] == 'column_values':
            st.success(f"💡 **Suggested**: Use column values method with '{analysis['suggested_column']}' column")
        else:
            st.info("💡 **Suggested**: Use column headers method (variables are column names)")

        # Method selection
        method = st.radio(
            "How should variables be extracted?",
            options=['columns', 'column_values'],
            format_func=lambda x: {
                'columns': '📋 Column Headers (variables are column names)',
                'column_values': '📝 Column Values (variables are in a specific column)'
            }[x],
            index=0 if analysis['suggested_method'] == 'columns' else 1,
            help="Choose how to extract variable names from your data"
        )

        column_name = None
        if method == 'column_values':
            # Show potential variable columns if found
            if analysis['potential_variable_columns']:
                st.write("**Potential variable columns found:**")
                for pot_col in analysis['potential_variable_columns']:
                    st.write(f"• **{pot_col['column']}** ({pot_col['unique_values']} unique values)")
                    st.write(f"  Sample: {', '.join(map(str, pot_col['sample_values'][:3]))}...")

            # Column selection
            column_name = st.selectbox(
                "Select the column containing variable names:",
                options=analysis['columns'],
                index=analysis['columns'].index(analysis.get('suggested_column', analysis['columns'][0]))
                      if analysis.get('suggested_column') in analysis['columns'] else 0
            )

        return method, column_name


    def render_change_dataset_button(self, has_results: bool = False) -> bool:
        """Render change dataset button with confirmation if needed."""
        # Initialize confirmation state
        if 'show_change_dataset_confirmation' not in st.session_state:
            st.session_state.show_change_dataset_confirmation = False

        if has_results:
            # Show confirmation dialog if triggered
            if st.session_state.show_change_dataset_confirmation:
                st.warning("⚠️ **Warning**: Changing the dataset will clear all current results and selections.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Change Dataset", type="primary", key="confirm_change"):
                        st.session_state.show_change_dataset_confirmation = False
                        return True
                with col2:
                    if st.button("❌ Cancel", type="secondary", key="cancel_change"):
                        st.session_state.show_change_dataset_confirmation = False
                        return False
            else:
                # Show initial change button
                if st.button("🔄 Change Dataset", type="secondary", help="⚠️ This will clear current results", key="change_dataset_btn"):
                    st.session_state.show_change_dataset_confirmation = True
                    st.rerun()
        else:
            if st.button("🔄 Change Dataset", type="secondary", help="Select a different dataset", key="change_dataset_simple"):
                return True
        return False

    def render_dataset_selection_flow(self) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str], Optional[str]]:
        """Render complete dataset selection flow."""
        # File selection
        selected_file = self.render_file_selection()
        if not selected_file:
            return None, None, None, None

        # Load and preview dataset
        df, error = self.load_clinical_data_file(selected_file)
        if error:
            st.error(f"❌ Error loading file: {error}")
            return None, None, None, None

        if df is None:
            st.error("❌ Failed to load dataset")
            return None, None, None, None

        # Dataset preview
        analysis = self.render_dataset_preview(df, selected_file)

        # Method selection
        method, column_name = self.render_extraction_method_selection(analysis)

        # Validate extraction method
        try:
            variables, total_count, error = self.preview_variable_extraction(df, method, column_name)
            if error:
                st.error(f"❌ Error in extraction: {error}")
                return None, None, None, None
            if not variables:
                st.warning("⚠️ No variables would be extracted with this method")
                return None, None, None, None
        except Exception as e:
            st.error(f"❌ Cannot validate extraction settings: {e}")
            return None, None, None, None

        return df, selected_file, method, column_name