# Feature Store Platform

A production-grade ML feature store built on [Feast](https://feast.dev/),
with a FastAPI registry API, a Next.js catalog UI, and full Kubernetes
deployment manifests. Designed for multi-team organizations where data
scientists need to share, discover, and reuse ML features.

## Architecture

```
 Consumers (data scientists, ML pipelines)
       |                  |
       v                  v
+--------------+   +--------------+
|  Catalog UI  |   |  REST API    |    User-facing layer
|  (Next.js)   |   |  (FastAPI)   |
|  :3000       |   |  :8000       |
+------+-------+   +------+-------+
       |                  |
       +--------+---------+
                |
        +-------v--------+
        | Feast Feature   |                Feature serving layer
        | Server  :6566   |
        +---+--------+---+
            |        |
    +-------v--+ +---v-----------+
    |  Redis   | |  PostgreSQL   |     Storage layer
    |  Online  | |  Registry DB  |
    |  :6379   | |  :5432        |
    +----------+ +---------------+
                        |
              +---------v---------+
              |  Offline Store    |    Batch / training data
              |  (Parquet files)  |
              +-------------------+
```

## Project Structure

```
feature-store-platform/
|-- feast_repo/              Feast feature definitions & data
|   |-- feature_store.yaml     Registry & store configuration
|   |-- entities.py            Entity definitions (user)
|   |-- data_sources.py        Parquet file data sources
|   |-- feature_views.py       Feature view definitions
|   |-- generate_data.py       Sample data generator (1000 users)
|   `-- Dockerfile
|-- api/                     FastAPI registry API
|   |-- main.py                App entrypoint, CORS, health check
|   |-- routes.py              /features, /teams, /search endpoints
|   |-- feast_client.py        Feast SDK wrapper
|   |-- models.py              Pydantic request/response schemas
|   `-- Dockerfile
|-- catalog_ui/              Next.js feature catalog frontend
|   |-- app/                   App Router pages
|   |-- components/            Sidebar, FeatureCard
|   |-- lib/                   Types, mock data
|   `-- Dockerfile
|-- k8s/                     Kubernetes manifests
|   |-- namespace.yaml         feature-store namespace
|   |-- configmap.yaml         Env vars & Feast k8s config override
|   |-- redis.yaml             Redis deployment + service
|   |-- postgres.yaml          PostgreSQL + PVC + service
|   |-- feast.yaml             Feast server deployment + service
|   |-- api.yaml               API deployment + service
|   |-- catalog-ui.yaml        UI deployment + service
|   `-- ingress.yaml           nginx ingress routing
|-- scripts/
|   `-- simulate_platform.py   Multi-team simulation demo
|-- docs/                    Extended documentation
|-- docker-compose.yml       Local development stack
|-- requirements.txt         Python dependencies
`-- .gitignore
```

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

Services will be available at:
- Catalog UI: http://localhost:3000
- Registry API: http://localhost:8000  (docs at /docs)
- Feast server: http://localhost:6566
- Redis: localhost:6379
- PostgreSQL: localhost:5432

### Manual Setup

```bash
# Python API
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate sample data and apply Feast definitions
cd feast_repo
python generate_data.py
feast apply

# Start the API
cd ..
uvicorn api.main:app --reload

# Next.js UI (separate terminal)
cd catalog_ui
npm install
npm run dev
```

### Run the Simulation

```bash
python scripts/simulate_platform.py
```

Demonstrates three teams registering features, cross-team discovery,
and point-in-time correct historical retrieval.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Feature store | Feast | Feature definitions, serving, registry |
| Online store | Redis | Low-latency feature lookups |
| Registry DB | PostgreSQL | Feature metadata storage |
| Offline store | Parquet / file | Batch training data |
| API | FastAPI | REST API for feature catalog |
| Frontend | Next.js 14 + Tailwind | Feature discovery UI |
| Orchestration | Kubernetes | Production deployment |
| Local dev | Docker Compose | Single-command dev environment |

## Documentation

- [Architecture & Design Decisions](docs/ARCHITECTURE.md)
- [Getting Started Guide](docs/GETTING_STARTED.md)
- [API Reference](docs/API.md)
