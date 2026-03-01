"""Feast SDK wrapper for the registry API.

This module owns the connection to the Feast feature store and provides
helper functions that translate Feast objects into plain dicts suitable
for Pydantic serialization.

The FeatureStore instance is created lazily and cached at module level
so every request re-uses the same connection.
"""

import os
from pathlib import Path

from feast import FeatureStore
from feast.feature_view import FeatureView

# FEAST_REPO_PATH can be overridden via environment variable in Docker /
# Kubernetes.  Defaults to the sibling feast_repo/ directory.
REPO_PATH = os.getenv(
    "FEAST_REPO_PATH",
    str(Path(__file__).resolve().parent.parent / "feast_repo"),
)

# Module-level singleton -- avoids re-reading the registry on every request.
_store: FeatureStore | None = None


def get_store() -> FeatureStore:
    """Return a cached FeatureStore instance."""
    global _store
    if _store is None:
        _store = FeatureStore(repo_path=REPO_PATH)
    return _store


def list_feature_views() -> list[FeatureView]:
    store = get_store()
    return store.list_feature_views()


def get_feature_view(name: str) -> FeatureView:
    store = get_store()
    return store.get_feature_view(name)


def extract_summary(fv: FeatureView) -> dict:
    """Extract a lightweight summary dict from a FeatureView.

    Used by the /features list endpoint.  Omits individual feature
    details to keep the payload small for catalog browsing.
    """
    return {
        "name": fv.name,
        "description": fv.description or "",
        # Ownership is derived from the Feast "owner" tag -- no
        # separate metadata DB needed.
        "owner_team": fv.tags.get("owner", "unassigned"),
        "entities": [e.name for e in fv.entity_columns],
        # Subtract entity columns from schema length to get the
        # actual feature count.
        "feature_count": len(fv.schema) - len(fv.entity_columns),
        "created_date": fv.created_timestamp,
        "freshness_sla": fv.tags.get("freshness_sla", "n/a"),
        "tier": fv.tags.get("tier", "standard"),
        "online": fv.online,
    }


def extract_detail(fv: FeatureView) -> dict:
    """Extract full detail dict including individual features and source.

    Used by the /features/{name} detail endpoint.
    """
    # Entity columns appear in schema but aren't "features" -- filter
    # them out so the API only returns actual feature fields.
    entity_names = {e.name for e in fv.entity_columns}
    features = [
        {"name": f.name, "dtype": str(f.dtype)}
        for f in fv.schema
        if f.name not in entity_names
    ]
    return {
        "name": fv.name,
        "description": fv.description or "",
        "owner_team": fv.tags.get("owner", "unassigned"),
        "entities": [e.name for e in fv.entity_columns],
        "features": features,
        "source_name": fv.batch_source.name if fv.batch_source else "unknown",
        "ttl_seconds": int(fv.ttl.total_seconds()) if fv.ttl else 0,
        "created_date": fv.created_timestamp,
        "freshness_sla": fv.tags.get("freshness_sla", "n/a"),
        "tier": fv.tags.get("tier", "standard"),
        "online": fv.online,
        "tags": dict(fv.tags) if fv.tags else {},
    }
