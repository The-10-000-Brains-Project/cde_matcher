# CDE Matcher

A modular, high-performance system for matching variable names to Common Data Elements (CDEs) using exact, fuzzy, and semantic matching algorithms. Features an interactive web interface for manual curation and report generation.

## Overview

The CDE Matcher helps researchers and data scientists map their dataset variable names to standardized Common Data Elements, facilitating data harmonization and interoperability. The system combines automated matching algorithms with manual curation workflows to ensure high-quality mappings.

## Key Features

### Multi-Algorithm Matching
- **Exact Matching**: Case-sensitive/insensitive string matching
- **Fuzzy Matching**: Edit distance with multiple algorithms (rapidfuzz)
- **Semantic Matching**: Domain knowledge-based concept mapping (20+ biomedical concepts)

### Interactive Web Interface
- **Component-based architecture**: Reusable UI components for better maintainability
- **Dataset selector**: Interactive file selection with preview and method configuration
- **Matcher configuration**: Real-time algorithm parameter tuning with examples
- **Results viewer**: Overview dashboard, detailed match views, and analytics
- **Report builder**: Manual curation, conflict resolution, and export functionality
- **Smart caching**: Configuration-based file management with hash naming
- **Flexible data handling**: Support for column headers and data dictionary formats
- **Password protection**: Optional authentication for deployed applications

### Comprehensive Results
- **Advanced analytics**: Confidence distributions and algorithm performance comparisons
- **Interactive selection**: Checkboxes and bulk operations for match curation
- **Conflict resolution**: Automatic detection and resolution of duplicate mappings
- **Session persistence**: Maintains selections across navigation
- **Cached results**: Smart loading from output directory
- **Export options**: Multiple formats including 2-column CSV reports

## Quick Start

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cde_matcher
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Launch the Application

#### Local Development Mode
```bash
# Use local data directories (data/clinical_data, data/cdes, data/output)
python main.py --local
```

#### Cloud Mode (GCS Bucket)
```bash
# Use GCS bucket gs://pathnd_cdes by default
python main.py
```

The application will open in your browser at `http://localhost:8080`

## Usage

### 1. Prepare Your Data

#### Local Mode
Place your clinical data CSV files in the `data/clinical_data/` directory.

#### Cloud Mode
Upload your clinical data CSV files to the GCS bucket at `gs://pathnd_cdes/clinical_data/`.

The system supports multiple formats:
- **Column Headers**: Raw clinical data where variables are column names (e.g., SEA-AD_Cohort_Metadata.csv)
- **Data Dictionaries**: Files with variables in specific columns (e.g., variable_name, Field)

### 2. Select Data Source
- **New Processing**: Select a clinical data file, preview its structure, and choose variable extraction method
- **Cached Results**: Load previously processed results from the output directory (smart caching prevents duplicate processing)
  - Local mode: `data/output/`
  - Cloud mode: `gs://pathnd_cdes/output/`

### 3. Configure Matchers
Adjust algorithm parameters in the sidebar:
- **Exact Matcher**: Case sensitivity options
- **Fuzzy Matcher**: Similarity threshold, algorithm choice, result limits
- **Semantic Matcher**: Exact-only mode, custom concept mappings

### 4. Process and Review
- Click "Start Matching Process" to run all algorithms
- Review results in Overview, Exact, Fuzzy, and Semantic match tabs
- Use interactive tables to explore match details

### 5. Manual Selection
- Use checkboxes to select matches for your final report
- Bulk operations: Select All, Deselect All, High Confidence (>0.8)
- Track selections with real-time count badges

### 6. Generate Report
- Navigate to "Manual Report" to review selections
- Resolve conflicts (same variable mapped to multiple CDEs)
- Download final 2-column CSV report (CDE, Variable)

## Authentication

### Password Protection Setup

The CDE Matcher supports optional password protection for deployed applications.

#### 1. Generate Password Hash
```bash
# Generate hash for your password
python ui/auth.py "your-secret-password"
# Output: Password hash for 'your-secret-password': a1b2c3d4e5f6...
```

#### 2. Set Environment Variable

**Local Development:**
```bash
export CDE_PASSWORD_HASH="a1b2c3d4e5f6..."
python main.py
```

**Cloud Run Deployment:**
```bash
gcloud run deploy cde-matcher \
  --image=your-image \
  --region=europe-west4 \
  --set-env-vars CDE_PASSWORD_HASH="a1b2c3d4e5f6..."
```

**App Engine (app.yaml):**
```yaml
env_variables:
  CDE_LOCAL_MODE: "false"
  CDE_GCS_BUCKET: "pathnd_cdes"
  CDE_PASSWORD_HASH: "a1b2c3d4e5f6..."
```

#### 3. Security Notes
- **Never commit password hashes to version control**
- Use Google Secret Manager for production deployments
- If no password hash is set, authentication is disabled
- Users stay logged in for the session duration

## Cloud Deployment

The CDE Matcher supports both **Docker + Cloud Run** (recommended) and **Google App Engine** deployments.

### Docker + Cloud Run Deployment (Recommended)

#### Quick Deploy
```bash
# Edit PROJECT_ID in deploy.sh, then:
./scripts/deploy.sh
```

#### Manual Deploy Steps
```bash
# 1. Enable APIs and create Artifact Registry repository
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
gcloud artifacts repositories create cde-matcher-repo --repository-format=docker --location=europe-west4
gcloud auth configure-docker europe-west4-docker.pkg.dev

# 2. Build and push image
docker build -t europe-west4-docker.pkg.dev/YOUR_PROJECT_ID/cde-matcher-repo/cde-matcher .
docker push europe-west4-docker.pkg.dev/YOUR_PROJECT_ID/cde-matcher-repo/cde-matcher

# 3. Deploy to Cloud Run
gcloud run deploy cde-matcher \
  --image europe-west4-docker.pkg.dev/YOUR_PROJECT_ID/cde-matcher-repo/cde-matcher \
  --platform managed \
  --region europe-west4 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars CDE_GCS_BUCKET=pathnd_cdes,CDE_LOCAL_MODE=false
```

#### With Password Protection
```bash
# Deploy with authentication
gcloud run deploy cde-matcher \
  --image europe-west4-docker.pkg.dev/YOUR_PROJECT_ID/cde-matcher-repo/cde-matcher \
  --platform managed \
  --region europe-west4 \
  --allow-unauthenticated \
  --set-env-vars CDE_PASSWORD_HASH="your-hash-here"
```

### Local Docker Development

#### Quick Start
```bash
# Local mode (uses data/ directory)
./scripts/local-dev.sh local

# Cloud mode (uses GCS bucket)
./scripts/local-dev.sh cloud
```

#### Manual Docker Commands
```bash
# Build image
docker build -t cde-matcher .

# Run local mode
docker run -p 8080:8080 -e CDE_LOCAL_MODE=true -v $(pwd)/data:/app/data:ro cde-matcher

# Run cloud mode (uses gcloud auth or service account key)
docker run -p 8080:8080 \
  -e CDE_LOCAL_MODE=false \
  -e CDE_GCS_BUCKET=pathnd_cdes \
  -v ~/.config/gcloud:/app/.config/gcloud:ro \
  cde-matcher
```

### Google App Engine Deployment (Alternative)

For environments where App Engine is preferred over Cloud Run:

#### Prerequisites
- Google Cloud Platform account with billing enabled
- GCS bucket `gs://pathnd_cdes` with the following structure:
  ```
  gs://pathnd_cdes/
  ├── clinical_data/     # Your clinical data CSV files
  ├── cdes/             # CDE reference files (e.g., digipath_cdes.csv)
  └── output/           # Results storage (auto-created)
  ```
- `gcloud` CLI installed and configured

#### Setup GCS Bucket
```bash
# Create bucket in Europe for better performance
gsutil mb -l europe-west4 gs://pathnd_cdes

# Upload your data
gsutil cp data/clinical_data/* gs://pathnd_cdes/clinical_data/
gsutil cp data/cdes/* gs://pathnd_cdes/cdes/
```

#### Deploy to App Engine
```bash
# Create App Engine app in europe-west4
gcloud app create --region=europe-west4

# Deploy the application
gcloud app deploy app.yaml

# View the deployed app
gcloud app browse
```

## Deployment Comparison

| Feature | Docker + Cloud Run | App Engine Flexible |
|---------|-------------------|-------------------|
| **Cold Start** | ~10-30 seconds | ~60-90 seconds |
| **Scaling** | 0 to 1000+ instances | Limited scaling |
| **Cost** | Pay per request | Minimum instance cost |
| **Deployment** | `./scripts/deploy.sh` | `gcloud app deploy` |
| **Updates** | Fast rebuilds (~2-3 min) | Slower deployments (~10-15 min) |
| **Registry** | Artifact Registry | Built-in |
| **Flexibility** | Full container control | Platform limitations |

## Production Recommendations

### Recommended: Docker + Cloud Run
- **Faster deployments**: ~2-3 minute builds vs 10-15 minute App Engine
- **Modern registry**: Uses Artifact Registry (GCR is deprecated)
- **Better scaling**: Automatic scaling to zero
- **Cost effective**: Pay only for actual usage
- **Simple workflow**: Direct Docker build/push/deploy
- **No build complexity**: No Cloud Build or docker-compose needed

### Cost Optimization
- **Multi-stage builds**: Smaller production images
- **Automatic scaling**: Scale to zero when not in use
- **Shared result caching**: Reduces processing costs across users
- **Resource limits**: 4GB memory, 2 CPU cores optimized for workload
- **Health checks**: Efficient resource management

### Configuration-Based Result Caching
The system uses intelligent caching based on:
- Dataset name and extraction method
- Matcher configuration (exact, fuzzy, semantic settings)
- MD5 hash of all parameters

This ensures multiple users can share the same GCS bucket safely:
- Identical configurations reuse cached results
- Different configurations generate separate result files
- No file conflicts or data overwrites

### GCS Bucket Structure
Required bucket structure for cloud deployment:
```
gs://pathnd_cdes/
├── clinical_data/     # Your clinical data CSV files
├── cdes/             # CDE reference files (e.g., digipath_cdes.csv)
└── output/           # Results storage (auto-created)
```

### Authentication

#### For Cloud Run/App Engine
- Uses **Application Default Credentials**
- Automatically configured in Google Cloud environments

#### For Local Development
```bash
# Option 1: gcloud auth (recommended)
gcloud auth application-default login
./scripts/local-dev.sh cloud

# Option 2: Service account key (alternative)
# 1. Create service account with Storage Object Admin role
# 2. Download key as service-account-key.json
# 3. Run: ./scripts/local-dev.sh cloud
```

## Architecture

### Modular Architecture

```
cde_matcher/
├── core/                   # Business logic (UI-agnostic)
│   ├── matchers/          # Matching algorithms
│   │   ├── base.py        # Abstract base class and result structures
│   │   ├── exact.py       # Exact string matching
│   │   ├── fuzzy.py       # Fuzzy matching with rapidfuzz
│   │   ├── semantic.py    # Domain knowledge matching
│   │   └── factory.py     # Dynamic matcher creation
│   ├── data_adapter.py    # GCS/local file access abstraction
│   └── pipeline.py        # Main processing pipeline
├── ui/                    # Streamlit interface
│   ├── components/        # Modular UI components
│   │   ├── dataset_selector.py    # File selection and preview
│   │   ├── matcher_config.py      # Algorithm configuration
│   │   ├── results_viewer.py      # Results display and analytics
│   │   └── report_builder.py      # Manual curation and export
│   ├── auth.py           # Authentication system
│   └── browser_app.py     # Main application
├── data/                  # Data storage (local mode)
│   ├── clinical_data/     # Input clinical datasets
│   ├── cdes/             # Target CDE definitions
│   └── output/           # Generated results and reports
└── docs/                 # Comprehensive documentation
```

### Component Architecture

The UI is built using modular components that can be reused and tested independently:

- **DatasetSelector**: Handles file selection, preview, and extraction method configuration
- **MatcherConfig**: Provides interactive algorithm parameter tuning with real-time examples
- **ResultsViewer**: Displays overview dashboard, detailed match views, and advanced analytics
- **ReportBuilder**: Manages manual curation, conflict resolution, and export functionality

### Pipeline Integration

```python
from cde_matcher.core.pipeline import CDEMatcherPipeline

# Initialize pipeline
pipeline = CDEMatcherPipeline()

# Configure matchers
pipeline.configure_matchers(
    exact_config={"case_sensitive": False},
    fuzzy_config={"threshold": 0.7, "algorithm": "token_sort_ratio"},
    semantic_config={"case_sensitive": False, "exact_only": False}
)

# Run matching with flexible variable extraction
results = pipeline.run_pipeline(
    source_path="data/clinical_data/variables.csv",
    target_path="data/cdes/digipath_cdes.csv",
    source_method="columns",  # or "column_values"
    source_column=None        # or specific column name
)
```

## Configuration

### Algorithm Parameters

#### Exact Matcher
- `case_sensitive: bool` - Enable case-sensitive matching (default: False)

#### Fuzzy Matcher
- `threshold: float` - Minimum similarity score (0.0-1.0, default: 0.7)
- `algorithm: str` - Matching algorithm:
  - `ratio`: Basic Levenshtein distance
  - `partial_ratio`: Best partial match
  - `token_sort_ratio`: Order-insensitive word matching
  - `token_set_ratio`: Set operations on words
- `max_results: int` - Maximum matches per field (default: 10)

#### Semantic Matcher
- `exact_only: bool` - Only exact concept matches (default: False)
- `custom_mappings: Dict` - Additional concept mappings

### Built-in Semantic Concepts

The system includes 20+ biomedical concept mappings:
- Patient identifiers: `donor_id`, `participant_id`, `subject_id`
- Demographics: `age_at_death`, `sex`, `race`, `education`
- Clinical measures: `MMSE`, `CASI`, `cognitive_status`
- Pathology scores: `Braak`, `Thal`, `CERAD`
- Genetics: `APOE_genotype`

### Environment Variables

- `CDE_LOCAL_MODE`: Set to "true" for local development (default: "false")
- `CDE_GCS_BUCKET`: GCS bucket name (default: "pathnd_cdes")
- `CDE_GCS_PROJECT`: GCS project ID (optional)
- `CDE_PASSWORD_HASH`: SHA256 hash for authentication (optional)
- `PORT`: Application port (default: 8080)

## Performance

### Benchmarks
Test dataset: SEA-AD Cohort (66 fields) vs DigiPath CDEs (332 items)

| Matcher | Processing Time | Matches Found | Avg Confidence |
|---------|----------------|---------------|----------------|
| Exact | ~0.1s | 1 | 1.000 |
| Fuzzy | ~2-3s | 6 | 0.825 |
| Semantic | ~0.5s | 56 | 0.891 |
| **Total** | **~3-4s** | **63 unique** | **0.847** |

## Development

### Project Structure
See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines and architecture documentation.

### Key Files
- `main.py` - Application entry point with authentication
- `ui/browser_app.py` - Main Streamlit application
- `cde_matcher/core/pipeline.py` - Processing pipeline
- `cde_matcher/core/matchers/` - Matching algorithm implementations
- `cde_matcher/core/data_adapter.py` - GCS/local file abstraction
- `ui/components/` - Modular UI components

### Running Tests
```bash
# Coming soon - test suite in development
pytest tests/
```

## Documentation

- [Architecture Overview](docs/architecture.md) - System design and component relationships
- [Development Guide](DEVELOPMENT.md) - Development workflows and guidelines
- [Matching Algorithms](docs/matching_algorithms.md) - Detailed algorithm specifications
- [Roadmap](docs/ROADMAP.md) - Feature roadmap and milestones
- [Changelog](docs/CHANGELOG.md) - Version history and updates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the interactive interface
- Powered by [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) for high-performance fuzzy matching
- Designed for biomedical research and data harmonization workflows

## Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check the [documentation](docs/) for detailed guides
- Review [DEVELOPMENT.md](DEVELOPMENT.md) for development setup

---

**Ready to harmonize your data?** [Get started](#quick-start) with the CDE Matcher today!