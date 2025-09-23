# CDE Matcher Project Plan

## Phase 1: Core Matching Engine
- **Modular Matcher Architecture**
  - Abstract base matcher interface
  - Plugin system for matcher implementations:
    - ExactMatcher
    - FuzzyMatcher (multiple algorithms)
    - SemanticMatcher (embeddings)
    - Future: LLMMatcher, specialized NLP matchers
  - Matcher registry with dynamic loading
  - Configurable matcher pipelines
  - Weighted ensemble scoring

- **Data Ingestion Module**
  - Format adapter interface
  - Concrete adapters:
    - RawCSVAdapter
    - CDEFormatAdapter
    - DictionaryBasedAdapter
  - Auto-detection with confidence scoring
  - Metadata extraction pipeline

## Phase 2: Knowledge Corpus Management (JSON-Based)
- **Corpus Structure**
  ```json
  {
    "accepted_matches": {
      "cde_item": [
        {
          "variable_name": "str",
          "dataset_id": "str",
          "confidence": 0.95,
          "timestamp": "ISO-8601",
          "annotation": "str"
        }
      ]
    },
    "unmatched_variables": [
      {
        "variable_name": "str",
        "dataset_id": "str",
        "frequency": 1,
        "potential_cde": false,
        "annotation": "str",
        "similar_variables": []
      }
    ],
    "metadata": {
      "version": "1.0",
      "last_updated": "ISO-8601",
      "total_datasets_processed": 0
    }
  }
  ```

- **Corpus Operations**
  - Load/save with file locking
  - Incremental updates
  - Automatic backups
  - Query methods for historical matches
  - Pattern extraction utilities
  - Similarity clustering for unmatched variables

## Phase 3: Streamlit Interface
- **Data Upload Pipeline**
  - Format detection with override
  - Preview and validation
  - Corpus lookup for known matches

- **Match Review Workflow**
  - **Three-tier matching display**:
    - Corpus-based suggestions (highest priority)
    - Algorithm matches (scored)
    - Unmatched variables (potential CDEs)
  - **Side-by-side validation**:
    - CDE details panel
    - Variable details panel
    - Historical match info from corpus
  - **Action buttons**:
    - Accept → Update corpus
    - Reject → Track reasoning
    - Mark as new CDE candidate

- **Report Builder**
  - Two-column table: "cde" | "variable"
  - Running match count
  - Edit/remove capabilities
  - Export options (CSV, Excel, JSON)

## Phase 4: Engineering Architecture
- **Project Structure**
```
cde_matcher/
├── core/
│   ├── matchers/
│   │   ├── base.py
│   │   ├── exact.py
│   │   ├── fuzzy.py
│   │   ├── semantic.py
│   │   └── ensemble.py
│   ├── adapters/
│   │   ├── base.py
│   │   └── implementations/
│   └── corpus/
│       ├── manager.py       # JSON corpus handler
│       └── analyzer.py      # Pattern analysis
├── ui/
│   ├── components/
│   └── pages/
├── data/
│   ├── corpus.json
│   ├── corpus_backups/
│   └── cdes/
├── config/
└── tests/
```

- **Design Principles**
  - Strategy pattern for matchers
  - Factory pattern for adapters
  - Simple JSON persistence
  - Type hints throughout
  - Comprehensive docstrings

## Phase 5: Core Components

### Matcher Interface
```python
class BaseMatcher(ABC):
    @abstractmethod
    def match(self, source: str, targets: List[str]) -> List[MatchResult]:
        pass
```

### Corpus Manager
```python
class CorpusManager:
    def __init__(self, corpus_path: Path):
        self.path = corpus_path
        self.corpus = self._load_or_create()
    
    def add_match(self, cde: str, variable: str, metadata: dict):
        """Add accepted match to corpus"""
    
    def get_suggestions(self, variable: str) -> List[Match]:
        """Get historical matches for variable"""
    
    def track_unmatched(self, variable: str, metadata: dict):
        """Track unmatched variable for future CDE consideration"""
    
    def save(self):
        """Save corpus to JSON with backup"""
```

### Data Adapter Interface
```python
class BaseAdapter(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> DataFrame:
        pass
    
    @abstractmethod
    def extract_metadata(self) -> Dict:
        pass
```

## Phase 6: Advanced Features
- **Batch Processing**
  - Multiple file uploads
  - Corpus-informed suggestions
  - Confidence-based auto-accept

- **Analytics Dashboard**
  - Match success rates
  - Common unmatched patterns
  - CDE coverage metrics
  - Dataset statistics

## Technical Stack
```python
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
rapidfuzz>=3.0.0
sentence-transformers>=2.2.0
pydantic>=2.0.0
pytest>=7.0.0
filelock>=3.0.0
```

## Development Phases
1. **MVP**: Basic matching + manual validation UI
2. **Corpus Integration**: JSON corpus with historical matches
3. **Enhanced Matching**: Additional algorithms and ensemble
4. **Analytics**: Pattern detection and reporting
5. **Scale**: Batch processing and optimization

## Success Metrics
- Match accuracy rate
- Validation time per dataset
- Corpus growth and utility
- CDE coverage percentage
- New CDE discovery rate