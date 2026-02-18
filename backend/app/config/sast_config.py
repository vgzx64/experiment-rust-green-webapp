"""Configuration for SAST tools integration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class SastConfig(BaseSettings):
    """Configuration for SAST scanning tools."""
    
    model_config = SettingsConfigDict(
        env_prefix="SAST_",
        env_file=".env",
        extra="ignore"
    )
    
    # Enable/disable SAST
    enabled: bool = True
    
    # Clippy configuration
    clippy_enabled: bool = True
    clippy_auto_fix: bool = True
    clippy_timeout: int = 120  # seconds
    clippy_warn_lints: list[str] = [
        "clippy::suspicious",
        "clippy::correctness",
        "clippy::style",
        "clippy::complexity",
        "clippy::perf"
    ]
    
    # Semgrep configuration
    semgrep_enabled: bool = True
    semgrep_auto_fix: bool = True
    semgrep_timeout: int = 300  # seconds
    semgrep_config: str = "auto"  # auto, p/security-audit, p/rust, etc.
    semgrep_container_image: Optional[str] = "semgrep/semgrep:latest"
    semgrep_use_container: bool = False  # Use Podman/Docker
    
    # Cargo-audit configuration
    cargo_audit_enabled: bool = True
    cargo_audit_timeout: int = 60  # seconds
    
    # Podman configuration (for containerized tools)
    podman_path: str = "podman"
    
    # General settings
    max_issues_per_scan: int = 1000
    fail_on_timeout: bool = False  # Continue pipeline if SAST times out


# Global SAST config instance
sast_config = SastConfig()
