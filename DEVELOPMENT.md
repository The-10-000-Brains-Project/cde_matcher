# DEVELOPMENT.md

# CDE Matcher Development Guide

This guide provides strategies for developing the CDE Matcher project, particularly when working with Claude Code or similar AI coding assistants.

## Development Philosophy

- **Simplicity First**: Each component should do one thing well
- **Test-Driven**: Write test specifications before implementation
- **Incremental**: Build in small, verifiable steps
- **Type-Safe**: Use type hints throughout for clarity
- **Modular**: Keep components loosely coupled and independently testable

## Project Structure

```
cde_matcher/
├── core/                 # Business logic (no UI dependencies)
│   ├── matchers/        # Matching algorithms
│   ├── adapters/        # Data format parsers
│   └── corpus/          # Corpus management
├── ui/                  # Streamlit interface
├── data/                # Sample data and corpus storage
├── config/              # Configuration management
├── tests/               # Unit tests mirroring src structure
└── prompts/             # Claude Code prompt templates
```

## Phase-Based Development Approach

### ✅ Phase 1: Core Infrastructure (COMPLETED)
**Implementation**: `cde_matcher/core/matchers/base.py`
- ✅ BaseMatcher abstract interface with type hints
- ✅ MatchResult dataclass with validation
- ✅ Custom exceptions (MatcherError, ConfigurationError, MatchingError)
- ✅ Input validation and result sorting utilities

### ✅ Phase 2: Matching Algorithms (COMPLETED)
**Implementations**:
- ✅ **ExactMatcher** (`cde_matcher/core/matchers/exact.py`) - Case-sensitive/insensitive exact matching
- ✅ **FuzzyMatcher** (`cde_matcher/core/matchers/fuzzy.py`) - Using rapidfuzz with multiple algorithms
- ✅ **SemanticMatcher** (`cde_matcher/core/matchers/semantic.py`) - Domain knowledge mappings
- ✅ **MatcherFactory** (`cde_matcher/core/matchers/factory.py`) - Dynamic matcher creation and ensemble support

### 🚧 Phase 3: Corpus Management (NEXT)
**Status**: Not yet implemented
```markdown
Prompt: "Create a JSON-based corpus manager with file locking for concurrent
access. Include methods to add matches, query history, and track unmatched
variables. Implement automatic backups."

Focus: Reliable persistence
```

### 🚧 Phase 4: Data Adapters (FUTURE)
**Status**: Basic CSV handling in pipeline, needs formalization
```markdown
Prompt: "Build adapter for raw CSV files. Extract column headers and sample
values. Include type inference and basic statistics."

Focus: One format at a time
```

### ✅ Phase 5: Streamlit Interface (COMPLETED)
**Status**: Fully integrated with manual match selection and flexible data handling
**Implementation**: `cde_browser_app.py`
- ✅ **File Selection Interface**: Load clinical data from `data/clinical_data/`
- ✅ **Flexible Data Preview**: Preview file structure and suggest extraction methods
- ✅ **Dataset Switching**: Change datasets with confirmation dialogs
- ✅ **Real-time Processing**: Interactive configuration and immediate results
- ✅ **Manual Match Selection**: Interactive data editor with checkboxes for each match
- ✅ **Conflict Resolution**: Detect and resolve variables mapped to multiple CDEs
- ✅ **Report Generation**: 2-column CSV download (CDE, Variable)
- ✅ **Session State Management**: Persistent selections across navigation
- ✅ **Multi-view Interface**: Overview, match details, and manual report builder
- ✅ **Smart Caching**: Configuration-based file management with hash naming

## Current Implementation Status

### ✅ Working Components

#### Matchers
All matchers implement the `BaseMatcher` interface and can be created via the factory pattern:

```python
from cde_matcher.core.matchers import create_matcher

# Create individual matchers
exact = create_matcher('exact', case_sensitive=False)
fuzzy = create_matcher('fuzzy', threshold=0.8, algorithm='token_sort_ratio')
semantic = create_matcher('semantic', case_sensitive=False)

# Use matchers
results = fuzzy.match("age_death", ["age_at_death", "death_age"])
```

#### Pipeline
The `CDEMatcherPipeline` in `cde_matcher_pipeline.py` provides end-to-end functionality with flexible data handling:

```python
from cde_matcher_pipeline import CDEMatcherPipeline

pipeline = CDEMatcherPipeline()

# Configure matchers
pipeline.configure_matchers(
    exact_config={"case_sensitive": False},
    fuzzy_config={"threshold": 0.7, "algorithm": "token_sort_ratio"},
    semantic_config={"case_sensitive": False, "exact_only": False}
)

# Flexible variable extraction
results = pipeline.run_pipeline(
    source_path="path/to/variables.csv",
    target_path="path/to/cdes.csv",
    source_method="columns",  # or "column_values"
    source_column=None        # or specific column name
)

# DataFrame-based processing (eliminates temp files)
results = pipeline.run_pipeline_from_dataframes(
    source_df=source_dataframe,
    target_df=target_dataframe,
    source_name="dataset_name",
    target_name="target_name"
)
```

### 📊 Test Results
Working with SEA-AD Cohort Metadata (66 fields) vs DigiPath CDEs (332 items):
- **Exact matches**: 1
- **Fuzzy matches**: 6 (threshold=0.7)
- **Semantic matches**: 56

### 🔧 Configuration Options

#### ExactMatcher
- `case_sensitive: bool` - Case sensitivity (default: True)

#### FuzzyMatcher
- `threshold: float` - Minimum similarity (0.0-1.0, default: 0.7)
- `algorithm: str` - Algorithm type ('ratio', 'partial_ratio', 'token_sort_ratio', 'token_set_ratio')
- `case_sensitive: bool` - Case sensitivity (default: False)
- `max_results: int` - Limit results (default: None)

#### SemanticMatcher
- `case_sensitive: bool` - Case sensitivity (default: False)
- `exact_only: bool` - Exact semantic matches only (default: False)
- `custom_mappings: Dict` - Additional concept mappings (default: None)

#### Streamlit Browser App
The `cde_browser_app.py` provides a complete development interface:

```python
# Launch the application
streamlit run cde_browser_app.py
```

Features:
- **Data Source Selection**: Choose between new processing or cached results
- **Flexible Data Handling**: Support for column headers and data dictionary formats
- **Dataset Preview**: Preview file structure with extraction method suggestions
- **Interactive Configuration**: Real-time matcher parameter tuning
- **Manual Curation**: Select matches using checkboxes and bulk operations
- **Conflict Management**: Resolve variables mapped to multiple CDEs
- **Report Export**: Download 2-column CSV reports
- **Navigation**: Sidebar with selection count badges
- **Smart Caching**: Automatic file deduplication with configuration hashing

### 🎯 Next Development Priorities

1. **Unit Tests** - Comprehensive test suite for all matchers
2. **Corpus Manager** - JSON-based persistence with file locking
3. **Data Adapters** - Formalized CSV and other format handlers
4. **Performance** - Optimization for large datasets
5. **Advanced Analytics** - Match quality insights and recommendations

## Working with Claude Code

### Effective Prompting Strategies

1. **Provide Context**
   - Current project state
   - Specific file being worked on
   - Dependencies available

2. **Be Specific**
   - One feature per prompt
   - Clear acceptance criteria
   - Expected input/output examples

3. **Include Constraints**
   - Line count limits (~100-150 lines)
   - Required libraries
   - Performance considerations

### Example Development Session

```markdown
## Context
We're building a CDE matcher. The base matcher interface is complete.

## Current Task
Add a fuzzy string matcher implementation.

## Requirements
- Inherit from BaseMatcher
- Use rapidfuzz library
- Configurable threshold (0.0 to 1.0)
- Return top N matches with scores
- Include method to configure algorithm type

## Constraints
- Keep under 150 lines
- Include docstrings with examples
- Add at least 5 unit tests
```

## Test-First Development

### Test Specification Template
```python
"""
Test <ComponentName> should:
1. [Behavior 1]
2. [Behavior 2]
3. [Edge case handling]
4. [Error conditions]

Example test case:
- Input: [specific input]
- Expected: [specific output]
"""
```

### Testing Strategy
- Write test specifications first
- Implement minimal code to pass tests
- Refactor for clarity
- Add edge cases
- Aim for >80% coverage

## Incremental Feature Development

### Feature Size Guidelines
- **Single File**: One matcher, one adapter, one UI component
- **<200 Lines**: Including docstrings and type hints
- **Single Responsibility**: Each class/function has one job
- **Testable**: Can be tested in isolation

### Progressive Enhancement Pattern
```
Version 1: Exact matching only
Version 2: Add fuzzy matching
Version 3: Add corpus lookup
Version 4: Add semantic matching
Version 5: Add batch processing
```

## Code Standards

### Type Hints
```python
from typing import List, Dict, Optional, Protocol
from dataclasses import dataclass

@dataclass
class MatchResult:
    source: str
    target: str
    confidence: float
    metadata: Dict[str, any]
```

### Documentation
```python
def match(self, source: str, targets: List[str]) -> List[MatchResult]:
    """
    Match source against targets using fuzzy string matching.
    
    Args:
        source: Variable name to match
        targets: List of CDE items
        
    Returns:
        Sorted list of matches above threshold
        
    Example:
        >>> matcher.match("age_death", ["age_at_death", "death_age"])
        [MatchResult(source="age_death", target="age_at_death", confidence=0.9)]
    """
```

### Error Handling
```python
# Define specific exceptions
class MatcherError(Exception):
    """Base exception for matchers"""

class CorpusError(Exception):
    """Corpus operation errors"""

# Use them for clear error messages
if threshold < 0 or threshold > 1:
    raise MatcherError(f"Threshold must be between 0 and 1, got {threshold}")
```

## Configuration Management

### Environment Variables
```bash
# .env.example
CORPUS_PATH=data/corpus.json
BACKUP_COUNT=5
FUZZY_THRESHOLD=0.7
SEMANTIC_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

### Settings Class
```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    corpus_path: str = "data/corpus.json"
    backup_count: int = 5
    fuzzy_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
```

## Development Workflow

1. **Start Small**: Implement minimal viable feature
2. **Test It**: Write and run tests
3. **Refactor**: Clean up code, add docs
4. **Integrate**: Connect to existing components
5. **Document**: Update relevant documentation
6. **Commit**: Small, focused commits

## Common Patterns

### Factory Pattern for Matchers
```python
class MatcherFactory:
    @staticmethod
    def create(matcher_type: str) -> BaseMatcher:
        if matcher_type == "exact":
            return ExactMatcher()
        elif matcher_type == "fuzzy":
            return FuzzyMatcher()
        raise ValueError(f"Unknown matcher: {matcher_type}")
```

### Repository Pattern for Corpus
```python
class CorpusRepository:
    def add(self, item: AcceptedMatch) -> None
    def find(self, criteria: Dict) -> List[AcceptedMatch]
    def update(self, item: AcceptedMatch) -> None
    def delete(self, id: str) -> None
```

## Performance Considerations

- Cache matcher instances
- Batch corpus writes
- Use session state in Streamlit
- Lazy load large models
- Index corpus for fast lookups

## Debugging Tips

1. **Logging**: Use structured logging for all operations
2. **Validation**: Validate inputs with Pydantic
3. **Assertions**: Add assertions for invariants
4. **Breakpoints**: Use interactive debugging
5. **Sample Data**: Keep minimal test datasets

## Next Steps

### Immediate (Phase 3)
1. **Unit Tests**: Create comprehensive test suite for all matchers
   - Test exact, fuzzy, and semantic matchers
   - Test factory pattern and error handling
   - Add integration tests for pipeline

2. **Corpus Manager**: Implement JSON-based persistence
   - File locking for concurrent access
   - Methods to add/query matches and track unmatched variables
   - Automatic backups and versioning

### Short Term (Phase 4)
3. **Data Adapters**: Formalize data ingestion
   - CSV adapter with metadata extraction
   - Support for different CDE formats
   - Type inference and validation

4. **Enhanced Pipeline**: Add corpus integration
   - Historical match lookup
   - Confidence-based auto-accept
   - Batch processing capabilities

### Medium Term (Phase 6)
5. **Advanced UI Features**: Enhanced Streamlit functionality
   - Batch file processing
   - Advanced filtering and search
   - Match validation workflows
   - Corpus management interface

6. **Performance Optimization**
   - Caching and indexing for large datasets
   - Parallel processing options
   - Memory-efficient algorithms

### Future Enhancements
7. **Advanced Matchers**: Additional algorithms
   - Embedding-based semantic matching
   - Domain-specific matchers
   - Ensemble voting mechanisms

8. **Analytics**: Match quality insights
   - Success rate tracking
   - Pattern analysis
   - Recommendation systems

Remember: Build working software incrementally. Each piece should be complete and tested before moving to the next. The current modular architecture provides a solid foundation for all future enhancements.