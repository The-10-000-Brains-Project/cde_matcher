"""
Data adapter for handling both local files and GCS bucket access.

Provides transparent access to data whether stored locally or in GCS buckets.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Optional, List, Union
import tempfile
import glob

from .config import config


class DataAdapter:
    """Adapter for accessing data from local files or GCS buckets."""

    def __init__(self, gcs_project_id: Optional[str] = None):
        """
        Initialize data adapter.

        Args:
            gcs_project_id: GCS project ID for authentication
        """
        self.gcs_project_id = gcs_project_id
        self._gcs_client = None

    def _get_gcs_client(self):
        """Get or create GCS client."""
        if self._gcs_client is None:
            try:
                from google.cloud import storage
                self._gcs_client = storage.Client(project=self.gcs_project_id)
            except ImportError:
                raise ImportError("google-cloud-storage not installed. Run: pip install google-cloud-storage")
        return self._gcs_client

    def _is_gcs_path(self, path: str) -> bool:
        """Check if path is a GCS bucket path."""
        return path.startswith('gs://')

    def _parse_gcs_path(self, gcs_path: str) -> tuple:
        """Parse GCS path into bucket and object names."""
        if not gcs_path.startswith('gs://'):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        path_parts = gcs_path[5:].split('/', 1)  # Remove 'gs://'
        bucket_name = path_parts[0]
        object_name = path_parts[1] if len(path_parts) > 1 else ""

        return bucket_name, object_name

    def read_csv(self, path: str) -> pd.DataFrame:
        """
        Read CSV file from local filesystem or GCS bucket.

        Args:
            path: Local file path or GCS bucket path (gs://bucket/path)

        Returns:
            DataFrame with loaded data
        """
        if self._is_gcs_path(path):
            return self._read_csv_from_gcs(path)
        else:
            return pd.read_csv(path)

    def _read_csv_from_gcs(self, gcs_path: str) -> pd.DataFrame:
        """Read CSV file from GCS bucket."""
        bucket_name, object_name = self._parse_gcs_path(gcs_path)

        client = self._get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        if not blob.exists():
            raise FileNotFoundError(f"GCS object not found: {gcs_path}")

        # Download to temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.csv') as temp_file:
            blob.download_to_filename(temp_file.name)
            df = pd.read_csv(temp_file.name)
            os.unlink(temp_file.name)  # Clean up temp file

        return df

    def list_files(self, path: str, pattern: str = "*.csv") -> List[str]:
        """
        List files in directory or GCS bucket prefix.

        Args:
            path: Local directory path or GCS bucket path
            pattern: File pattern to match (only used for local paths)

        Returns:
            List of file paths/names
        """
        if self._is_gcs_path(path):
            return self._list_gcs_files(path, pattern)
        else:
            return self._list_local_files(path, pattern)

    def _list_local_files(self, directory: str, pattern: str = "*.csv") -> List[str]:
        """List local files matching pattern."""
        if not os.path.exists(directory):
            return []

        full_pattern = os.path.join(directory, pattern)
        files = glob.glob(full_pattern)
        return [os.path.basename(f) for f in files]

    def _list_gcs_files(self, gcs_path: str, pattern: str = "*.csv") -> List[str]:
        """List files in GCS bucket with prefix."""
        bucket_name, prefix = self._parse_gcs_path(gcs_path)

        client = self._get_gcs_client()
        bucket = client.bucket(bucket_name)

        # Ensure prefix ends with / if it should be a directory
        if prefix and not prefix.endswith('/'):
            prefix += '/'

        # List blobs with prefix
        blobs = bucket.list_blobs(prefix=prefix)

        files = []
        for blob in blobs:
            # Only include files (not directories) that match pattern
            if not blob.name.endswith('/'):
                filename = os.path.basename(blob.name)
                if pattern == "*.csv" and filename.endswith('.csv'):
                    files.append(filename)
                elif pattern == "*" or filename.endswith(pattern.replace('*', '')):
                    files.append(filename)

        return files

    def file_exists(self, path: str) -> bool:
        """Check if file exists locally or in GCS."""
        if self._is_gcs_path(path):
            return self._gcs_file_exists(path)
        else:
            return os.path.exists(path)

    def _gcs_file_exists(self, gcs_path: str) -> bool:
        """Check if file exists in GCS bucket."""
        try:
            bucket_name, object_name = self._parse_gcs_path(gcs_path)
            client = self._get_gcs_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            return blob.exists()
        except Exception:
            return False

    def get_full_path(self, base_path: str, filename: str) -> str:
        """Get full path for a file given base path and filename."""
        if self._is_gcs_path(base_path):
            # Ensure proper GCS path format
            if base_path.endswith('/'):
                return f"{base_path}{filename}"
            else:
                return f"{base_path}/{filename}"
        else:
            return os.path.join(base_path, filename)

    def write_json(self, path: str, data: dict) -> None:
        """Write JSON data to local file or GCS bucket."""
        if self._is_gcs_path(path):
            self._write_json_to_gcs(path, data)
        else:
            import json
            # Ensure local directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def _write_json_to_gcs(self, gcs_path: str, data: dict) -> None:
        """Write JSON data to GCS bucket."""
        import json
        bucket_name, object_name = self._parse_gcs_path(gcs_path)

        client = self._get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        # Convert to JSON string and upload
        json_string = json.dumps(data, indent=2)
        blob.upload_from_string(json_string, content_type='application/json')

    def read_json(self, path: str) -> dict:
        """Read JSON data from local file or GCS bucket."""
        if self._is_gcs_path(path):
            return self._read_json_from_gcs(path)
        else:
            import json
            with open(path, 'r') as f:
                return json.load(f)

    def _read_json_from_gcs(self, gcs_path: str) -> dict:
        """Read JSON data from GCS bucket."""
        import json
        bucket_name, object_name = self._parse_gcs_path(gcs_path)

        client = self._get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        if not blob.exists():
            raise FileNotFoundError(f"GCS object not found: {gcs_path}")

        # Download and parse JSON
        json_string = blob.download_as_text()
        return json.loads(json_string)


def get_data_paths():
    """Get configured data paths from centralized configuration."""
    return config.data_paths


# Global data adapter instance
_data_adapter = None

def get_data_adapter():
    """Get global data adapter instance."""
    global _data_adapter
    if _data_adapter is None:
        _data_adapter = DataAdapter(config.gcs_project)
    return _data_adapter