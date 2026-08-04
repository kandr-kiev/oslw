"""Core package - domain primitives and exceptions."""

from oslw.core.exceptions import (
    DoctorCureError,
    DoctorError,
    DigestError,
    GraphError,
    GraphGenerationError,
    IngestError,
    OslwError,
    PageNotFoundError,
    PageValidationError,
    SourceError,
    SourceFetchError,
    WikiError,
)

__all__ = [
    "OslwError",
    "WikiError",
    "PageNotFoundError",
    "PageValidationError",
    "SourceError",
    "SourceFetchError",
    "GraphError",
    "GraphGenerationError",
    "DoctorError",
    "DoctorCureError",
    "DigestError",
    "IngestError",
]
