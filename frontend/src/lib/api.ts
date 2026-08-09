import {
  PlayerSyncResponse,
  PlayerProfileMatchesResponse,
  RenderJobPayload,
  RenderJobResponse,
  RenderJobStatusResponse,
  ApiKeyResponse,
  UserResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1";

export async function syncPlayerMatches(playerId: number): Promise<PlayerSyncResponse> {
  const res = await fetch(`${API_BASE_URL}/players/${playerId}/sync`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to sync matches for player ${playerId}`);
  }
  return res.json();
}

export async function getPlayerMatches(playerId: number): Promise<PlayerProfileMatchesResponse> {
  const res = await fetch(`${API_BASE_URL}/players/${playerId}/matches`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch match history for player ${playerId}`);
  }
  return res.json();
}

export async function submitRenderJob(payload: RenderJobPayload): Promise<RenderJobResponse> {
  const res = await fetch(`${API_BASE_URL}/render/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to submit video render job");
  }
  return res.json();
}

export async function getRenderJobStatus(jobId: string): Promise<RenderJobStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/render/jobs/${jobId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to poll status for job ${jobId}`);
  }
  return res.json();
}

export async function listPlayerRenderJobs(playerId?: number): Promise<RenderJobResponse[]> {
  const url = playerId && playerId > 0
    ? `${API_BASE_URL}/render/jobs?player_id=${playerId}`
    : `${API_BASE_URL}/render/jobs`;
  const res = await fetch(url);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch render jobs");
  }
  return res.json();
}

export async function getSteamLoginUrl(): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/auth/steam/login`);
  if (!res.ok) throw new Error("Failed to fetch Steam login URL");
  const data = await res.json();
  return data.login_url;
}

export async function mockSteamLogin(steamId64: string): Promise<{ access_token: string }> {
  const res = await fetch(`${API_BASE_URL}/auth/steam/callback?mock_steam_id64=${steamId64}`);
  if (!res.ok) throw new Error("Failed to authenticate with mock Steam ID");
  return res.json();
}

export async function getAuthMe(token: string): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Invalid or expired session token");
  return res.json();
}

export async function createApiKey(name: string, token: string): Promise<ApiKeyResponse> {
  const res = await fetch(`${API_BASE_URL}/keys`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to create API key");
  }
  return res.json();
}

export async function listApiKeys(token: string): Promise<ApiKeyResponse[]> {
  const res = await fetch(`${API_BASE_URL}/keys`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Failed to list API keys");
  return res.json();
}

export async function revokeApiKey(keyId: number, token: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/keys/${keyId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Failed to revoke API key");
}
