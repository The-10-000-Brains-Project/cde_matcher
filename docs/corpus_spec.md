# Corpus Specification

## Purpose
Track accepted matches and unmatched variables for learning.

## JSON Structure
```json
{
  "version": "1.0",
  "accepted_matches": {},
  "unmatched_variables": [],
  "metadata": {}
}
```

## Operations
- `add_match()` - [Implementation details TBD]
- `query_matches()` - [Implementation details TBD]
- `add_unmatched()` - [Implementation details TBD]

## File Management
- Location: `data/corpus.json`
- Backup strategy: [TBD]
- Locking mechanism: [TBD]