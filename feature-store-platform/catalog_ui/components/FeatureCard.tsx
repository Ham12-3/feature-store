import Link from "next/link";
import { FeatureViewSummary } from "@/lib/types";

const TEAM_BADGE: Record<string, string> = {
  "payments-team": "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
  "identity-team": "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  "fraud-team": "bg-rose-50 text-rose-700 ring-rose-600/20",
};

// Accepts both Summary and Detail objects -- optional fields degrade gracefully.
export default function FeatureCard({
  fv,
}: {
  fv: FeatureViewSummary & {
    ttl_seconds?: number;
    consuming_models?: { name: string }[];
  };
}) {
  const badgeClass =
    TEAM_BADGE[fv.owner_team] ?? "bg-gray-50 text-gray-700 ring-gray-600/20";

  return (
    <Link href={`/features/${fv.name}`}>
      <div className="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md">
        {/* Header row */}
        <div className="mb-3 flex items-start justify-between">
          <h3 className="font-mono text-sm font-semibold text-slate-900 group-hover:text-indigo-600">
            {fv.name}
          </h3>
          <div className="flex items-center gap-2">
            {fv.tier === "critical" && (
              <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
                critical
              </span>
            )}
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${badgeClass}`}
            >
              {fv.owner_team}
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="mb-4 line-clamp-2 text-sm text-slate-500">
          {fv.description}
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${fv.online ? "bg-green-500" : "bg-gray-300"}`}
            />
            {fv.online ? "Online" : "Offline"}
          </span>
          <span>{fv.feature_count} features</span>
          <span>SLA: {fv.freshness_sla}</span>
          {fv.ttl_seconds != null && (
            <span>TTL: {formatTTL(fv.ttl_seconds)}</span>
          )}
          {fv.consuming_models != null && (
            <span>
              {fv.consuming_models.length} model
              {fv.consuming_models.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

function formatTTL(seconds: number): string {
  if (seconds >= 86400) return `${Math.floor(seconds / 86400)}d`;
  if (seconds >= 3600) return `${Math.floor(seconds / 3600)}h`;
  if (seconds >= 60) return `${Math.floor(seconds / 60)}m`;
  return `${seconds}s`;
}
