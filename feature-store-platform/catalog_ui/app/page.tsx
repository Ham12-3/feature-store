"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import FeatureCard from "@/components/FeatureCard";
import { FeatureViewSummary } from "@/lib/types";
import { fetchFeatures, searchFeatures } from "@/lib/api";

function HomeContent() {
  const searchParams = useSearchParams();
  const teamFilter = searchParams.get("team");
  const [search, setSearch] = useState("");
  const [allFeatures, setAllFeatures] = useState<FeatureViewSummary[]>([]);

  // Load features from API (falls back to mock data automatically)
  useEffect(() => {
    fetchFeatures().then(setAllFeatures);
  }, []);

  // When the user types a search query, ask the API
  useEffect(() => {
    if (!search) {
      fetchFeatures().then(setAllFeatures);
      return;
    }
    const timer = setTimeout(() => {
      searchFeatures(search).then(setAllFeatures);
    }, 200); // small debounce
    return () => clearTimeout(timer);
  }, [search]);

  const filtered = useMemo(() => {
    if (!teamFilter) return allFeatures;
    return allFeatures.filter((fv) => fv.owner_team === teamFilter);
  }, [teamFilter, allFeatures]);

  const grouped = useMemo(() => {
    const map = new Map<string, FeatureViewSummary[]>();
    for (const fv of filtered) {
      const list = map.get(fv.owner_team) ?? [];
      list.push(fv);
      map.set(fv.owner_team, list);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  const totalFeatures = filtered.reduce(
    (sum, fv) => sum + fv.feature_count,
    0,
  );

  return (
    <div className="mx-auto max-w-5xl px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          {teamFilter ? (
            <>
              <span className="text-slate-400">Team /</span> {teamFilter}
            </>
          ) : (
            "Feature Catalog"
          )}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Browse and discover ML features across your organization.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <svg
          className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search features by name, description, or tag..."
          className="w-full rounded-xl border border-gray-200 bg-white py-3 pl-11 pr-4 text-sm shadow-sm transition-colors placeholder:text-slate-400 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        />
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
          <p className="text-2xl font-bold text-slate-900">{filtered.length}</p>
          <p className="text-xs text-slate-500">Feature Views</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
          <p className="text-2xl font-bold text-slate-900">{totalFeatures}</p>
          <p className="text-xs text-slate-500">Total Features</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
          <p className="text-2xl font-bold text-slate-900">{grouped.length}</p>
          <p className="text-xs text-slate-500">Teams</p>
        </div>
      </div>

      {/* Feature groups */}
      {grouped.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 py-16 text-center">
          <p className="text-sm text-slate-400">
            No feature views match your search.
          </p>
        </div>
      )}

      {grouped.map(([team, views]) => (
        <section key={team} className="mb-10">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-400">
            <span className="inline-block h-2 w-2 rounded-full bg-indigo-400" />
            {team}
            <span className="ml-1 font-normal">({views.length})</span>
          </h2>
          <div className="grid gap-4">
            {views.map((fv) => (
              <FeatureCard key={fv.name} fv={fv} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-slate-400">
          Loading...
        </div>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
