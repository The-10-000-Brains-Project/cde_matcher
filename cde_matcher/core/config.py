"""
Configuration management for CDE Matcher with GCS-first architecture.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import pandas as pd

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


@dataclass
class StorageConfig:
    """Configuration for data storage - defaults to GCS with local fallback."""

    # Storage type: "gcs" (default) or "local"
    storage_type: str = "gcs"

    # GCS configuration (defaults for pathnd_cdes bucket)
    gcs_bucket_name: str = "pathnd_cdes"
    gcs_project_id: Optional[str] = None

    # GCS paths within bucket (matching your structure)
    gcs_clinical_data_prefix: str = "clinical_data"
    gcs_cdes_prefix: str = "cdes"
    gcs_output_prefix: str = "output"

    # Local paths (fallback when --local is used)
    local_clinical_data_dir: str = "data/clinical_data"
    local_cdes_dir: str = "data/cdes"
    local_output_dir: str = "data/output"

    @classmethod
    def create(cls, use_local: bool = False) -> "StorageConfig":
        """Create configuration with GCS as default, local as fallback."""
        if use_local or not GCS_AVAILABLE:
            return cls(storage_type="local")

        # Check for custom bucket name or project
        bucket_name = os.getenv("GCS_BUCKET_NAME", "pathnd_cdes")
        project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")

        return cls(
            storage_type="gcs",
            gcs_bucket_name=bucket_name,
            gcs_project_id=project_id
        )

    @staticmethod
    def check_local_flag() -> bool:
        """Check if --local flag is present in command line arguments."""
        return "--local" in sys.argv


class DataManager:
    """Unified data manager with GCS-first architecture."""

    def __init__(self, config: Optional[StorageConfig] = None):
        # Auto-detect local flag if no config provided
        if config is None:
            use_local = StorageConfig.check_local_flag()
            config = StorageConfig.create(use_local=use_local)

        self.config = config
        self._gcs_client = None
        self._bucket = None
        self._temp_dir = None

        if self.config.storage_type == "gcs":
            self._initialize_gcs()

        print(f"🗄️  Storage: {self.get_display_location()}")

    def _initialize_gcs(self):
        """Initialize GCS client and bucket."""
        if not GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is required for GCS support.\n"
                "Install with: pip install google-cloud-storage\n"
                "Or use --local flag for local development"
            )

        try:
            self._gcs_client = storage.Client(project=self.config.gcs_project_id)
            self._bucket = self._gcs_client.bucket(self.config.gcs_bucket_name)

            # Verify bucket access
            if not self._bucket.exists():
                raise ValueError(f"GCS bucket '{self.config.gcs_bucket_name}' does not exist or is not accessible")

            # Create temp directory for GCS file caching
            self._temp_dir = tempfile.mkdtemp(prefix="cde_matcher_gcs_")
            print(f"✅ Connected to GCS bucket: {self.config.gcs_bucket_name}")

        except Exception as e:
            print(f"❌ Failed to connect to GCS: {e}")
            print("💡 Use --local flag for local development")
            raise

    def list_clinical_data_files(self) -> List[str]:
        """List available clinical data files."""
        if self.config.storage_type == "gcs":
            return self._list_gcs_files(self.config.gcs_clinical_data_prefix, ".csv")
        else:
            return self._list_local_files(self.config.local_clinical_data_dir, ".csv")

    def load_clinical_data_file(self, filename: str) -> pd.DataFrame:
        """Load a clinical data file."""
        if self.config.storage_type == "gcs":
            blob_path = f"{self.config.gcs_clinical_data_prefix}/{filename}"
            return self._load_gcs_csv(blob_path)
        else:
            file_path = os.path.join(self.config.local_clinical_data_dir, filename)
            return pd.read_csv(file_path)

    def load_cdes_file(self, filename: str = "digipath_cdes.csv") -> pd.DataFrame:
        """Load the CDEs file."""
        if self.config.storage_type == "gcs":
            blob_path = f"{self.config.gcs_cdes_prefix}/{filename}"
            return self._load_gcs_csv(blob_path)
        else:
            file_path = os.path.join(self.config.local_cdes_dir, filename)
            return pd.read_csv(file_path)

    def save_results(self, results: dict, filename: str) -> str:
        """Save results to storage and return the path/location."""
        if self.config.storage_type == "gcs":
            blob_path = f"{self.config.gcs_output_prefix}/{filename}"
            return self._save_gcs_json(results, blob_path)
        else:
            # Ensure output directory exists
            os.makedirs(self.config.local_output_dir, exist_ok=True)
            file_path = os.path.join(self.config.local_output_dir, filename)
            import json
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            return file_path

    def list_output_files(self) -> List[str]:
        """List available output files."""
        if self.config.storage_type == "gcs":
            return self._list_gcs_files(self.config.gcs_output_prefix, ".json")
        else:
            if not os.path.exists(self.config.local_output_dir):
                return []
            import glob
            json_files = glob.glob(os.path.join(self.config.local_output_dir, "*.json"))
            return [os.path.basename(f) for f in json_files]

    def load_output_file(self, filename: str) -> dict:
        """Load an output file."""
        if self.config.storage_type == "gcs":
            blob_path = f"{self.config.gcs_output_prefix}/{filename}"
            return self._load_gcs_json(blob_path)
        else:
            file_path = os.path.join(self.config.local_output_dir, filename)
            import json
            with open(file_path, 'r') as f:
                return json.load(f)

    def output_file_exists(self, filename: str) -> bool:
        """Check if an output file exists."""
        if self.config.storage_type == "gcs":
            blob_path = f"{self.config.gcs_output_prefix}/{filename}"
            blob = self._bucket.blob(blob_path)
            return blob.exists()
        else:
            file_path = os.path.join(self.config.local_output_dir, filename)
            return os.path.exists(file_path)

    def get_display_location(self) -> str:
        """Get human-readable storage location for display."""
        if self.config.storage_type == "gcs":
            return f"GCS Bucket: gs://{self.config.gcs_bucket_name}/"
        else:
            return f"Local Directory: {os.path.abspath('data')}/"

    def get_storage_info(self) -> dict:
        """Get storage configuration info for display."""
        if self.config.storage_type == "gcs":
            return {
                "type": "Google Cloud Storage",
                "bucket": self.config.gcs_bucket_name,
                "clinical_data": f"gs://{self.config.gcs_bucket_name}/{self.config.gcs_clinical_data_prefix}/",
                "cdes": f"gs://{self.config.gcs_bucket_name}/{self.config.gcs_cdes_prefix}/",
                "output": f"gs://{self.config.gcs_bucket_name}/{self.config.gcs_output_prefix}/"
            }
        else:
            return {
                "type": "Local Storage",
                "clinical_data": os.path.abspath(self.config.local_clinical_data_dir),
                "cdes": os.path.abspath(self.config.local_cdes_dir),
                "output": os.path.abspath(self.config.local_output_dir)
            }

    # Private methods for GCS operations
    def _list_gcs_files(self, prefix: str, extension: str) -> List[str]:
        """List files in GCS with given prefix and extension."""
        try:
            blobs = self._bucket.list_blobs(prefix=prefix)
            files = []
            for blob in blobs:
                if blob.name.endswith(extension) and not blob.name.endswith('/'):
                    # Get just the filename, not the full path
                    filename = blob.name.split('/')[-1]
                    if filename:  # Skip empty filenames
                        files.append(filename)
            return sorted(files)
        except Exception as e:
            print(f"⚠️  Warning: Could not list files from {prefix}: {e}")
            return []

    def _load_gcs_csv(self, blob_path: str) -> pd.DataFrame:
        """Load CSV file from GCS."""
        blob = self._bucket.blob(blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: gs://{self.config.gcs_bucket_name}/{blob_path}")

        # Download to temporary file
        temp_filename = blob_path.replace('/', '_').replace(' ', '_')
        temp_path = os.path.join(self._temp_dir, temp_filename)

        print(f"📥 Downloading: gs://{self.config.gcs_bucket_name}/{blob_path}")
        blob.download_to_filename(temp_path)

        # Load with pandas
        df = pd.read_csv(temp_path)

        # Clean up temp file
        os.unlink(temp_path)

        return df

    def _load_gcs_json(self, blob_path: str) -> dict:
        """Load JSON file from GCS."""
        blob = self._bucket.blob(blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: gs://{self.config.gcs_bucket_name}/{blob_path}")

        print(f"📥 Loading: gs://{self.config.gcs_bucket_name}/{blob_path}")
        content = blob.download_as_text()
        import json
        return json.loads(content)

    def _save_gcs_json(self, data: dict, blob_path: str) -> str:
        """Save JSON data to GCS."""
        import json
        content = json.dumps(data, indent=2, default=str)

        blob = self._bucket.blob(blob_path)
        print(f"📤 Uploading: gs://{self.config.gcs_bucket_name}/{blob_path}")
        blob.upload_from_string(content, content_type='application/json')

        return f"gs://{self.config.gcs_bucket_name}/{blob_path}"

    def _list_local_files(self, directory: str, extension: str) -> List[str]:
        """List local files with given extension."""
        if not os.path.exists(directory):
            return []
        import glob
        files = glob.glob(os.path.join(directory, f"*{extension}"))
        return [os.path.basename(f) for f in files]

    def __del__(self):
        """Clean up temporary directory."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)


# Global data manager instance
_data_manager = None

def get_data_manager() -> DataManager:
    """Get global data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

def reset_data_manager():
    """Reset the global data manager (useful for testing)."""
    global _data_manager
    _data_manager = None