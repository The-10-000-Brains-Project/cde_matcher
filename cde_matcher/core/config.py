"""
Configuration management for CDE Matcher.

Centralizes all environment variable handling and provides type-safe configuration
with sensible defaults for all deployment scenarios.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """
    Application configuration with environment variable defaults.

    All configuration is loaded from environment variables with sensible defaults.
    This provides a single source of truth for all application settings.
    """

    # Server settings
    port: int = int(os.getenv('PORT', '8080'))

    # Data storage configuration
    local_mode: bool = os.getenv('CDE_LOCAL_MODE', 'false').lower() == 'true'
    gcs_bucket: str = os.getenv('CDE_GCS_BUCKET', 'pathnd_cdes')
    gcs_project: Optional[str] = os.getenv('CDE_GCS_PROJECT')

    # Authentication settings
    password_hash: Optional[str] = os.getenv('CDE_PASSWORD_HASH')

    @property
    def data_paths(self) -> dict:
        """
        Get data paths based on local/cloud mode.

        Returns:
            Dictionary with paths for clinical_data, cdes, and output directories.
            Uses local paths when local_mode=True, GCS paths otherwise.
        """
        if self.local_mode:
            return {
                'clinical_data': 'data/clinical_data',
                'cdes': 'data/cdes',
                'output': 'data/output'
            }
        else:
            return {
                'clinical_data': f'gs://{self.gcs_bucket}/clinical_data',
                'cdes': f'gs://{self.gcs_bucket}/cdes',
                'output': f'gs://{self.gcs_bucket}/output'
            }

    @property
    def is_authenticated(self) -> bool:
        """Check if authentication is enabled (password hash is set)."""
        return self.password_hash is not None

    @property
    def is_cloud_mode(self) -> bool:
        """Check if running in cloud mode (opposite of local_mode)."""
        return not self.local_mode

    def __str__(self) -> str:
        """String representation of configuration (safe for logging)."""
        return (
            f"Config("
            f"port={self.port}, "
            f"local_mode={self.local_mode}, "
            f"gcs_bucket='{self.gcs_bucket}', "
            f"gcs_project='{self.gcs_project}', "
            f"auth_enabled={self.is_authenticated}"
            f")"
        )


# Global configuration instance
config = Config()