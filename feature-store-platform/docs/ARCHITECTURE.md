# Architecture & Design Decisions

## Overview

The Feature Store Platform is a three-tier system designed for
organizations where multiple ML teams need to share features without
duplicating data pipelines.

```
 +-----------+    +-----------+    +------------+
 | Team A    |    | Team B    |    | Team C     |
 | (fraud)   |    | (reco)    |    | (credit)   |
 +-----+-----+    +-----+-----+    +------+-----+
       |                |                  |
       v                v                  v
  +--------------------------------------------+
  |        Shared Feast Registry               |   Single source of truth
  |     (PostgreSQL in prod, SQLite local)     |   for all feature metadata
  +----+------------------+--------------------+
       |                  |
  +----v------+    +------v-------+
  | Online    |    | Offline      |                 Dual-store architecture
  | Store     |    | Store        |
  | (Redis)   |    | (Parquet)    |
  +-----------+    +--------------+
```

## Component Design

### Feast Feature Repository (`feast_repo/`)

The repository is the canonical definition of all features. Each file
has a single responsibility:

- **entities.py** -- Defines the `user` entity with `user_id` as the
  join key. All feature views reference this entity, ensuring
  consistent entity resolution across teams.

- **data_sources.py** -- Declares the `FileSource` pointing at the
  parquet file. In production this would be swapped for a BigQuery,
  Redshift, or Snowflake source via the Feast config.

- **feature_views.py** -- The core feature definitions. Each view
  uses `tags` for organizational metadata:
  - `owner`: The team responsible for the feature view.
  - `freshness_sla`: How stale the data can be before alerting.
  - `tier`: "critical" or "standard" -- drives monitoring priority.

  This tag-based ownership model was chosen over a separate metadata
  database because it keeps ownership co-located with the feature
  definition, making it harder for metadata to drift.

- **feature_store.yaml** -- Registry and store configuration. Local
  development uses SQLite; the k8s ConfigMap overrides this with
  PostgreSQL (registry) and Redis (online store).

### FastAPI Registry API (`api/`)

The API is a thin read layer over the Feast registry. Design choices:

- **Singleton FeatureStore** (`feast_client.py`) -- The Feast SDK
  is initialized once and cached in a module-level variable. This
  avoids re-reading the registry on every request.

- **Summary vs Detail separation** -- `extract_summary()` returns
  lightweight metadata for list views. `extract_detail()` adds
  individual features, source info, and full tags. This prevents
  over-fetching on the catalog homepage.

- **Search across multiple fields** -- The `/features/search` endpoint
  concatenates name, description, tags, and feature names into a
  single searchable string. Simple but effective for a catalog of
  tens to hundreds of feature views.

- **Team derivation from tags** -- The `/teams` endpoint dynamically
  groups feature views by their `owner` tag rather than maintaining
  a separate team registry. Adding a new team is as simple as
  creating a feature view with a new owner tag.

- **Historical retrieval via POST** -- `/features/retrieve` accepts
  entity keys and feature references, builds an entity DataFrame,
  and delegates to Feast's `get_historical_features()`. This
  provides point-in-time correct joins out of the box.

### Next.js Catalog UI (`catalog_ui/`)

The frontend is a read-only catalog for feature discovery:

- **App Router** -- Uses Next.js 14 App Router with client components
  for interactive search and URL-driven team filtering.

- **Mock data** -- Ships with `lib/mock-data.ts` so the UI is
  fully functional without a running backend. In production, this
  would be replaced with `fetch()` calls to the API.

- **URL-based team filter** -- Clicking a team in the sidebar sets
  `?team=fraud-team` in the URL. This makes filtered views
  shareable and bookmarkable.

- **Tailwind CSS** -- Utility-first CSS with a consistent design
  system: dark sidebar (`slate-900`), light content area (`gray-50`),
  color-coded team badges, tier indicators, and data-type pills.

### Storage Layer

**Why Redis for online store?**
Redis provides sub-millisecond reads for real-time serving. Feast
materializes features from the offline store into Redis, so ML models
can fetch the latest feature values at prediction time.

**Why PostgreSQL for registry?**
The registry holds metadata (feature view definitions, entities,
data sources). PostgreSQL gives us:
- Concurrent access from multiple API replicas
- Durability guarantees for metadata
- SQL querying for advanced registry operations

SQLite is used in local development for zero-setup convenience.

**Why Parquet for offline store?**
Parquet files provide columnar storage that's efficient for the
analytical queries used in training data generation. In production,
this would typically be a data warehouse (BigQuery, Redshift).

## Kubernetes Deployment

```
 Namespace: feature-store
 +----------------------------------------------+
 |                                              |
 |  +----------+  +----------+  +----------+   |
 |  | feast x2 |  | api x2   |  | ui x2    |   |   Application pods
 |  +----+-----+  +----+-----+  +----+-----+   |
 |       |             |             |          |
 |  +----v-----+  +----v-----+  +---v------+   |
 |  | feast-svc|  | api-svc  |  | ui-svc   |   |   ClusterIP services
 |  +----------+  +----------+  +----------+   |
 |       |             |             |          |
 |  +----v-------------v-------------v------+   |
 |  |            Ingress (nginx)            |   |   External routing
 |  |  /feast -> feast  /api -> api  / -> ui|   |
 |  +-------------------------------------------+
 |                                              |
 |  +----------+  +----------+                  |
 |  | redis    |  | postgres |                  |   Data stores
 |  +----------+  | + PVC    |                  |
 |                +----------+                  |
 +----------------------------------------------+
```

Key design decisions:
- **2 replicas** for feast, api, and ui for availability.
- **ConfigMap-mounted feature_store.yaml** overrides the baked-in
  SQLite config with PostgreSQL + Redis connection strings.
- **PersistentVolumeClaim** for PostgreSQL ensures registry data
  survives pod restarts.
- **Resource requests/limits** on all pods prevent noisy-neighbor
  issues in a shared cluster.
- **Readiness and liveness probes** on all application pods enable
  automatic restart on failure.

## Data Flow

### Feature Registration
```
Team defines feature_views.py
  -> feast apply
    -> Writes metadata to Registry (PostgreSQL)
    -> Other teams can discover via API or UI
```

### Online Materialization
```
feast materialize
  -> Reads from Offline Store (Parquet)
  -> Writes latest values to Online Store (Redis)
  -> Feast server can now serve low-latency lookups
```

### Training Data Generation
```
store.get_historical_features(entity_df, features)
  -> Reads from Offline Store
  -> Performs point-in-time join on event_timestamp
  -> Returns DataFrame with correct historical values
```

### Feature Serving (inference)
```
ML model at prediction time
  -> Calls Feast server with entity keys
  -> Feast reads from Redis
  -> Returns feature vector in <10ms
```
