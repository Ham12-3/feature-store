"""Pydantic models for API request and response schemas.

These models serve double duty:
  1. FastAPI uses them for automatic request validation.
  2. They appear in the auto-generated OpenAPI / Swagger docs.
"""

from datetime import datetime

from pydantic import BaseModel


class FeatureField(BaseModel):
    """A single feature within a feature view."""
    name: str
    dtype: str  # Feast type name, e.g. "Float64", "Int64"


class FeatureViewSummary(BaseModel):
    """Lightweight view returned by the /features list endpoint."""
    name: str
    description: str
    owner_team: str
    entities: list[str]
    feature_count: int
    created_date: datetime | None
    freshness_sla: str
    tier: str            # "critical" | "standard"
    online: bool


class FeatureViewDetail(BaseModel):
    """Full view returned by /features/{name}, including individual features."""
    name: str
    description: str
    owner_team: str
    entities: list[str]
    features: list[FeatureField]
    source_name: str
    ttl_seconds: int
    created_date: datetime | None
    freshness_sla: str
    tier: str
    online: bool
    tags: dict[str, str]  # All Feast tags, raw


class TeamSummary(BaseModel):
    """Team grouping returned by /teams."""
    name: str
    feature_view_count: int
    feature_views: list[str]


class RetrieveRequest(BaseModel):
    """POST body for /features/retrieve.

    features:  List of "view_name:feature_name" references.
    entities:  Dict mapping entity key names to lists of entity IDs.
    """
    features: list[str]
    entities: dict[str, list[str]]


class RetrieveResponse(BaseModel):
    """Wrapper around the point-in-time join results."""
    results: list[dict]


class HealthResponse(BaseModel):
    """Returned by /health."""
    status: str            # "healthy" | "degraded"
    feast_connected: bool
    timestamp: datetime
