# CDE Matcher Architecture

## Overview

The CDE Matcher is a modular system for matching variable names to Common Data Elements (CDEs) using multiple algorithms. The architecture follows the strategy pattern for matchers and provides a factory pattern for easy instantiation and configuration.

## Component Diagram

```
cde_matcher/
├── core/
│   ├── matchers/               # Matching algorithms
│   │   ├── base.py            # BaseMatcher interface & MatchResult
│   │   ├── exact.py           # Exact string matching
│   │   ├── fuzzy.py           # Fuzzy string matching (rapidfuzz)
│   │   ├── semantic.py        # Domain knowledge matching
│   │   └── factory.py         # Matcher factory & ensemble
│   ├── adapters/              # Data format handlers (future)
│   │   └── __init__.py
│   └── corpus/                # Knowledge persistence (future)
│       └── __init__.py
├── ui/                        # User interface components (future)
│   ├── components/
│   └── __init__.py
├── tests/                     # Unit and integration tests
│   ├── test_matchers/
│   └── __init__.py
├── data/                      # Sample datasets
│   ├── cdes/
│   └── samples/
├── cde_matcher_pipeline.py    # End-to-end pipeline implementation
└── scripts/                   # Legacy/reference implementations
    ├── match_seaad_digipath_fields.py
    └── view_matches_app.py
```

## Key Interfaces

### BaseMatcher Interface
Abstract base class defining the matcher contract:

```python
class BaseMatcher(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return matcher type identifier"""

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """Configure matcher with algorithm-specific parameters"""

    @abstractmethod
    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        """Match source against targets, return sorted results"""
```

### MatchResult Data Structure
Standard result format across all matchers:

```python
@dataclass
class MatchResult:
    source: str              # Original variable name
    target: str              # Matched CDE item
    confidence: float        # Match confidence (0.0-1.0)
    match_type: str          # Algorithm used ('exact', 'fuzzy', 'semantic')
    metadata: Dict[str, Any] # Algorithm-specific details
```

### Factory Pattern
Unified matcher creation and configuration:

```python
# Create individual matchers
exact = create_matcher('exact', case_sensitive=False)
fuzzy = create_matcher('fuzzy', threshold=0.8, algorithm='token_sort_ratio')
semantic = create_matcher('semantic', case_sensitive=False)

# Create ensemble
matchers = create_ensemble([
    {'type': 'exact', 'case_sensitive': False},
    {'type': 'fuzzy', 'threshold': 0.7, 'algorithm': 'ratio'}
])
```

## Implemented Components

### ✅ Exact Matcher
- **File**: `cde_matcher/core/matchers/exact.py`
- **Features**: Case-sensitive/insensitive exact string matching
- **Configuration**: `case_sensitive: bool`
- **Use Case**: Identical field names with optional case differences

### ✅ Fuzzy Matcher
- **File**: `cde_matcher/core/matchers/fuzzy.py`
- **Features**: Multiple algorithms via rapidfuzz library
- **Algorithms**: ratio, partial_ratio, token_sort_ratio, token_set_ratio
- **Configuration**:
  - `threshold: float` (0.0-1.0)
  - `algorithm: str`
  - `case_sensitive: bool`
  - `max_results: int`
- **Use Case**: Similar but not identical field names

### ✅ Semantic Matcher
- **File**: `cde_matcher/core/matchers/semantic.py`
- **Features**: Domain knowledge-based concept mapping
- **Configuration**:
  - `case_sensitive: bool`
  - `exact_only: bool`
  - `custom_mappings: Dict[str, List[str]]`
- **Use Case**: Conceptually related terms with different naming

### ✅ Pipeline Implementation
- **File**: `cde_matcher_pipeline.py`
- **Features**: End-to-end processing with all matchers
- **Input**: Source CSV (variables), Target CSV (CDEs)
- **Output**: JSON file with match results and metadata

## Data Flow

### Current Implementation
1. **Data Loading**: CSV files → pandas DataFrames
2. **Field Extraction**: Column names and CDE items → string lists
3. **Matching**: Each matcher processes source fields against targets
4. **Result Aggregation**: All match results collected with metadata
5. **Output**: JSON file with categorized matches and summary statistics

### Future Enhanced Flow
1. **Input Data** → **Data Adapter** (format detection & parsing)
2. **Adapter** → **Corpus Lookup** (check for historical matches)
3. **New Variables** → **Matcher Pipeline** (exact → fuzzy → semantic)
4. **Match Results** → **UI Validation** (user review & approval)
5. **User Decisions** → **Corpus Update** (persist accepted matches)

## Design Decisions

### ✅ Implemented Decisions
- **Strategy Pattern**: Modular matchers with common interface
- **Factory Pattern**: Unified creation and configuration
- **Type Safety**: Comprehensive type hints throughout
- **Configuration**: Extensive per-matcher customization
- **Error Handling**: Custom exceptions with clear messages
- **Performance**: rapidfuzz for optimized fuzzy matching

### 🚧 Future Decisions
- **Corpus Format**: JSON initially, may migrate to database
- **UI Framework**: Streamlit for rapid prototyping
- **Persistence**: File locking for concurrent access
- **Caching**: In-memory matcher instances and results
- **Scaling**: Parallel processing for large datasets

## Performance Characteristics

### Current Benchmarks
- **Dataset**: 66 source fields × 332 target items = 21,912 comparisons
- **Exact Matching**: ~0.1s (O(n) with set operations)
- **Fuzzy Matching**: ~2-3s (O(n²) with optimizations)
- **Semantic Matching**: ~0.5s (O(n) concept lookup)
- **Total Pipeline**: ~3-4s end-to-end

### Optimization Strategies
- **Fuzzy**: Use rapidfuzz.process.extract for top-k results
- **Semantic**: Hash-based concept lookup
- **Caching**: Reuse configured matcher instances
- **Parallelization**: Process matchers concurrently
- **Indexing**: Pre-compute embeddings for semantic matching

## Extension Points

### Adding New Matchers
1. Inherit from `BaseMatcher`
2. Implement required abstract methods
3. Register with `MatcherFactory`
4. Add configuration options
5. Include in pipeline ensemble

### Custom Semantic Mappings
```python
custom_mappings = {
    'patient_identifier': ['subject_id', 'participant_id', 'patient_id'],
    'birth_year': ['year_of_birth', 'birth_date', 'dob']
}
semantic = create_matcher('semantic', custom_mappings=custom_mappings)
```

### Pipeline Customization
```python
pipeline = CDEMatcherPipeline()
pipeline.configure_matchers(
    exact_config={'case_sensitive': False},
    fuzzy_config={'threshold': 0.8, 'algorithm': 'token_sort_ratio'},
    semantic_config={'exact_only': True}
)
```

## User Interface Layer

### Streamlit Browser Application
The `cde_browser_app.py` provides a complete web-based interface for CDE matching:

```
┌─────────────────────────────────────────────────────────────┐
│                    CDE Matcher Browser                      │
├─────────────────────────────────────────────────────────────┤
│ Sidebar:                    │ Main Content:                 │
│ ┌─────────────────────────┐ │ ┌───────────────────────────┐ │
│ │ Data Source Selection   │ │ │ File Selection            │ │
│ │ ├─ New Processing       │ │ │ ├─ Clinical Data Files    │ │
│ │ └─ Cached Results       │ │ │ └─ DigiPath CDEs (auto)   │ │
│ │                         │ │ └───────────────────────────┘ │
│ │ Matcher Configuration   │ │ ┌───────────────────────────┐ │
│ │ ├─ Exact Settings       │ │ │ Match Results             │ │
│ │ ├─ Fuzzy Parameters     │ │ │ ├─ Overview Dashboard     │ │
│ │ └─ Semantic Options     │ │ │ ├─ Interactive Selection  │ │
│ │                         │ │ │ └─ Manual Report Builder  │ │
│ │ Navigation (5 selected) │ │ └───────────────────────────┘ │
│ │ ├─ Overview             │ │                               │
│ │ ├─ Exact Matches        │ │                               │
│ │ ├─ Fuzzy Matches        │ │                               │
│ │ ├─ Semantic Matches     │ │                               │
│ │ ├─ Manual Report (5)    │ │                               │
│ │ └─ Export Options       │ │                               │
│ └─────────────────────────┘ │                               │
└─────────────────────────────────────────────────────────────┘
```

### Interactive Match Selection

#### Data Editor Interface
Each match type (Exact, Fuzzy, Semantic) displays results in an interactive `st.data_editor`:

```python
# Interactive match selection with real-time updates
edited_df = st.data_editor(
    df[['Select', 'Variable', 'DigiPath CDE', 'Confidence', 'Match Type']],
    column_config={
        "Select": st.column_config.CheckboxColumn("Select")
    }
)
```

#### Selection Management
- **Individual Selection**: Checkbox per match
- **Bulk Operations**: Select All, Deselect All, High Confidence
- **Persistence**: Session state maintains selections across navigation
- **Real-time Feedback**: Selection count badges and metrics

### Manual Report Builder

#### Conflict Resolution System
```python
# Detect conflicts (same variable → multiple CDEs)
variable_mappings = {}
conflicts = []
for match in selected_matches:
    var, cde = match['variable'], match['cde']
    if var in variable_mappings and variable_mappings[var] != cde:
        conflicts.append(var)
```

#### Report Generation Pipeline
```
User Selections → Conflict Detection → Resolution Interface → Final Report → CSV Download
```

### Session State Architecture

#### Data Persistence
```python
st.session_state = {
    'results': {...},                    # Pipeline results
    'selected_matches': [...],           # User selections
    'manual_report': {...},             # Report metadata
    'processing_complete': bool,         # Navigation state
    'matcher_config': {...}             # Algorithm parameters
}
```

#### State Management Pattern
- **Initialization**: Check and create missing state variables
- **Updates**: Immediate updates on user interactions
- **Validation**: Ensure state consistency across navigation
- **Cleanup**: Reset on new data processing

### Integration with Pipeline

#### Data Flow
```
Clinical Data Files → Streamlit Interface → CDEMatcherPipeline → Results → Interactive Selection → Manual Report
```

#### Configuration Bridging
```python
# UI configuration passed to pipeline
results = pipeline.run_pipeline(
    source_path=variables_file,
    target_path=digipath_cdes,
    exact_config=st.session_state.matcher_config['exact'],
    fuzzy_config=st.session_state.matcher_config['fuzzy'],
    semantic_config=st.session_state.matcher_config['semantic']
)
```

## Future Architecture Enhancements

### Planned Extensions
- **Corpus Integration**: Historical match lookup and storage
- **Batch Processing**: Multiple file upload and processing
- **Advanced Analytics**: Match quality insights and recommendations
- **API Layer**: REST endpoints for external integrations

This architecture provides a solid foundation for CDE matching while maintaining flexibility for future enhancements and domain-specific customizations. The addition of the interactive user interface enables practical deployment and manual curation workflows.
