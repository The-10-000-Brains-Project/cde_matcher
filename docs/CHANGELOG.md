# Changelog

## [Unreleased]
- Working on: Unit tests and corpus management

## [0.5.0] - 2024-09-23
### Major Refactor: Modular Component Architecture
- **BREAKING**: Complete UI refactor from monolithic to modular design
- **BREAKING**: File locations changed: `cde_browser_app.py` → `ui/browser_app.py`, `cde_matcher_pipeline.py` → `cde_matcher/core/pipeline.py`
- **BREAKING**: Output directory moved from `output/` → `data/output/`

### Added
- **Modular UI Components**: Four specialized, reusable components
  - `DatasetSelector`: File selection, preview, and extraction method configuration
  - `MatcherConfig`: Interactive algorithm parameter tuning with real-time examples
  - `ResultsViewer`: Overview dashboard, detailed views, and advanced analytics
  - `ReportBuilder`: Manual curation, conflict resolution, and export functionality
- **Enhanced User Experience**: Improved interaction flows and validation
  - No default dataset selection - users must actively choose files
  - Proper confirmation dialogs for dataset changes with session state management
  - Streamlined interface without redundant extraction preview
- **Smart Caching System**: Configuration-based file management
  - MD5 hash-based file naming prevents duplicate processing
  - Automatic detection and reuse of existing results with identical configurations
  - Cached results saved to organized `data/output/` directory
- **Flexible Data Handling**: Enhanced support for multiple clinical data formats
  - Column headers extraction for raw clinical data
  - Data dictionary extraction from specific columns (variable_name, Field, etc.)
  - Dataset structure analysis with extraction method suggestions
- **Advanced Analytics**: Enhanced results visualization and insights
  - Confidence distribution charts with median indicators
  - Algorithm performance comparison with dual-axis plots
  - Coverage analysis and match quality breakdowns

### Enhanced
- **Repository Organization**: Clean, professional structure following Python packaging conventions
  - Proper package structure with `__init__.py` files and exports
  - Comprehensive `.gitignore` for Python development
  - All business logic separated from UI components
- **Code Quality**: Modernized Streamlit usage and error handling
  - Fixed all deprecated `use_container_width` → `width='stretch'` warnings
  - Improved error handling with informative user messages
  - Better session state management and component isolation
- **Documentation**: Updated all documentation to reflect modular architecture
  - README.md updated with new launch commands and structure
  - DEVELOPMENT.md enhanced with refactor details and component descriptions
  - Architecture documentation updated with component responsibilities

### Technical Improvements
- **Maintainability**: 1,500+ line monolithic app reduced to 400-line main app + 4 focused components
- **Testability**: Components can now be tested and developed independently
- **Reusability**: UI components can be used in other interfaces or applications
- **Performance**: Eliminated temporary file creation through DataFrame-based processing

### Changed
- Launch command: `streamlit run cde_browser_app.py` → `streamlit run ui/browser_app.py`
- Import paths: `from cde_matcher_pipeline import` → `from cde_matcher.core.pipeline import`
- Output location: Results now saved to `data/output/` for better organization
- Component access: UI components available via `from ui.components import DatasetSelector, MatcherConfig, ResultsViewer, ReportBuilder`

## [0.4.0] - 2024-09-19
### Added
- **Interactive Streamlit Browser Application**: Complete web-based interface for CDE matching
  - Real-time data processing with progress tracking
  - File selection from local `data/clinical_data/` directory
  - Interactive matcher configuration with live parameter tuning
  - Multiple result views: Overview, Exact, Fuzzy, Semantic matches
- **Manual Match Selection System**: User-driven curation workflows
  - Interactive data editor with checkbox selection for each match
  - Bulk selection operations: Select All, Deselect All, High Confidence matches
  - Session state persistence across navigation tabs
  - Real-time selection count badges and metrics
- **Manual Report Builder**: Comprehensive report generation and management
  - Conflict detection for variables mapped to multiple CDEs
  - Interactive conflict resolution with Keep/Remove options
  - Editable final report table with validation
  - 2-column CSV download (CDE, Variable) with timestamped filenames
- **Cached Results Support**: Load and browse previously processed results
  - Automatic detection of JSON files in `data/output/` directory
  - Backward compatibility with older result formats
  - File preview and metadata display
  - Seamless integration with manual selection workflows
- **Enhanced Session Management**: Robust state persistence and navigation
  - Multi-page navigation with selection count tracking
  - Configuration bridging between UI and pipeline
  - Stable radio button navigation (fixed label issues)

### Enhanced
- **User Experience**: Improved visual design and interaction patterns
  - Fixed white-on-white text visibility issues
  - Replaced deprecated `use_container_width` with `width='stretch'`
  - Clear visual feedback for selection states and processing status
  - Intuitive navigation flow with contextual help messages
- **Data Flow Architecture**: Streamlined processing pipeline integration
  - Direct integration between Streamlit UI and CDEMatcherPipeline
  - Real-time configuration passing from UI to matching algorithms
  - Temporary file management for processing workflows

### Performance
- **Session State Optimization**: Efficient selection tracking and updates
  - Immediate state updates on user interactions
  - Optimized conflict detection and resolution algorithms
  - Memory-efficient storage of match metadata and selections

## [0.3.0] - 2024-01-20
### Added
- **Modular Architecture**: Complete rewrite with strategy and factory patterns
- **FuzzyMatcher**: High-performance fuzzy matching using rapidfuzz library
  - Multiple algorithms: ratio, partial_ratio, token_sort_ratio, token_set_ratio
  - Configurable thresholds and result limits
  - Optimized top-k search capabilities
- **SemanticMatcher**: Domain knowledge-based concept mapping
  - 20+ built-in biomedical concept mappings
  - Custom mapping support
  - Partial and exact semantic matching options
- **MatcherFactory**: Unified creation and configuration system
  - Dynamic matcher instantiation
  - Ensemble support for multiple matchers
  - Configuration validation and error handling
- **CDEMatcherPipeline**: End-to-end processing workflow
  - CSV data loading and field extraction
  - Multi-algorithm matching with result aggregation
  - JSON output with comprehensive metadata
- **Comprehensive Documentation**:
  - Architecture overview with component diagrams
  - Detailed algorithm specifications
  - Usage examples and configuration guides
  - Development roadmap and implementation status

### Enhanced
- **ExactMatcher**: Improved with better configuration and performance
- **MatchResult**: Enhanced dataclass with validation and metadata
- **Error Handling**: Custom exceptions with clear messages
- **Type Safety**: 100% type hints coverage throughout codebase

### Performance
- **Benchmarks**: 66×332 comparisons in ~3-4s total pipeline time
- **Optimizations**: Set-based exact matching, rapidfuzz optimizations
- **Scalability**: Designed for larger datasets with caching strategies

### Changed
- Removed SEA-AD specific references for generic reusability
- Migrated from monolithic scripts to modular package structure
- Updated all documentation to reflect current implementation

## [0.2.0] - 2024-01-15
### Added
- JSON corpus manager with file locking
- Corpus backup system
### Changed
- Switched from SQLite to JSON for corpus storage

## [0.1.0] - 2024-01-10
### Added
- Base matcher interface
- Exact matcher implementation
- Basic Streamlit UI