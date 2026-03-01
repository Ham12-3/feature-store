# API Reference

Base URL: `http://localhost:8000`

Interactive Swagger docs: `http://localhost:8000/docs`

---

## GET /health

Health check endpoint. Verifies API liveness and Feast registry
connectivity.

**Response** `200 OK`

```json
{
  "status": "healthy",
  "feast_connected": true,
  "timestamp": "2026-02-28T12:00:00.000000+00:00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"healthy"` if Feast is reachable, `"degraded"` otherwise |
| feast_connected | boolean | Whether the Feast registry responded |
| timestamp | datetime | Server time (UTC) |

---

## GET /features

List all registered feature views with summary metadata.

**Response** `200 OK`

```json
[
  {
    "name": "user_transaction_features",
    "description": "Aggregated transaction features per user",
    "owner_team": "payments-team",
    "entities": ["user_id"],
    "feature_count": 3,
    "created_date": "2026-01-10T09:00:00",
    "freshness_sla": "1h",
    "tier": "critical",
    "online": true
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| name | string | Unique feature view identifier |
| description | string | Human-readable description |
| owner_team | string | Team responsible (from `owner` tag) |
| entities | string[] | Join keys for this view |
| feature_count | integer | Number of features (excludes entity columns) |
| created_date | datetime | When the view was first registered |
| freshness_sla | string | Maximum acceptable data staleness |
| tier | string | `"critical"` or `"standard"` |
| online | boolean | Whether features are materialized for serving |

---

## GET /features/search?q={query}

Search feature views by name, description, tag values, or individual
feature names. Case-insensitive substring match.

**Parameters**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| q | query | string | Yes | Search term (min 1 character) |

**Example**

```
GET /features/search?q=fraud
GET /features/search?q=amount
GET /features/search?q=critical
```

**Response** `200 OK` -- Same schema as `GET /features`, filtered
to matching views.

```json
[
  {
    "name": "user_risk_features",
    "description": "User risk scoring features",
    "owner_team": "fraud-team",
    "entities": ["user_id"],
    "feature_count": 2,
    "created_date": "2026-01-15T11:00:00",
    "freshness_sla": "15m",
    "tier": "critical",
    "online": true
  }
]
```

---

## GET /features/{name}

Get full details of a specific feature view, including individual
features, data types, source info, and all tags.

**Parameters**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| name | path | string | Yes | Feature view name |

**Example**

```
GET /features/user_transaction_features
```

**Response** `200 OK`

```json
{
  "name": "user_transaction_features",
  "description": "Aggregated transaction features per user",
  "owner_team": "payments-team",
  "entities": ["user_id"],
  "features": [
    { "name": "avg_transaction_amount", "dtype": "Float64" },
    { "name": "total_transaction_count", "dtype": "Int64" },
    { "name": "last_transaction_date", "dtype": "UnixTimestamp" }
  ],
  "source_name": "user_transactions_source",
  "ttl_seconds": 86400,
  "created_date": "2026-01-10T09:00:00",
  "freshness_sla": "1h",
  "tier": "critical",
  "online": true,
  "tags": {
    "owner": "payments-team",
    "freshness_sla": "1h",
    "tier": "critical"
  }
}
```

**Error** `404 Not Found`

```json
{
  "detail": "Feature view 'nonexistent' not found"
}
```

---

## GET /teams

List all teams and their owned feature views. Teams are derived
dynamically from the `owner` tag on each feature view.

**Response** `200 OK`

```json
[
  {
    "name": "fraud-team",
    "feature_view_count": 1,
    "feature_views": ["user_risk_features"]
  },
  {
    "name": "identity-team",
    "feature_view_count": 1,
    "feature_views": ["user_profile_features"]
  },
  {
    "name": "payments-team",
    "feature_view_count": 1,
    "feature_views": ["user_transaction_features"]
  }
]
```

---

## POST /features/retrieve

Retrieve historical feature values for a set of entities. Uses
Feast's point-in-time join to return the correct feature values
as of the query timestamp.

**Request Body**

```json
{
  "features": [
    "user_transaction_features:avg_transaction_amount",
    "user_risk_features:chargeback_count"
  ],
  "entities": {
    "user_id": ["user_0001", "user_0002", "user_0003"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| features | string[] | Feature references in `view_name:feature_name` format |
| entities | object | Entity key-value pairs. Keys are entity names, values are arrays of entity IDs |

**Response** `200 OK`

```json
{
  "results": [
    {
      "user_id": "user_0001",
      "event_timestamp": "2026-02-28 12:00:00",
      "avg_transaction_amount": 156.42,
      "chargeback_count": 0
    },
    {
      "user_id": "user_0002",
      "event_timestamp": "2026-02-28 12:00:00",
      "avg_transaction_amount": 892.10,
      "chargeback_count": 2
    }
  ]
}
```

**Error** `400 Bad Request`

Returned when the feature reference is malformed or the feature
view does not exist.

```json
{
  "detail": "Feature view 'nonexistent' does not exist..."
}
```

---

## Error Responses

All endpoints may return standard HTTP error codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (malformed input, invalid feature references) |
| 404 | Resource not found (unknown feature view name) |
| 422 | Validation error (missing required parameters) |
| 500 | Internal server error |

Validation errors (422) follow the FastAPI format:

```json
{
  "detail": [
    {
      "loc": ["query", "q"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## CORS

The API allows all origins (`*`) for development. In production,
restrict `allow_origins` in `api/main.py` to your frontend domain.
