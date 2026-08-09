"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Shield, Key, LogIn, LogOut, User, Sparkles } from "lucide-react";
import Logo from "@/components/Logo";
import { getSteamLoginUrl, mockSteamLogin, getAuthMe as getCurrentUser } from "@/lib/api";
import { UserResponse } from "@/lib/types";

export default function Navbar() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [showMockAuthModal, setShowMockAuthModal] = useState(false);
  const [mockId64, setMockId64] = useState("76561197960265728");
  const [loading, setLoading] = useState(false);

  const checkCurrentUser = useCallback(async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("dota_jwt_token") : null;
    if (!token) return;
    try {
      const u = await getCurrentUser(token);
      setUser(u);
    } catch {
      localStorage.removeItem("dota_jwt_token");
      setUser(null);
    }
  }, []);

  useEffect(() => {
    checkCurrentUser();
  }, [checkCurrentUser]);

  const handleSteamLogin = async () => {
    try {
      const loginUrl = await getSteamLoginUrl();
      window.location.href = loginUrl;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to initiate Steam login";
      alert(message);
    }
  };

  const handleMockLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const tokenData = await mockSteamLogin(mockId64);
      localStorage.setItem("dota_jwt_token", tokenData.access_token);
      const userProfile = await getCurrentUser(tokenData.access_token);
      setUser(userProfile);
      setShowMockAuthModal(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Mock login failed";
      alert(message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("dota_jwt_token");
    setUser(null);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 border border-red-500/40 shadow-lg shadow-red-950/50 group-hover:scale-105 transition-transform">
            <Logo className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-xl tracking-tight text-white">Dota Stats Visualizer</span>
            </div>
            <p className="text-xs text-slate-400">Match History & Race Animation Platform</p>
          </div>
        </Link>

        {/* Navigation Links & Auth Actions */}
        <div className="flex items-center gap-4">
          <Link
            href="/keys"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <Key className="h-4 w-4 text-amber-400" />
            <span>Developer API Keys</span>
          </Link>

          {user ? (
            <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 border border-amber-500/40 text-amber-400">
                  <User className="h-4 w-4" />
                </div>
                <div className="hidden sm:block">
                  <p className="text-xs font-semibold text-white">{user.display_name}</p>
                  <p className="text-[10px] text-slate-400">ID: {user.steam_id32}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {process.env.NODE_ENV !== "production" && (
                <button
                  onClick={() => setShowMockAuthModal(true)}
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 border border-slate-700 hover:border-slate-500 hover:bg-slate-800 transition-colors"
                >
                  <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                  <span>Dev Login</span>
                </button>
              )}

              <button
                onClick={handleSteamLogin}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white gradient-bg-btn shadow-lg shadow-red-950/40"
              >
                <LogIn className="h-4 w-4" />
                <span>Steam Login</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Dev Mock Auth Modal */}
      {showMockAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md glass-panel p-6 rounded-2xl border border-slate-700">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="h-6 w-6 text-amber-400" />
              <h3 className="text-lg font-bold text-white">Dev / Steam Mock Authentication</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Simulate Steam OpenID 2.0 authentication for local testing without Valve server redirection.
            </p>
            <form onSubmit={handleMockLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  64-bit Steam ID64
                </label>
                <input
                  type="text"
                  value={mockId64}
                  onChange={(e) => setMockId64(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-500"
                  placeholder="e.g. 76561197960265728"
                  required
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMockAuthModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-white gradient-bg-btn disabled:opacity-50"
                >
                  {loading ? "Authenticating..." : "Login as Mock User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}
