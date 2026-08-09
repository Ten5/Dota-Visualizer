"use client";

import React, { useState } from "react";
import { Search, RefreshCw, UserCheck, CheckCircle2, AlertCircle, Film } from "lucide-react";
import { syncPlayerMatches, getPlayerMatches } from "@/lib/api";
import { PlayerProfileMatchesResponse } from "@/lib/types";

interface PlayerLookupProps {
  onPlayerSelected: (playerId: number, playerName: string) => void;
  selectedPlayerId: number;
  onOpenRecentVideos?: () => void;
}

export default function PlayerLookup({ onPlayerSelected, selectedPlayerId, onOpenRecentVideos }: PlayerLookupProps) {
  const [inputSteamId, setInputSteamId] = useState(selectedPlayerId ? selectedPlayerId.toString() : "");
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [profile, setProfile] = useState<PlayerProfileMatchesResponse | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleInputChange = (val: string) => {
    setInputSteamId(val);
    const parsed = parseInt(val.trim(), 10);
    if (!isNaN(parsed) && parsed > 0) {
      onPlayerSelected(parsed, profile?.player_name || `Player #${parsed}`);
    } else {
      onPlayerSelected(0, "");
    }
  };

  const handleFetchProfile = async (id: number) => {
    setLoading(true);
    setStatusMsg(null);
    try {
      const data = await getPlayerMatches(id);
      setProfile(data);
      onPlayerSelected(data.player_id, data.player_name);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load player history";
      setStatusMsg({ type: "error", text: message });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncMatches = async () => {
    const idNum = parseInt(inputSteamId, 10);
    if (isNaN(idNum) || idNum <= 0) {
      setStatusMsg({ type: "error", text: "Please enter a valid 32-bit Steam Account ID." });
      return;
    }

    setSyncing(true);
    setStatusMsg(null);
    try {
      const syncRes = await syncPlayerMatches(idNum);
      setStatusMsg({ type: "success", text: syncRes.message });
      await handleFetchProfile(idNum);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "OpenDota match sync failed";
      setStatusMsg({ type: "error", text: message });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            <UserCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Target Player Profile</h2>
            <p className="text-xs text-slate-400">Enter a 32-bit Steam ID to fetch OpenDota match history</p>
          </div>
        </div>

        {profile && (
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Profile Cached</span>
          </span>
        )}
      </div>

      {/* Search Input Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={inputSteamId}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder="32-bit Steam ID (e.g. 70388657)"
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
          />
          <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
        </div>

        <button
          type="button"
          onClick={() => handleFetchProfile(parseInt(inputSteamId, 10))}
          disabled={loading || syncing}
          className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Load History"}
        </button>

        <button
          type="button"
          onClick={handleSyncMatches}
          disabled={syncing || loading}
          className="px-5 py-3 rounded-xl gradient-bg-btn text-white text-sm font-semibold shadow-lg shadow-red-950/40 flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
          <span>{syncing ? "Syncing..." : "Sync OpenDota"}</span>
        </button>

        {onOpenRecentVideos && (
          <button
            type="button"
            onClick={onOpenRecentVideos}
            className="px-5 py-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-sm font-semibold border border-amber-500/20 transition-colors flex items-center justify-center gap-2"
          >
            <Film className="h-4 w-4" />
            <span>Recent Videos</span>
          </button>
        )}
      </div>

      {/* Status Message */}
      {statusMsg && (
        <div
          className={`p-3 rounded-xl flex items-center gap-2.5 text-xs font-medium border ${
            statusMsg.type === "success"
              ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-300"
              : "bg-red-950/30 border-red-500/30 text-red-300"
          }`}
        >
          {statusMsg.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Profile Card Banner */}
      {profile && (
        <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-red-600 font-black text-white text-xl shadow-md">
              {profile.player_name ? profile.player_name.charAt(0).toUpperCase() : "P"}
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>{profile.player_name}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-normal">
                  #{profile.player_id}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Total Matches: <span className="font-semibold text-slate-200">{profile.total_matches}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-400">
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-500">Public Status</span>
              <span className="font-semibold text-slate-200">
                {profile.is_public ? "Public Profile" : "Anonymous"}
              </span>
            </div>
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-500">Sample Match Count</span>
              <span className="font-semibold text-amber-400">{profile.matches.length} Matches</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
