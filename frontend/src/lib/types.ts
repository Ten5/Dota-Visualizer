export interface PlayerSyncResponse {
  player_id: number;
  player_name: string;
  total_matches: number;
  new_matches_synced: number;
  last_synced_at: string;
  message: string;
}

export interface PlayerProfileMatchesResponse {
  player_id: number;
  player_name: string;
  avatar_url?: string;
  is_public: boolean;
  total_matches: number;
  matches: Array<{
    match_id: number;
    start_time: number;
    hero_id: number;
    kills?: number;
    deaths?: number;
    assists?: number;
    radiant_win?: boolean;
  }>;
}

export interface RenderJobPayload {
  player_id: number;
  metric: string;
  aspect_ratio?: string;
  theme?: string;
  quality?: string;
  custom_audio_id?: string;
}

export interface RenderJobResponse {
  job_id: string;
  player_id: number;
  metric: string;
  aspect_ratio: string;
  theme: string;
  quality: string;
  custom_audio_id?: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "EXPIRED";
  progress: number;
  created_at: string;
  video_url?: string;
  expires_at?: string;
}

export interface RenderJobStatusResponse {
  job_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "EXPIRED";
  progress: number;
  video_url?: string;
  expires_at?: string;
  error_message?: string;
}

export interface ApiKeyResponse {
  id: number;
  name: string;
  key?: string;
  is_active: boolean;
  created_at: string;
}

export interface UserResponse {
  id: number;
  steam_id64: string;
  steam_id32: number;
  display_name: string;
  avatar_url?: string;
}
