"""Feature Store Platform -- FastAPI application.

This is the entrypoint for the registry API.  It wires together:
  - CORS middleware (allows the Next.js frontend to call the API)
  - Feature / team routes (see routes.py)
  - A /health endpoint that also verifies Feast connectivity

Run with:
    uvicorn api.main:app --reload
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import HealthResponse
from api.routes import router

app = FastAPI(
    title="Feature Store Platform API",
    description="API for browsing, searching, and retrieving ML features from Feast",
    version="0.1.0",
)

# CORS: allow all origins for development.  In production, restrict
# allow_origins to the actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all feature and team routes at the root path.
app.include_router(router)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check -- also verifies Feast registry connectivity.

    Returns "healthy" if the Feast registry is reachable, "degraded"
    otherwise.  Kubernetes readiness probes should target this endpoint.
    """
    feast_ok = False
    try:
        from api.feast_client import list_feature_views

        list_feature_views()
        feast_ok = True
    except Exception:
        pass
    return HealthResponse(
        status="healthy" if feast_ok else "degraded",
        feast_connected=feast_ok,
        timestamp=datetime.now(timezone.utc),
    )
