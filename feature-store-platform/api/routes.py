"""API route handlers for feature views, teams, and feature retrieval.

All routes are mounted on a single APIRouter and included in the main
app.  The Feast registry is the sole source of truth -- there is no
separate database for feature metadata.
"""

from collections import defaultdict
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.feast_client import (
    extract_detail,
    extract_summary,
    get_feature_view,
    get_store,
    list_feature_views,
)
from api.models import (
    FeatureViewDetail,
    FeatureViewSummary,
    RetrieveRequest,
    RetrieveResponse,
    TeamSummary,
)

router = APIRouter()


# ---- Feature view endpoints ------------------------------------------------


@router.get("/features", response_model=list[FeatureViewSummary])
def list_features():
    """List all feature views with summary metadata."""
    fvs = list_feature_views()
    return [extract_summary(fv) for fv in fvs]


@router.get("/features/search", response_model=list[FeatureViewSummary])
def search_features(q: str = Query(..., min_length=1)):
    """Search feature views by name, description, or tag values.

    Performs a case-insensitive substring match across the feature view
    name, description, all tag values, and individual feature names.
    """
    query = q.lower()
    fvs = list_feature_views()
    results = []
    for fv in fvs:
        # Build a single searchable string from all relevant fields.
        searchable = " ".join(
            [
                fv.name,
                fv.description or "",
                *fv.tags.values(),
                *[f.name for f in fv.schema],
            ]
        ).lower()
        if query in searchable:
            results.append(extract_summary(fv))
    return results


@router.get("/features/{name}", response_model=FeatureViewDetail)
def get_feature_detail(name: str):
    """Get full details of a specific feature view."""
    try:
        fv = get_feature_view(name)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Feature view '{name}' not found")
    return extract_detail(fv)


# ---- Team endpoints ---------------------------------------------------------


@router.get("/teams", response_model=list[TeamSummary])
def list_teams():
    """List all teams and their owned feature views.

    Teams are derived dynamically from the "owner" tag on each feature
    view.  No separate team registry is needed -- adding a new owner
    tag value automatically creates a new team in this listing.
    """
    fvs = list_feature_views()
    teams: dict[str, list[str]] = defaultdict(list)
    for fv in fvs:
        owner = fv.tags.get("owner", "unassigned")
        teams[owner].append(fv.name)
    return [
        TeamSummary(
            name=team,
            feature_view_count=len(views),
            feature_views=sorted(views),
        )
        for team, views in sorted(teams.items())
    ]


# ---- Feature retrieval ------------------------------------------------------


@router.post("/features/retrieve", response_model=RetrieveResponse)
def retrieve_features(request: RetrieveRequest):
    """Retrieve historical feature values for given entities.

    Builds an entity DataFrame from the request, injects the current
    timestamp, and delegates to Feast's get_historical_features() for
    a point-in-time correct join.

    Example body::

        {
          "features": [
            "user_transaction_features:avg_transaction_amount",
            "user_risk_features:chargeback_count"
          ],
          "entities": {
            "user_id": ["user_0001", "user_0002"]
          }
        }
    """
    store = get_store()
    try:
        entity_df = pd.DataFrame(request.entities)
        # Feast requires an event_timestamp column for the point-in-time
        # join.  Default to "now" so callers get the latest values.
        entity_df["event_timestamp"] = datetime.now()
        result = store.get_historical_features(
            entity_df=entity_df,
            features=request.features,
        ).to_df()
        # Convert timestamps to strings for JSON serialisation -- pandas
        # datetime64 types are not natively JSON-serialisable.
        for col in result.select_dtypes(include=["datetime64[ns]", "datetimetz"]):
            result[col] = result[col].astype(str)
        return RetrieveResponse(results=result.to_dict(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
