"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Key, Plus, Trash2, Copy, Check, ShieldAlert, Sparkles } from "lucide-react";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/api";
import { ApiKeyResponse } from "@/lib/types";

export default function ApiKeyManager() {
  const [keys, setKeys] = useState<ApiKeyResponse[]>([]);
  const [keyName, setKeyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("dota_jwt_token") : null;

  const loadKeys = useCallback(async () => {
    if (!token) return;
    try {
      const data = await listApiKeys(token);
      setKeys(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load keys";
      setErrorMsg(message);
    }
  }, [token]);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMsg("Please log in with Steam to create developer API keys.");
      return;
    }
    if (!keyName.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await createApiKey(keyName, token);
      if (res.key) {
        setNewlyCreatedKey(res.key);
      }
      setKeyName("");
      await loadKeys();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to generate key";
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (id: number) => {
    if (!token) return;
    if (!confirm("Are you sure you want to revoke this API key?")) return;
    try {
      await revokeApiKey(id, token);
      await loadKeys();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Revocation failed";
      alert(message);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!token) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center space-y-4 max-w-xl mx-auto">
        <ShieldAlert className="h-10 w-10 text-amber-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Authentication Required</h3>
        <p className="text-xs text-slate-400">
          Please log in using Steam OpenID (or Dev Mock Login) to create and manage developer API keys.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Key className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Developer Security & API Keys</h2>
            <p className="text-xs text-slate-400">
              Generate SHA-256 hashed API keys (`X-API-Key` header) for external integration
            </p>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs font-medium">
          {errorMsg}
        </div>
      )}

      {/* Newly Generated Key Alert Box */}
      {newlyCreatedKey && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/50 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
              <Sparkles className="h-4 w-4" />
              <span>Copy Your Secret API Key Now</span>
            </span>
            <button
              onClick={() => setNewlyCreatedKey(null)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Dismiss
            </button>
          </div>
          <p className="text-[11px] text-amber-200/80">
            This secret key will <strong>never be shown again</strong>. Store it securely in your application environment.
          </p>
          <div className="flex items-center gap-2 pt-1">
            <input
              type="text"
              readOnly
              value={newlyCreatedKey}
              className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-amber-500/30 font-mono text-xs text-amber-400 select-all focus:outline-none"
            />
            <button
              onClick={() => copyToClipboard(newlyCreatedKey)}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold flex items-center gap-1.5"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied!" : "Copy Key"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Key Form */}
      <form onSubmit={handleCreateKey} className="flex gap-3">
        <input
          type="text"
          value={keyName}
          onChange={(e) => setKeyName(e.target.value)}
          placeholder="Key Description / App Name (e.g. CLI Production Worker)"
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 rounded-xl gradient-bg-btn text-white text-xs font-bold flex items-center gap-1.5 shadow-lg disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          <span>{loading ? "Generating..." : "Generate New Key"}</span>
        </button>
      </form>

      {/* Active Keys List */}
      <div className="space-y-3 pt-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Active API Keys ({keys.length})
        </h3>

        {keys.length === 0 ? (
          <div className="p-6 text-center rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-500">
            No active API keys found. Generate a key above to access developer APIs.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80 rounded-xl bg-slate-900/40 border border-slate-800">
            {keys.map((k) => (
              <div key={k.id} className="p-4 flex items-center justify-between gap-4">
                <div>
                  <div className="font-semibold text-xs text-white">{k.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    ID: {k.id} | Created: {new Date(k.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Active
                  </span>
                  <button
                    onClick={() => handleRevokeKey(k.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                    title="Revoke Key"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
