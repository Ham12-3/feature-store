"""Feature view definitions for the feature store.

Each FeatureView maps a group of related features to a data source
and an entity.  Feature views are the unit of sharing -- teams
register views and other teams discover and reuse them.

Tags convention (used by the API and UI for metadata):
  - owner:          Team name responsible for data quality.
  - freshness_sla:  Maximum acceptable staleness (e.g. "1h", "15m").
  - tier:           "critical" (real-time SLA) or "standard" (best-effort).
"""

from datetime import timedelta

from feast import FeatureView, Field
from feast.types import Float64, Int64, UnixTimestamp

from entities import user
from data_sources import user_transactions_source

# ---------------------------------------------------------------------------
# Payments team -- transaction aggregates
# ---------------------------------------------------------------------------
user_transaction_features = FeatureView(
    name="user_transaction_features",
    entities=[user],
    # TTL = 1 day: features older than this are considered stale and
    # will not be returned by online serving.
    ttl=timedelta(days=1),
    schema=[
        Field(name="avg_transaction_amount", dtype=Float64),
        Field(name="total_transaction_count", dtype=Int64),
        # UnixTimestamp is stored as an int64 epoch but Feast handles
        # serialization automatically.
        Field(name="last_transaction_date", dtype=UnixTimestamp),
    ],
    source=user_transactions_source,
    online=True,
    description="Aggregated transaction features per user",
    tags={
        "owner": "payments-team",
        "freshness_sla": "1h",
        "tier": "critical",
    },
)

# ---------------------------------------------------------------------------
# Identity team -- profile & engagement signals
# ---------------------------------------------------------------------------
user_profile_features = FeatureView(
    name="user_profile_features",
    entities=[user],
    # Longer TTL (7 days) because profile data changes slowly.
    ttl=timedelta(days=7),
    schema=[
        Field(name="account_age_days", dtype=Int64),
        Field(name="login_frequency", dtype=Float64),
    ],
    source=user_transactions_source,
    online=True,
    description="User profile and engagement features",
    tags={
        "owner": "identity-team",
        "freshness_sla": "24h",
        "tier": "standard",
    },
)

# ---------------------------------------------------------------------------
# Fraud team -- risk indicators
# ---------------------------------------------------------------------------
user_risk_features = FeatureView(
    name="user_risk_features",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="failed_transaction_ratio", dtype=Float64),
        Field(name="chargeback_count", dtype=Int64),
    ],
    source=user_transactions_source,
    online=True,
    description="User risk scoring features",
    tags={
        "owner": "fraud-team",
        # Tightest SLA -- fraud models need near-real-time data.
        "freshness_sla": "15m",
        "tier": "critical",
    },
)
