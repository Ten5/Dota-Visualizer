"use client";

import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import PlayerLookup from "@/components/PlayerLookup";
import RenderStudio from "@/components/RenderStudio";
import VideoPlayerModal from "@/components/VideoPlayerModal";
import RecentVideosModal from "@/components/RecentVideosModal";
import { Film } from "lucide-react";
import { RenderJobResponse } from "@/lib/types";

export default function HomePage() {
  const [selectedPlayerId, setSelectedPlayerId] = useState<number>(0);
  const [playerName, setPlayerName] = useState<string>("");
  const [activeJob, setActiveJob] = useState<RenderJobResponse | null>(null);
  const [showRecentModal, setShowRecentModal] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0e14]">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 sm:px-6 space-y-8">
        {/* Hero Section Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-red-950/40 to-slate-900 border border-slate-800 p-8 sm:p-10 shadow-2xl">
          <div className="relative z-10 max-w-2xl space-y-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              🎮 Dota Stats Visualizer
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Transform Dota 2 Match History into <span className="gradient-text-dota">High-FPS Video Animations</span>
            </h1>
            <p className="text-sm text-slate-300">
              Fetch player stats from OpenDota, calculate time-series metric races, and render videos directly in your browser.
            </p>
          </div>

          {/* Decorative Background Accent */}
          <div className="absolute right-[-40px] top-[-40px] h-72 w-72 rounded-full bg-red-600/10 blur-3xl pointer-events-none" />
        </div>

        {/* 1. Player Lookup & OpenDota Sync Component */}
        <PlayerLookup
          selectedPlayerId={selectedPlayerId}
          onPlayerSelected={(id, name) => {
            setSelectedPlayerId(id);
            setPlayerName(name);
          }}
          onOpenRecentVideos={() => setShowRecentModal(true)}
        />

        {/* 2. Video Render Studio Component */}
        <RenderStudio
          selectedPlayerId={selectedPlayerId}
          onJobSubmitted={(job) => setActiveJob(job)}
        />
      </main>

      {/* 3. Live Video Player Overlay Modal */}
      {activeJob && (
        <VideoPlayerModal
          job={activeJob}
          onClose={() => setActiveJob(null)}
        />
      )}

      {/* 4. Recent Videos Modal */}
      {showRecentModal && (
        <RecentVideosModal
          playerId={selectedPlayerId > 0 ? selectedPlayerId : undefined}
          onClose={() => setShowRecentModal(false)}
          onSelectJob={(job) => {
            setShowRecentModal(false);
            setActiveJob(job);
          }}
        />
      )}

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-medium">
        <p>Dota 2 History Visualized @ Ten5 | Made with Antigravity</p>
      </footer>
    </div>
  );
}
