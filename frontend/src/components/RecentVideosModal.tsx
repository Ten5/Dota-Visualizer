"use client";

import React, { useState, useEffect, useCallback } from "react";
import { X, Film, Play, Download, Clock, RefreshCw, AlertCircle, Sparkles } from "lucide-react";
import { listPlayerRenderJobs } from "@/lib/api";
import { RenderJobResponse } from "@/lib/types";

interface RecentVideosModalProps {
  playerId?: number;
  onClose: () => void;
  onSelectJob: (job: RenderJobResponse) => void;
}

export default function RecentVideosModal({
  playerId,
  onClose,
  onSelectJob,
}: RecentVideosModalProps) {
  const [jobs, setJobs] = useState<RenderJobResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activePreviewJobId, setActivePreviewJobId] = useState<string | null>(null);

  const backendBase = process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "")
    : "http://localhost:8050";

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await listPlayerRenderJobs(playerId && playerId > 0 ? playerId : undefined);
      setJobs(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load recent videos";
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  }, [playerId]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl glass-panel p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-6 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
              <Film className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Recent Generated Videos</h2>
              <p className="text-xs text-slate-400">
                View & play active video renders {playerId && playerId > 0 ? `for Player #${playerId}` : "(All Recent Renders)"} (Stored in 1-Hour Ephemeral Cache)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchJobs}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Refresh List"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {errorMsg && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="p-12 text-center text-xs text-slate-400">
              Loading recent video jobs...
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-12 text-center rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400 space-y-2">
              <Film className="h-8 w-8 text-slate-600 mx-auto" />
              <p>No recent video renders found.</p>
              <p className="text-[11px] text-slate-500">
                Submit a new render job from the Render Studio below to generate high-FPS MP4 videos!
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80 rounded-xl bg-slate-900/40 border border-slate-800">
              {jobs.map((j) => {
                const videoFullUrl = j.video_url
                  ? `${backendBase}${j.video_url}`
                  : `${backendBase}/api/v1/render/media/${j.job_id}.mp4`;
                const isPreviewActive = activePreviewJobId === j.job_id;

                return (
                  <div key={j.job_id} className="p-4 flex flex-col gap-3 hover:bg-slate-800/30 transition-colors rounded-xl">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white">{j.metric}</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                            {j.aspect_ratio}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                            {j.theme}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-400">
                          <span>Player: <code className="font-mono text-slate-300">#{j.player_id}</code></span>
                          <span>•</span>
                          <span>ID: <code className="font-mono text-slate-300">{j.job_id}</code></span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-slate-500" />
                            <span>{new Date(j.created_at).toLocaleTimeString()}</span>
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {j.status === "COMPLETED" ? (
                          <>
                            <button
                              onClick={() => setActivePreviewJobId(isPreviewActive ? null : j.job_id)}
                              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md transition-colors ${
                                isPreviewActive
                                  ? "bg-slate-700 text-white"
                                  : "bg-red-600 hover:bg-red-500 text-white shadow-red-950/40"
                              }`}
                            >
                              <Play className="h-3.5 w-3.5 fill-current" />
                              <span>{isPreviewActive ? "Close Player" : "Play Preview"}</span>
                            </button>
                            <a
                              href={videoFullUrl}
                              download={`${j.job_id}.mp4`}
                              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
                              title="Download MP4"
                            >
                              <Download className="h-4 w-4" />
                            </a>
                          </>
                        ) : j.status === "FAILED" ? (
                          <span className="px-3 py-1 rounded-lg text-xs font-semibold bg-red-950/50 text-red-400 border border-red-500/30">
                            Failed
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-lg text-xs font-semibold bg-amber-950/50 text-amber-400 border border-amber-500/30">
                            Rendering ({j.progress}%)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Inline HTML5 Video Preview Frame */}
                    {isPreviewActive && j.status === "COMPLETED" && (
                      <div className="w-full pt-2">
                        <div className="relative overflow-hidden rounded-xl bg-black border border-slate-700 p-1 flex items-center justify-center max-h-[380px]">
                          <video
                            controls
                            autoPlay
                            playsInline
                            preload="auto"
                            crossOrigin="anonymous"
                            className="w-full max-h-[360px] object-contain rounded-lg"
                          >
                            <source src={videoFullUrl} type="video/mp4" />
                            Your browser does not support HTML5 video playback.
                          </video>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
