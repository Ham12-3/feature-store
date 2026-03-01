"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FeatureViewDetail } from "@/lib/types";
import { fetchFeatureDetail } from "@/lib/api";

const TEAM_BADGE: Record<string, string> = {
  "payments-team": "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
  "identity-team": "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  "fraud-team": "bg-rose-50 text-rose-700 ring-rose-600/20",
};

const DTYPE_COLOR: Record<string, string> = {
  Float64: "bg-sky-50 text-sky-700",
  Int64: "bg-violet-50 text-violet-700",
  UnixTimestamp: "bg-amber-50 text-amber-700",
};

function formatTTL(seconds: number): string {
  if (seconds >= 86400) return `${Math.floor(seconds / 86400)} day(s)`;
  if (seconds >= 3600) return `${Math.floor(seconds / 3600)} hour(s)`;
  if (seconds >= 60) return `${Math.floor(seconds / 60)} min`;
  return `${seconds}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function FeatureDetailPage() {
  const { name } = useParams<{ name: string }>();
  const [fv, setFv] = useState<FeatureViewDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeatureDetail(name)
      .then(setFv)
      .finally(() => setLoading(false));
  }, [name]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-400">
        Loading...
      </div>
    );
  }

  if (!fv) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4">
        <p className="text-lg text-slate-400">Feature view not found.</p>
        <Link
          href="/"
          className="text-sm text-indigo-600 underline hover:text-indigo-800"
        >
          Back to catalog
        </Link>
      </div>
    );
  }

  const badgeClass =
    TEAM_BADGE[fv.owner_team] ?? "bg-gray-50 text-gray-700 ring-gray-600/20";

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 flex items-center gap-2 text-sm text-slate-400">
        <Link href="/" className="hover:text-indigo-600">
          Catalog
        </Link>
        <span>/</span>
        <Link
          href={`/?team=${fv.owner_team}`}
          className="hover:text-indigo-600"
        >
          {fv.owner_team}
        </Link>
        <span>/</span>
        <span className="text-slate-600">{fv.name}</span>
      </nav>

      {/* Header */}
      <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="font-mono text-xl font-bold text-slate-900">
              {fv.name}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
              {fv.description}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {fv.tier === "critical" && (
              <span className="inline-flex items-center rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
                Critical
              </span>
            )}
            {fv.tier === "standard" && (
              <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">
                Standard
              </span>
            )}
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${badgeClass}`}
            >
              {fv.owner_team}
            </span>
          </div>
        </div>

        {/* Metadata grid */}
        <div className="grid grid-cols-2 gap-4 border-t border-gray-100 pt-4 sm:grid-cols-4">
          <div>
            <p className="text-xs font-medium text-slate-400">Status</p>
            <p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-slate-700">
              <span
                className={`inline-block h-2 w-2 rounded-full ${fv.online ? "bg-green-500" : "bg-gray-300"}`}
              />
              {fv.online ? "Online" : "Offline"}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">Freshness SLA</p>
            <p className="mt-1 text-sm font-medium text-slate-700">
              {fv.freshness_sla}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">TTL</p>
            <p className="mt-1 text-sm font-medium text-slate-700">
              {fv.ttl_seconds ? formatTTL(fv.ttl_seconds) : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">Created</p>
            <p className="mt-1 text-sm font-medium text-slate-700">
              {fv.created_date ? formatDate(fv.created_date) : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Features table */}
      {fv.features && fv.features.length > 0 && (
        <div className="mb-8 rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Features ({fv.features.length})
            </h2>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Data Type</th>
                <th className="px-6 py-3">Entity</th>
                <th className="px-6 py-3">Source</th>
              </tr>
            </thead>
            <tbody>
              {fv.features.map((feat, i) => (
                <tr
                  key={feat.name}
                  className={
                    i < fv.features.length - 1
                      ? "border-b border-gray-50"
                      : ""
                  }
                >
                  <td className="px-6 py-3 font-mono text-sm text-slate-800">
                    {feat.name}
                  </td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ${DTYPE_COLOR[feat.dtype] ?? "bg-gray-50 text-gray-700"}`}
                    >
                      {feat.dtype}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-mono text-sm text-slate-500">
                    {fv.entities.join(", ")}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-500">
                    {fv.source_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Consuming models */}
      {fv.consuming_models && fv.consuming_models.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Consuming Models ({fv.consuming_models.length})
            </h2>
          </div>
          <div className="divide-y divide-gray-50">
            {fv.consuming_models.map((model) => (
              <div
                key={`${model.name}-${model.version}`}
                className="flex items-center justify-between px-6 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {model.name}{" "}
                    <span className="font-normal text-slate-400">
                      {model.version}
                    </span>
                  </p>
                  <p className="text-xs text-slate-400">{model.team}</p>
                </div>
                <p className="text-xs text-slate-400">
                  Trained {formatDate(model.last_trained)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
