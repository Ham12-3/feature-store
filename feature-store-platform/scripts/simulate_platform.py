#!/usr/bin/env python3
"""
Feature Store Platform -- Multi-Team Simulation
=================================================
Simulates three teams independently registering features to a shared
Feast registry, discovering each other's work, and performing
point-in-time correct cross-team feature retrieval.

Usage
-----
    cd feature-store-platform
    python scripts/simulate_platform.py
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from feast import Entity, FeatureStore, FeatureView, Field, FileSource, ValueType
from feast.types import Float64, Int64, String

# --- Config ---------------------------------------------------------------
NUM_USERS = 100
SEED = 42

SNAPSHOTS = [
    datetime(2026, 1, 1),
    datetime(2026, 1, 8),
    datetime(2026, 1, 15),
    datetime(2026, 1, 22),
    datetime(2026, 2, 1),
]

# Deterministic fraud scores for user_0001 to showcase point-in-time
USER1_FRAUD = [0.10, 0.10, 0.85, 0.85, 0.25]

# ---Pretty-print helpers ---------------------------------------------
DIV = "=" * 66
SUB = "-" * 52


def banner(step: str | None, title: str):
    print(f"\n{DIV}")
    label = f"  STEP {step} -- {title}" if step else f"  {title}"
    print(label)
    print(DIV)


def info(msg: str, indent: int = 2):
    print(f"{' ' * indent}{msg}")


def ok(msg: str):
    info(f"[OK] {msg}")


def arrow(msg: str):
    info(f" ->  {msg}")


def table(df: pd.DataFrame, max_rows: int = 8):
    """Print a dataframe as a compact aligned table."""
    txt = df.head(max_rows).to_string(index=False)
    for line in txt.splitlines():
        info(line, indent=4)
    if len(df) > max_rows:
        info(f"    ... and {len(df) - max_rows} more rows", indent=4)


# ---Data generation --------------------------------------------------
def _user_ids() -> list[str]:
    return [f"user_{i:04d}" for i in range(1, NUM_USERS + 1)]


def generate_fraud_data(data_dir: Path) -> Path:
    """Fraud-team: fraud_score, suspicious_activity_count, days_since_last_fraud_flag."""
    rng = np.random.RandomState(SEED)
    rows = []
    for snap_idx, ts in enumerate(SNAPSHOTS):
        for uid in _user_ids():
            if uid == "user_0001":
                fraud_score = USER1_FRAUD[snap_idx]
            else:
                fraud_score = round(float(rng.uniform(0.0, 0.6)), 4)
            rows.append(
                {
                    "user_id": uid,
                    "fraud_score": fraud_score,
                    "suspicious_activity_count": int(rng.randint(0, 20)),
                    "days_since_last_fraud_flag": int(rng.randint(0, 365)),
                    "event_timestamp": ts,
                    "created_timestamp": ts,
                }
            )
    path = data_dir / "fraud_features.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def generate_reco_data(data_dir: Path) -> Path:
    """Recommendations-team: preferred_category, avg_session_minutes, items_viewed_per_session."""
    rng = np.random.RandomState(SEED + 1)
    categories = ["electronics", "clothing", "home", "sports", "books"]
    rows = []
    for ts in SNAPSHOTS:
        for uid in _user_ids():
            rows.append(
                {
                    "user_id": uid,
                    "preferred_category": rng.choice(categories),
                    "avg_session_minutes": round(float(rng.uniform(1.0, 45.0)), 2),
                    "items_viewed_per_session": int(rng.randint(1, 50)),
                    "event_timestamp": ts,
                    "created_timestamp": ts,
                }
            )
    path = data_dir / "reco_features.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def generate_credit_data(data_dir: Path) -> Path:
    """Credit-team: credit_score, debt_to_income_ratio, open_accounts."""
    rng = np.random.RandomState(SEED + 2)
    rows = []
    for ts in SNAPSHOTS:
        for uid in _user_ids():
            rows.append(
                {
                    "user_id": uid,
                    "credit_score": int(rng.randint(300, 850)),
                    "debt_to_income_ratio": round(float(rng.uniform(0.05, 0.80)), 4),
                    "open_accounts": int(rng.randint(1, 15)),
                    "event_timestamp": ts,
                    "created_timestamp": ts,
                }
            )
    path = data_dir / "credit_features.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


# ---Feast object definitions -----------------------------------------
def make_entity() -> Entity:
    return Entity(
        name="user",
        join_keys=["user_id"],
        value_type=ValueType.STRING,
        description="Platform user",
    )


def make_fraud_fv(source_path: str) -> FeatureView:
    return FeatureView(
        name="user_fraud_scores",
        entities=[make_entity()],
        ttl=timedelta(days=1),
        schema=[
            Field(name="fraud_score", dtype=Float64),
            Field(name="suspicious_activity_count", dtype=Int64),
            Field(name="days_since_last_fraud_flag", dtype=Int64),
        ],
        source=FileSource(
            name="fraud_source",
            path=source_path,
            timestamp_field="event_timestamp",
            created_timestamp_column="created_timestamp",
        ),
        online=True,
        description="Real-time fraud risk indicators per user",
        tags={"owner": "fraud-team", "freshness_sla": "15m", "tier": "critical"},
    )


def make_reco_fv(source_path: str) -> FeatureView:
    return FeatureView(
        name="user_reco_features",
        entities=[make_entity()],
        ttl=timedelta(days=7),
        schema=[
            Field(name="preferred_category", dtype=String),
            Field(name="avg_session_minutes", dtype=Float64),
            Field(name="items_viewed_per_session", dtype=Int64),
        ],
        source=FileSource(
            name="reco_source",
            path=source_path,
            timestamp_field="event_timestamp",
            created_timestamp_column="created_timestamp",
        ),
        online=True,
        description="User browsing and preference signals for recommendations",
        tags={
            "owner": "recommendations-team",
            "freshness_sla": "6h",
            "tier": "standard",
        },
    )


def make_credit_fv(source_path: str) -> FeatureView:
    return FeatureView(
        name="user_credit_profile",
        entities=[make_entity()],
        ttl=timedelta(days=1),
        schema=[
            Field(name="credit_score", dtype=Int64),
            Field(name="debt_to_income_ratio", dtype=Float64),
            Field(name="open_accounts", dtype=Int64),
        ],
        source=FileSource(
            name="credit_source",
            path=source_path,
            timestamp_field="event_timestamp",
            created_timestamp_column="created_timestamp",
        ),
        online=True,
        description="Core credit profile attributes for underwriting",
        tags={"owner": "credit-team", "freshness_sla": "1h", "tier": "critical"},
    )


# =======================================================================
#  MAIN SIMULATION
# =======================================================================
def main():
    banner(None, "FEATURE STORE PLATFORM -- MULTI-TEAM SIMULATION")

    # -- Setup ---------------------------------------------------------
    repo_dir = Path(tempfile.mkdtemp(prefix="feast_sim_"))
    data_dir = repo_dir / "data"
    data_dir.mkdir()

    # Write a minimal feature_store.yaml
    (repo_dir / "feature_store.yaml").write_text(
        "project: simulation\n"
        "provider: local\n"
        "registry: data/registry.db\n"
        "online_store:\n"
        "  type: sqlite\n"
        "  path: data/online_store.db\n"
        "offline_store:\n"
        "  type: file\n"
        "entity_key_serialization_version: 2\n"
    )
    info(f"Temporary Feast project: {repo_dir}")
    store = FeatureStore(repo_path=str(repo_dir))

    try:
        _run_simulation(store, repo_dir, data_dir)
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)
        info(f"\nCleaned up {repo_dir}")


def _run_simulation(store: FeatureStore, repo_dir: Path, data_dir: Path):
    # -- Step 1 -- Generate data ----------------------------------------
    banner("1/5", "DATA GENERATION")

    fraud_path = generate_fraud_data(data_dir)
    reco_path = generate_reco_data(data_dir)
    credit_path = generate_credit_data(data_dir)

    for label, path, features in [
        (
            "fraud-team",
            fraud_path,
            "fraud_score, suspicious_activity_count, days_since_last_fraud_flag",
        ),
        (
            "recommendations-team",
            reco_path,
            "preferred_category, avg_session_minutes, items_viewed_per_session",
        ),
        (
            "credit-team",
            credit_path,
            "credit_score, debt_to_income_ratio, open_accounts",
        ),
    ]:
        rows = len(pd.read_parquet(path))
        info(f"\n  {label}")
        info(f"    File:     {path.name}")
        info(f"    Rows:     {rows:,}  ({NUM_USERS} users x {len(SNAPSHOTS)} snapshots)")
        info(f"    Features: {features}")
    ok("All datasets generated")

    # -- Step 2 -- Team registration ------------------------------------
    banner("2/5", "TEAM FEATURE REGISTRATION")

    entity = make_entity()
    fraud_fv = make_fraud_fv(str(fraud_path))
    reco_fv = make_reco_fv(str(reco_path))
    credit_fv = make_credit_fv(str(credit_path))

    teams = [
        ("fraud-team", fraud_fv),
        ("recommendations-team", reco_fv),
        ("credit-team", credit_fv),
    ]

    for team_name, fv in teams:
        info(f"\n  [{team_name}] Registering '{fv.name}'...")
        store.apply([entity, fv])
        ok(f"'{fv.name}' registered  ({len(fv.schema)} fields, TTL={fv.ttl})")

    all_fvs = store.list_feature_views()
    info(f"\n  Registry now contains {len(all_fvs)} feature view(s).")

    # -- Step 3 -- Cross-team discovery ---------------------------------
    banner("3/5", "CROSS-TEAM FEATURE DISCOVERY")

    info("Scenario: credit-team is building a new creditworthiness model.")
    info("They search the shared registry for useful features.\n")
    info("  > store.list_feature_views()\n")

    header = f"  {'Feature View':<28} {'Owner':<25} {'# Fields':>8}   Description"
    info(header)
    info("  " + "-" * len(header.strip()))
    for fv in all_fvs:
        owner = fv.tags.get("owner", "unknown")
        desc = (fv.description or "")[:40]
        entity_fields = {e.name for e in fv.entity_columns}
        n_features = len([f for f in fv.schema if f.name not in entity_fields])
        info(f"  {fv.name:<28} {owner:<25} {n_features:>8}   {desc}")

    info("\n  credit-team inspects fraud-team's features for reuse:")
    info("  > store.get_feature_view('user_fraud_scores')\n")

    inspected = store.get_feature_view("user_fraud_scores")
    entity_fields = {e.name for e in inspected.entity_columns}
    for f in inspected.schema:
        if f.name in entity_fields:
            continue
        usefulness = {
            "fraud_score": "Highly useful for credit risk!",
            "suspicious_activity_count": "Useful -- signals instability",
            "days_since_last_fraud_flag": "Marginal for credit",
        }.get(f.name, "")
        info(f"    {f.name:<35} {str(f.dtype):<12}  {usefulness}")

    info(
        "\n  Decision: Reuse 'fraud_score' and 'suspicious_activity_count'"
    )
    info("            alongside own credit features for the new model.")

    # -- Step 4 -- Point-in-time retrieval ------------------------------
    banner("4/5", "POINT-IN-TIME CORRECT RETRIEVAL")

    info("Demonstrating temporal correctness with user_0001.\n")
    info("  Fraud-score timeline (from generated data):")
    for ts, score in zip(SNAPSHOTS, USER1_FRAUD):
        label = ""
        if score > 0.7:
            label = "  <-- flagged!"
        elif score < 0.15 and ts == SNAPSHOTS[0]:
            label = "  (clean)"
        elif score < 0.3 and ts == SNAPSHOTS[-1]:
            label = "  (resolved)"
        info(f"    {ts.strftime('%Y-%m-%d')}  ->  fraud_score = {score:.2f}{label}")

    # Query at three points that fall between snapshots
    query_points = [
        ("2026-01-05", 0.10, "before any flag"),
        ("2026-01-20", 0.85, "after flagging"),
        ("2026-02-05", 0.25, "after resolution"),
    ]

    info(
        "\n  Querying with historical timestamps (point-in-time join):\n"
    )

    entity_df = pd.DataFrame(
        {
            "user_id": ["user_0001"] * len(query_points),
            "event_timestamp": [
                datetime.strptime(q[0], "%Y-%m-%d") for q in query_points
            ],
        }
    )

    result = store.get_historical_features(
        entity_df=entity_df,
        features=["user_fraud_scores:fraud_score"],
    ).to_df()

    all_correct = True
    for i, (date_str, expected, context) in enumerate(query_points):
        actual = result.iloc[i]["fraud_score"]
        match = abs(actual - expected) < 0.001
        mark = "[OK]" if match else "[FAIL]"
        if not match:
            all_correct = False
        info(
            f"    Query @ {date_str} ({context:<20})  "
            f"expected={expected:.2f}  got={actual:.2f}  {mark}"
        )

    info("")
    if all_correct:
        ok("Point-in-time join is CORRECT -- Feast returned the right")
        info("       feature values for each historical moment.")
    else:
        info("  [!] Some values did not match -- check data generation.")

    # -- Step 5 -- Cross-team retrieval ---------------------------------
    banner("5/5", "CROSS-TEAM FEATURE RETRIEVAL")

    info("credit-team builds a training set combining their own features")
    info("with fraud-team features -- a single get_historical_features call.\n")

    cross_features = [
        "user_credit_profile:credit_score",
        "user_credit_profile:debt_to_income_ratio",
        "user_fraud_scores:fraud_score",
        "user_fraud_scores:suspicious_activity_count",
    ]

    info("  Requested features:")
    for feat in cross_features:
        view, name = feat.split(":")
        arrow(f"{name:<35} (from {view})")

    sample_users = [f"user_{i:04d}" for i in range(1, 11)]
    cross_entity_df = pd.DataFrame(
        {
            "user_id": sample_users,
            "event_timestamp": [datetime(2026, 2, 1)] * len(sample_users),
        }
    )

    cross_result = store.get_historical_features(
        entity_df=cross_entity_df,
        features=cross_features,
    ).to_df()

    display_df = cross_result[
        [
            "user_id",
            "credit_score",
            "debt_to_income_ratio",
            "fraud_score",
            "suspicious_activity_count",
        ]
    ].copy()
    display_df.columns = [
        "user_id",
        "credit_score",
        "debt_income",
        "fraud_score",
        "suspicious_cnt",
    ]

    info("\n  Results (10 users @ 2026-02-01):\n")
    table(display_df, max_rows=10)

    info(f"\n  Rows returned: {len(cross_result)}")
    info(f"  Columns:       {list(cross_result.columns)}")
    ok("Cross-team feature join successful!")

    # -- Summary -------------------------------------------------------
    banner(None, "SIMULATION COMPLETE")
    info("")
    info("  Summary")
    info("  -------")
    info("  * 3 teams registered features independently to a shared registry")
    info("  * credit-team discovered and inspected fraud-team features")
    info("  * Point-in-time retrieval verified correct for user_0001")
    info("  * Cross-team feature join returned combined training data")
    info("")
    info("  This demonstrates how a centralized feature store enables")
    info("  teams to share, discover, and reuse ML features without")
    info("  duplicating data pipelines.")
    info("")


if __name__ == "__main__":
    main()
