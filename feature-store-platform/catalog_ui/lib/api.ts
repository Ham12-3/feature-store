/**
 * API client for the Feature Store Registry API.
 *
 * Tries the real backend first.  If the backend is unreachable (e.g.
 * running the UI standalone without Docker), silently falls back to
 * the mock data so the UI always renders something useful.
 */

import { FeatureViewDetail, FeatureViewSummary, TeamSummary } from "./types";
import { FEATURE_VIEWS, TEAMS } from "./mock-data";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---- Raw fetch helpers (throw on failure) ----------------------------------

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

// ---- Public functions (API-first, mock-fallback) ---------------------------

export async function fetchFeatures(): Promise<FeatureViewSummary[]> {
  try {
    const data = await get<FeatureViewSummary[]>("/features");
    if (data.length > 0) return data;
  } catch {}
  // Fallback: convert mock detail objects to summaries
  return FEATURE_VIEWS.map((fv) => ({
    name: fv.name,
    description: fv.description,
    owner_team: fv.owner_team,
    entities: fv.entities,
    feature_count: fv.feature_count,
    created_date: fv.created_date,
    freshness_sla: fv.freshness_sla,
    tier: fv.tier,
    online: fv.online,
  }));
}

export async function fetchFeatureDetail(
  name: string,
): Promise<FeatureViewDetail | null> {
  try {
    return await get<FeatureViewDetail>(`/features/${name}`);
  } catch {}
  // Fallback: look up from mock data
  return FEATURE_VIEWS.find((fv) => fv.name === name) ?? null;
}

export async function fetchTeams(): Promise<TeamSummary[]> {
  try {
    const data = await get<TeamSummary[]>("/teams");
    if (data.length > 0) return data;
  } catch {}
  return TEAMS;
}

export async function searchFeatures(
  query: string,
): Promise<FeatureViewSummary[]> {
  try {
    return await get<FeatureViewSummary[]>(
      `/features/search?q=${encodeURIComponent(query)}`,
    );
  } catch {}
  // Fallback: client-side search over mock data
  const q = query.toLowerCase();
  return FEATURE_VIEWS.filter((fv) => {
    const haystack = [fv.name, fv.description, fv.owner_team]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}
