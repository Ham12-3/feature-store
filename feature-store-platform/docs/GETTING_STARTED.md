# Getting Started

## Prerequisites

- Python 3.10+
- Node.js 18+ (for catalog UI)
- Docker & Docker Compose (for containerized setup)
- kubectl (for Kubernetes deployment)

## Option 1: Docker Compose (Recommended)

The fastest way to get the full stack running.

```bash
cd feature-store-platform
docker compose up --build
```

This starts all 5 services:

| Service | URL | Description |
|---------|-----|-------------|
| Catalog UI | http://localhost:3000 | Feature discovery frontend |
| Registry API | http://localhost:8000 | REST API (Swagger at /docs) |
| Feast Server | http://localhost:6566 | Online feature serving |
| Redis | localhost:6379 | Online store |
| PostgreSQL | localhost:5432 | Registry database |

To stop: `docker compose down`
To stop and remove volumes: `docker compose down -v`

## Option 2: Manual Local Setup

### Step 1: Python Environment

```bash
cd feature-store-platform

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2: Generate Sample Data

```bash
cd feast_repo
python generate_data.py
```

This creates `data/user_transactions.parquet` with 1,000 users.

### Step 3: Apply Feast Definitions

```bash
# Still inside feast_repo/
feast apply
```

This registers entities, data sources, and feature views in the
local SQLite registry (`data/registry.db`).

### Step 4: Start the Feast Feature Server

```bash
feast serve -h 0.0.0.0 -p 6566
```

Leave this running in a terminal.

### Step 5: Start the FastAPI Server

```bash
# In a new terminal, from the project root
cd feature-store-platform
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Verify:
- Health check: http://localhost:8000/health
- Swagger docs: http://localhost:8000/docs
- List features: http://localhost:8000/features

### Step 6: Start the Catalog UI

```bash
# In a new terminal
cd catalog_ui
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Step 7: Run the Simulation

```bash
# From the project root
python scripts/simulate_platform.py
```

This runs the full multi-team demo:
1. Generates data for 3 teams
2. Registers features to a temporary registry
3. Shows cross-team feature discovery
4. Verifies point-in-time correct retrieval
5. Demonstrates cross-team feature joins

## Option 3: Kubernetes Deployment

### Prerequisites
- A running Kubernetes cluster (minikube, kind, EKS, GKE, etc.)
- kubectl configured to talk to your cluster
- Container images built and accessible

### Build Images

```bash
# Feast server
docker build -t feature-store-platform/feast:latest ./feast_repo

# API server (context = project root)
docker build -t feature-store-platform/api:latest -f api/Dockerfile .

# Catalog UI
docker build -t feature-store-platform/catalog-ui:latest ./catalog_ui
```

If using a remote registry, tag and push:
```bash
docker tag feature-store-platform/feast:latest your-registry/feast:latest
docker push your-registry/feast:latest
# ... repeat for api and catalog-ui
```

### Deploy

```bash
# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Then apply everything else
kubectl apply -f k8s/

# Verify pods are running
kubectl get pods -n feature-store
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
api-xxxxxx-xxxxx              1/1     Running   0          1m
catalog-ui-xxxxxx-xxxxx       1/1     Running   0          1m
feast-xxxxxx-xxxxx            1/1     Running   0          1m
postgres-xxxxxx-xxxxx         1/1     Running   0          1m
redis-xxxxxx-xxxxx            1/1     Running   0          1m
```

### Access via Ingress

If using an nginx ingress controller:

```bash
# Add to /etc/hosts (or use your ingress IP)
127.0.0.1 features.localhost
```

- UI: http://features.localhost/
- API: http://features.localhost/api/
- Feast: http://features.localhost/feast/

## Verifying the Setup

### API Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "feast_connected": true,
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### List Features

```bash
curl http://localhost:8000/features
```

Should return 3 feature views.

### Retrieve Features

```bash
curl -X POST http://localhost:8000/features/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "features": [
      "user_transaction_features:avg_transaction_amount",
      "user_risk_features:chargeback_count"
    ],
    "entities": {
      "user_id": ["user_0001", "user_0002"]
    }
  }'
```

## Troubleshooting

### "Registry not found" errors
Run `feast apply` inside `feast_repo/` to initialize the registry.

### API returns "degraded" health
The Feast registry is unreachable. Check that `feast_repo/data/registry.db`
exists (local) or that PostgreSQL is running (Docker/k8s).

### Catalog UI shows no data
The UI ships with mock data and works standalone. If connected to the
API, ensure `NEXT_PUBLIC_API_URL` points to the running API server.

### Docker build fails for catalog_ui
Run `cd catalog_ui && npm install` first to generate `package-lock.json`,
which the Dockerfile expects.
