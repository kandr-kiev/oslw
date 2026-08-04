"""Domain exceptions for OSLW."""


class OslwError(Exception):
    """Base exception for all OSLW errors."""


class WikiError(OslwError):
    """Wiki-related errors."""


class PageNotFoundError(WikiError):
    """Wiki page not found."""

    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Wiki page not found: {slug}")


class PageValidationError(WikiError):
    """Wiki page validation error."""

    def __init__(self, slug: str, errors: list[str]):
        self.slug = slug
        self.errors = errors
        super().__init__(f"Page '{slug}' has {len(errors)} validation errors")


class SourceError(OslwError):
    """Source monitoring errors."""


class SourceFetchError(SourceError):
    """Failed to fetch from source."""

    def __init__(self, source: str, url: str, reason: str):
        self.source = source
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {source} ({url}): {reason}")


class GraphError(OslwError):
    """Graph-related errors."""


class GraphGenerationError(GraphError):
    """Failed to generate graph."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Graph generation failed: {reason}")


class DoctorError(OslwError):
    """WikiDoctor errors."""


class DoctorCureError(DoctorError):
    """Error during wiki cure operation."""

    def __init__(self, step: str, reason: str):
        self.step = step
        self.reason = reason
        super().__init__(f"Doctor cure step '{step}' failed: {reason}")


class DigestError(OslwError):
    """Digest generation errors."""


class IngestError(OslwError):
    """Content ingestion errors."""
