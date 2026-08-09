"use client";

import React from "react";
import Navbar from "@/components/Navbar";
import ApiKeyManager from "@/components/ApiKeyManager";

export default function KeysPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0b0e14]">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 sm:px-6">
        <ApiKeyManager />
      </main>

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-medium">
        <p>Dota 2 History Visualized @ Ten5 | Made with Antigravity</p>
      </footer>
    </div>
  );
}
