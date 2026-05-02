"""Custom exceptions exposed by the public API."""

from __future__ import annotations


class TurbaError(Exception):
    """Base exception for all package-specific errors."""


class ValidationError(TurbaError):
    """Raised when user input fails validation."""


class SiteDataNotFoundError(TurbaError):
    """Raised when the requested website returns no usable site information."""


class CropNotFoundError(TurbaError):
    """Raised when a requested crop is not available at a site."""


class UpstreamResponseError(TurbaError):
    """Raised when upstream HTML cannot be parsed as expected."""
