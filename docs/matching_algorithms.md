# Matching Algorithms

## ✅ Exact Matcher (`ExactMatcher`)
- **Purpose**: Find identical strings with optional case insensitivity
- **Implementation**: Set-based O(n) comparison using Python's built-in string matching
- **File**: `cde_matcher/core/matchers/exact.py`
- **Configuration**:
  - `case_sensitive: bool` - Whether to match case exactly (default: True)
- **Performance**: ~0.1s for 66×332 comparisons
- **Use Case**: Variables with identical names but potentially different case

### Example Usage
```python
exact = create_matcher('exact', case_sensitive=False)
results = exact.match("Age_at_Death", ["age_at_death", "birth_date"])
# Returns: [MatchResult(source="Age_at_Death", target="age_at_death", confidence=1.0)]
```

## ✅ Fuzzy Matcher (`FuzzyMatcher`)
- **Purpose**: Find similar strings using edit distance algorithms
- **Library**: rapidfuzz (high-performance C++ implementation)
- **File**: `cde_matcher/core/matchers/fuzzy.py`
- **Algorithms**:
  - `ratio`: Basic Levenshtein ratio
  - `partial_ratio`: Best partial match ratio
  - `token_sort_ratio`: Ratio after sorting tokens
  - `token_set_ratio`: Ratio after token set operations
- **Configuration**:
  - `threshold: float` - Minimum similarity (0.0-1.0, default: 0.7)
  - `algorithm: str` - Algorithm choice (default: 'ratio')
  - `case_sensitive: bool` - Case sensitivity (default: False)
  - `max_results: int` - Result limit (default: None)
- **Performance**: ~2-3s for 66×332 comparisons with optimizations
- **Use Case**: Variables with minor spelling differences or variations

### Example Usage
```python
fuzzy = create_matcher('fuzzy', threshold=0.8, algorithm='token_sort_ratio')
results = fuzzy.match("age_death", ["age_at_death", "death_age", "birth_date"])
# Returns matches above threshold with confidence scores
```

### Algorithm Comparison
| Algorithm | Use Case | Example |
|-----------|----------|---------|
| `ratio` | General similarity | "age_death" vs "age_at_death" |
| `partial_ratio` | Substring matching | "age" vs "age_at_death" |
| `token_sort_ratio` | Word order insensitive | "death age" vs "age death" |
| `token_set_ratio` | Extra words tolerant | "patient age" vs "age" |

## ✅ Semantic Matcher (`SemanticMatcher`)
- **Purpose**: Find conceptually similar terms using domain knowledge
- **Method**: Pre-defined concept mappings for biomedical terms
- **File**: `cde_matcher/core/matchers/semantic.py`
- **Configuration**:
  - `case_sensitive: bool` - Case sensitivity (default: False)
  - `exact_only: bool` - Only exact semantic matches (default: False)
  - `custom_mappings: Dict[str, List[str]]` - Additional concept mappings
- **Performance**: ~0.5s for 66×332 comparisons
- **Use Case**: Variables representing same concept with different terminology

### Built-in Concept Mappings
```python
# Example mappings included in SemanticMatcher
{
    'donor_id': ['participant_id', 'BB_id', 'additional_ID', 'subject_id'],
    'age_at_death': ['age_at_death', 'age_at_onset', 'death_age'],
    'sex': ['sex', 'gender'],
    'apoe_genotype': ['apoe_genotype', 'genetics_screening', 'apoe'],
    'brain_ph': ['brain_ph', 'ph', 'tissue_ph'],
    # ... 20+ biomedical concepts
}
```

### Example Usage
```python
# Using built-in mappings
semantic = create_matcher('semantic', case_sensitive=False)
results = semantic.match("donor id", ["participant_id", "subject_id"])

# Adding custom mappings
custom_mappings = {
    'patient_identifier': ['patient_id', 'pid', 'medical_record_number']
}
semantic = create_matcher('semantic', custom_mappings=custom_mappings)
```

## ✅ Factory Pattern & Ensemble Support
- **File**: `cde_matcher/core/matchers/factory.py`
- **Purpose**: Unified matcher creation and ensemble processing
- **Features**:
  - Dynamic matcher instantiation
  - Configuration validation
  - Multi-matcher ensemble creation
  - Registry pattern for extensibility

### Example Ensemble Usage
```python
# Create ensemble of multiple matchers
ensemble_configs = [
    {'type': 'exact', 'case_sensitive': False},
    {'type': 'fuzzy', 'threshold': 0.8, 'algorithm': 'token_sort_ratio'},
    {'type': 'semantic', 'exact_only': False}
]
matchers = create_ensemble(ensemble_configs)

# Process with all matchers
all_results = []
for matcher in matchers:
    results = matcher.match(source, targets)
    all_results.extend(results)
```

## 🚧 Future Algorithms (Planned)

### LLM-based Matcher
- **Purpose**: Context-aware semantic matching using large language models
- **Method**: Prompt-based similarity assessment
- **Use Case**: Complex domain-specific terminology

### Embedding-based Semantic Matcher
- **Purpose**: Vector similarity using pre-trained embeddings
- **Models**: sentence-transformers, BioBERT, ClinicalBERT
- **Method**: Cosine similarity of sentence embeddings

### Ensemble Scorer with Weighted Voting
- **Purpose**: Combine multiple matcher results with learned weights
- **Method**: Weighted average or machine learning-based scoring
- **Training**: Historical match acceptance data

## Performance Benchmarks

### Test Dataset: SEA-AD (66 fields) vs DigiPath (332 items)

| Matcher | Processing Time | Matches Found | Avg Confidence |
|---------|----------------|---------------|----------------|
| Exact | ~0.1s | 1 | 1.000 |
| Fuzzy (threshold=0.7) | ~2-3s | 6 | 0.825 |
| Semantic | ~0.5s | 56 | 0.891 |
| **Total Pipeline** | **~3-4s** | **63 unique** | **0.847** |

### Optimization Strategies
- **Fuzzy**: Use `rapidfuzz.process.extract` for top-k results
- **Semantic**: Hash-based concept lookup with O(1) access
- **Ensemble**: Parallel processing of independent matchers
- **Caching**: Reuse configured matcher instances