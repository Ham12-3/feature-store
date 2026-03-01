import { FeatureViewDetail, ModelConsumer, TeamSummary } from "./types";

const MODEL_CONSUMERS: Record<string, ModelConsumer[]> = {
  user_transaction_features: [
    {
      name: "Fraud Detection Model",
      version: "v2.1",
      team: "fraud-team",
      last_trained: "2026-02-15",
    },
    {
      name: "User Segmentation Model",
      version: "v1.3",
      team: "growth-team",
      last_trained: "2026-02-20",
    },
    {
      name: "Credit Scoring Model",
      version: "v3.0",
      team: "risk-team",
      last_trained: "2026-02-10",
    },
  ],
  user_profile_features: [
    {
      name: "User Segmentation Model",
      version: "v1.3",
      team: "growth-team",
      last_trained: "2026-02-20",
    },
    {
      name: "Churn Prediction Model",
      version: "v1.0",
      team: "retention-team",
      last_trained: "2026-02-18",
    },
  ],
  user_risk_features: [
    {
      name: "Fraud Detection Model",
      version: "v2.1",
      team: "fraud-team",
      last_trained: "2026-02-15",
    },
    {
      name: "Credit Scoring Model",
      version: "v3.0",
      team: "risk-team",
      last_trained: "2026-02-10",
    },
    {
      name: "Transaction Approval Model",
      version: "v4.2",
      team: "payments-team",
      last_trained: "2026-02-22",
    },
  ],
};

export const FEATURE_VIEWS: FeatureViewDetail[] = [
  {
    name: "user_transaction_features",
    description:
      "Aggregated transaction features per user including averages, totals, and recency metrics. Used across fraud detection, segmentation, and credit scoring.",
    owner_team: "payments-team",
    entities: ["user_id"],
    feature_count: 3,
    created_date: "2026-01-10T09:00:00Z",
    freshness_sla: "1h",
    tier: "critical",
    online: true,
    features: [
      { name: "avg_transaction_amount", dtype: "Float64" },
      { name: "total_transaction_count", dtype: "Int64" },
      { name: "last_transaction_date", dtype: "UnixTimestamp" },
    ],
    source_name: "user_transactions_source",
    ttl_seconds: 86400,
    tags: { owner: "payments-team", freshness_sla: "1h", tier: "critical" },
    consuming_models: MODEL_CONSUMERS["user_transaction_features"],
  },
  {
    name: "user_profile_features",
    description:
      "User profile and engagement features capturing account maturity and activity patterns. Powers segmentation and churn prediction models.",
    owner_team: "identity-team",
    entities: ["user_id"],
    feature_count: 2,
    created_date: "2026-01-12T14:30:00Z",
    freshness_sla: "24h",
    tier: "standard",
    online: true,
    features: [
      { name: "account_age_days", dtype: "Int64" },
      { name: "login_frequency", dtype: "Float64" },
    ],
    source_name: "user_transactions_source",
    ttl_seconds: 604800,
    tags: { owner: "identity-team", freshness_sla: "24h", tier: "standard" },
    consuming_models: MODEL_CONSUMERS["user_profile_features"],
  },
  {
    name: "user_risk_features",
    description:
      "User risk scoring features tracking transaction failure rates and chargeback history. Critical for real-time fraud prevention and transaction approval.",
    owner_team: "fraud-team",
    entities: ["user_id"],
    feature_count: 2,
    created_date: "2026-01-15T11:00:00Z",
    freshness_sla: "15m",
    tier: "critical",
    online: true,
    features: [
      { name: "failed_transaction_ratio", dtype: "Float64" },
      { name: "chargeback_count", dtype: "Int64" },
    ],
    source_name: "user_transactions_source",
    ttl_seconds: 86400,
    tags: { owner: "fraud-team", freshness_sla: "15m", tier: "critical" },
    consuming_models: MODEL_CONSUMERS["user_risk_features"],
  },
];

export const TEAMS: TeamSummary[] = (() => {
  const map = new Map<string, string[]>();
  for (const fv of FEATURE_VIEWS) {
    const list = map.get(fv.owner_team) ?? [];
    list.push(fv.name);
    map.set(fv.owner_team, list);
  }
  return Array.from(map.entries())
    .map(([name, views]) => ({
      name,
      feature_view_count: views.length,
      feature_views: views.sort(),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
})();
