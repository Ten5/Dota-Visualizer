"use client";

import React, { useEffect, useState } from "react";
import { X, Download, Play, AlertCircle, CheckCircle2, Loader2, Clock } from "lucide-react";
import { getRenderJobStatus } from "@/lib/api";
import { RenderJobResponse, RenderJobStatusResponse } from "@/lib/types";

interface VideoPlayerModalProps {
  job: RenderJobResponse;
  onClose: () => void;
}

export default function VideoPlayerModal({ job, onClose }: VideoPlayerModalProps) {
  const [jobStatus, setJobStatus] = useState<RenderJobStatusResponse>({
    job_id: job.job_id,
    status: job.status,
    progress: job.progress,
  });

  useEffect(() => {
    if (jobStatus.status === "COMPLETED" || jobStatus.status === "FAILED" || jobStatus.status === "EXPIRED") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getRenderJobStatus(job.job_id);
        setJobStatus(updated);
        if (updated.status === "COMPLETED" || updated.status === "FAILED" || updated.status === "EXPIRED") {
          clearInterval(interval);
        }
      } catch (e) {
        console.error("Error polling job status:", e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [job.job_id, jobStatus.status]);

  const backendBase = process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.trim().replace(/\/api\/v1\/?$/, "").replace(/\/+$/, "")
    : "http://localhost:8050";

  const fullVideoUrl = jobStatus.video_url
    ? `${backendBase}${jobStatus.video_url}`
    : undefined;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl glass-panel p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-5">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
              <Play className="h-5 w-5 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Render Job Progress</h3>
              <p className="text-xs font-mono text-slate-400">ID: {job.job_id}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Status Indicator & Animated Progress Bar */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-2 text-slate-300">
              {jobStatus.status === "COMPLETED" ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="text-emerald-400 font-bold">Rendering Complete!</span>
                </>
              ) : jobStatus.status === "FAILED" ? (
                <>
                  <AlertCircle className="h-4 w-4 text-red-400" />
                  <span className="text-red-400 font-bold">Rendering Failed</span>
                </>
              ) : (
                <>
                  <Loader2 className="h-4 w-4 text-amber-400 animate-spin" />
                  <span>
                    {jobStatus.progress < 30
                      ? "Ingesting match history..."
                      : jobStatus.progress < 75
                      ? "Rendering OpenCV frames & typography..."
                      : "Adding audio & encoding MP4..."}
                  </span>
                </>
              )}
            </span>

            <span className="font-mono text-amber-400 text-sm font-bold">{jobStatus.progress}%</span>
          </div>

          {/* Progress Bar Track */}
          <div className="w-full h-3 rounded-full bg-slate-900 overflow-hidden border border-slate-800 p-0.5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-red-600 via-amber-500 to-emerald-400 transition-all duration-300 shadow-md shadow-red-950/50"
              style={{ width: `${Math.max(jobStatus.progress, 5)}%` }}
            />
          </div>
        </div>

        {/* Video Player Box */}
        {jobStatus.status === "COMPLETED" && fullVideoUrl ? (
          <div className="space-y-4">
            <div className="relative overflow-hidden rounded-xl bg-black border border-slate-800 shadow-inner flex items-center justify-center max-h-[420px]">
              <video
                controls
                autoPlay
                playsInline
                preload="auto"
                crossOrigin="anonymous"
                className="w-full max-h-[400px] object-contain rounded-xl"
              >
                <source src={fullVideoUrl} type="video/mp4" />
                Your browser does not support inline video playback.
              </video>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Clock className="h-3.5 w-3.5 text-slate-500" />
                <span>Expires in 1 Hour (Ephemeral Storage)</span>
              </div>

              <a
                href={fullVideoUrl}
                download={`${job.job_id}.mp4`}
                className="px-5 py-2.5 rounded-xl gradient-bg-btn text-white text-xs font-bold shadow-lg flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                <span>Download MP4 Video</span>
              </a>
            </div>
          </div>
        ) : jobStatus.status === "FAILED" ? (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs space-y-1">
            <div className="font-bold text-red-200">Error Description:</div>
            <div>{jobStatus.error_message || "An error occurred during video rendering pipeline execution."}</div>
          </div>
        ) : (
          <div className="p-12 text-center rounded-xl bg-slate-900/50 border border-slate-800/80 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-10 w-10 text-amber-400 animate-spin" />
            <p className="text-xs text-slate-400">
              Generating native video frames on background Celery worker queue...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
