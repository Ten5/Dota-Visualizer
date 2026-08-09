"use client";

import React, { useState } from "react";
import { Play, Flame, Film, Sparkles, Sliders, Palette } from "lucide-react";
import { submitRenderJob } from "@/lib/api";
import { RenderJobPayload, RenderJobResponse } from "@/lib/types";

interface RenderStudioProps {
  selectedPlayerId: number;
  onJobSubmitted: (job: RenderJobResponse) => void;
}

const METRICS = [
  { id: "Hero Impact Score", name: "⚡ Hero Impact Rating", desc: "Wins × √(Games) signature mains score" },
  { id: "Multi-Kill & Rampage Race", name: "🔥 Multi-Kill & Rampages", desc: "High-kill & teamfight slaughter race" },
  { id: "GPM Farming Efficiency", name: "🌾 GPM Farming Efficiency", desc: "Average Gold Per Min timeline" },
  { id: "Win Streak Master", name: "🏆 Win Streak Master", desc: "Longest winning sprees per hero" },
  { id: "Roshan & Aegis Claims", name: "🛡️ Roshan & Aegis Claims", desc: "Objective siege & boss kills" },
  { id: "Blitz Stomper (Fastest Victory)", name: "🚀 Blitz Stomper", desc: "Fastest push victory duration" },
  { id: "Hero Masteries", name: "👑 Hero Masteries", desc: "Most played main heroes race" },
  { id: "Total Wins", name: "🥇 Total Wins", desc: "Victory milestones per hero" },
  { id: "Win Rate % (Top 20 Mains)", name: "📈 Win Rate %", desc: "Win rate percentage for top mains" },
  { id: "Most Purchased Items", name: "⚔️ Most Purchased Items", desc: "Item purchase race history" },
  { id: "Role Evolution", name: "🎭 Role Evolution", desc: "Core vs Support role balance" },
  { id: "KDA Ratio (Efficiency)", name: "🎯 KDA Efficiency", desc: "Kill/Death/Assist ratio timeline" },
  { id: "Tower Damage (Thousands)", name: "🏰 Tower Damage", desc: "Objective siege damage" },
  { id: "Laning Preference", name: "🗺️ Laning Preference", desc: "Safe/Mid/Offlane distribution" },
  { id: "Total Damage (Millions)", name: "💥 Total Hero Damage", desc: "Combat damage dealt" },
  { id: "Total Deaths", name: "💀 Total Deaths", desc: "Casualty count timeline" },
  { id: "Total Gold (Millions)", name: "💰 Total Net Gold", desc: "Farming efficiency race" },
];

const THEMES = [
  { id: "Midnight Cyberpunk", name: "Midnight Cyberpunk" },
  { id: "Dire Crimson", name: "Dire Crimson" },
  { id: "Radiant Gold", name: "Radiant Gold" },
  { id: "Neon Emerald", name: "Neon Emerald" },
];

const QUALITIES = [
  { id: "Draft", label: "Draft (Fast)" },
  { id: "Normal", label: "Normal (30 FPS)" },
  { id: "High", label: "High (Smooth)" },
  { id: "Ultra", label: "Ultra (HD 60 FPS)" },
];

export default function RenderStudio({ selectedPlayerId, onJobSubmitted }: RenderStudioProps) {
  const [metric, setMetric] = useState("Hero Impact Score");
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [theme, setTheme] = useState("Midnight Cyberpunk");
  const [quality, setQuality] = useState("Normal");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlayerId || selectedPlayerId <= 0) {
      setErrorMsg("Please select or look up a valid player Steam ID first.");
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const payload: RenderJobPayload = {
        player_id: selectedPlayerId,
        metric,
        aspect_ratio: aspectRatio,
        theme,
        quality,
      };

      const jobResp = await submitRenderJob(payload);
      onJobSubmitted(jobResp);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to submit render job";
      setErrorMsg(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Video Render Studio</h2>
            <p className="text-xs text-slate-400">Configure race animation, layout ratio, and quality settings</p>
          </div>
        </div>

        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          Target Player: <span className="text-amber-400">#{selectedPlayerId || 70388657}</span>
        </span>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs font-medium">
          {errorMsg}
        </div>
      )}

      {/* 1. Metric Selection Grid */}
      <div className="space-y-2.5">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-amber-400" />
          <span>Select Visualization Metric</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
          {METRICS.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMetric(m.id)}
              className={`p-3 rounded-xl border text-left transition-all ${
                metric === m.id
                  ? "neon-border-red bg-red-950/30 text-white"
                  : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              <div className="font-semibold text-xs text-white truncate">{m.name}</div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">{m.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 2. Aspect Ratio & Quality Presets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-2">
        {/* Aspect Ratio */}
        <div className="space-y-2">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Film className="h-3.5 w-3.5 text-red-400" />
            <span>Aspect Ratio</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setAspectRatio("9:16")}
              className={`py-2.5 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 ${
                aspectRatio === "9:16"
                  ? "neon-border-red bg-red-950/30 text-white"
                  : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700"
              }`}
            >
              <span>📱 9:16 Shorts</span>
            </button>
            <button
              type="button"
              onClick={() => setAspectRatio("16:9")}
              className={`py-2.5 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 ${
                aspectRatio === "16:9"
                  ? "neon-border-red bg-red-950/30 text-white"
                  : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700"
              }`}
            >
              <span>🖥️ 16:9 Video</span>
            </button>
          </div>
        </div>

        {/* Quality Preset */}
        <div className="space-y-2">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sliders className="h-3.5 w-3.5 text-amber-400" />
            <span>Quality Preset</span>
          </label>
          <select
            value={quality}
            onChange={(e) => setQuality(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-red-500"
          >
            {QUALITIES.map((q) => (
              <option key={q.id} value={q.id}>
                {q.label}
              </option>
            ))}
          </select>
        </div>

        {/* UI Theme */}
        <div className="space-y-2">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Palette className="h-3.5 w-3.5 text-emerald-400" />
            <span>Visual Theme</span>
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-red-500"
          >
            {THEMES.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Submit Button */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={submitting || !selectedPlayerId || selectedPlayerId <= 0}
          className="w-full py-3.5 rounded-xl gradient-bg-btn text-white font-bold text-sm shadow-xl shadow-red-950/50 flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Play className="h-4 w-4 fill-current" />
          <span>
            {submitting
              ? "Submitting Job..."
              : !selectedPlayerId || selectedPlayerId <= 0
              ? "Enter a Steam Account ID Above to Begin"
              : "Generate Video Animation"}
          </span>
        </button>
      </div>
    </form>
  );
}
