export interface FeatureField {
  name: string;
  dtype: string;
}

export interface FeatureViewSummary {
  name: string;
  description: string;
  owner_team: string;
  entities: string[];
  feature_count: number;
  created_date: string;
  freshness_sla: string;
  tier: string;
  online: boolean;
}

export interface FeatureViewDetail extends FeatureViewSummary {
  features: FeatureField[];
  source_name: string;
  ttl_seconds: number;
  tags: Record<string, string>;
  consuming_models: ModelConsumer[];
}

export interface ModelConsumer {
  name: string;
  version: string;
  team: string;
  last_trained: string;
}

export interface TeamSummary {
  name: string;
  feature_view_count: number;
  feature_views: string[];
}
