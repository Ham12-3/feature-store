"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { TeamSummary } from "@/lib/types";
import { fetchFeatures, fetchTeams } from "@/lib/api";

const TEAM_COLORS: Record<string, string> = {
  "payments-team": "bg-indigo-400",
  "identity-team": "bg-emerald-400",
  "fraud-team": "bg-rose-400",
};

export default function Sidebar() {
  const searchParams = useSearchParams();
  const activeTeam = searchParams.get("team");

  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [viewCount, setViewCount] = useState(0);
  const [featureCount, setFeatureCount] = useState(0);

  useEffect(() => {
    fetchTeams().then(setTeams);
    fetchFeatures().then((fvs) => {
      setViewCount(fvs.length);
      setFeatureCount(fvs.reduce((s, fv) => s + fv.feature_count, 0));
    });
  }, []);

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-64 flex-col bg-slate-900 text-slate-300">
      {/* Logo */}
      <div className="border-b border-slate-700/50 px-6 py-5">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500 text-sm font-bold text-white">
            FC
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">
              Feature Catalog
            </h1>
            <p className="text-xs text-slate-500">
              {viewCount} views &middot; {featureCount} features
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <div className="mb-1 px-3 text-xs font-medium uppercase tracking-wider text-slate-500">
          Browse
        </div>

        <Link
          href="/"
          className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
            !activeTeam
              ? "bg-slate-800 text-white"
              : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
          }`}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
            />
          </svg>
          All Feature Views
        </Link>

        <div className="mb-1 mt-6 px-3 text-xs font-medium uppercase tracking-wider text-slate-500">
          Teams
        </div>

        {teams.map((team) => (
          <Link
            key={team.name}
            href={`/?team=${team.name}`}
            className={`mb-0.5 flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${
              activeTeam === team.name
                ? "bg-slate-800 text-white"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-3">
              <span
                className={`inline-block h-2 w-2 rounded-full ${TEAM_COLORS[team.name] ?? "bg-slate-400"}`}
              />
              {team.name}
            </span>
            <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-500">
              {team.feature_view_count}
            </span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-700/50 px-6 py-4">
        <p className="text-xs text-slate-600">Powered by Feast</p>
      </div>
    </aside>
  );
}
