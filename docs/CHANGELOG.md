# Changelog

## [Unreleased]
- Working on: Unit tests and corpus management

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