// Local AI Voice Studio — TypeScript Types

// ── System / Hardware ──
export interface SystemInfo {
  cpu: { name: string; cores_physical: number; cores_logical: number; architecture: string; usage_percent?: number };
  ram: { total_gb: number; available_gb: number; used_gb?: number; used_percent: number };
  gpu: {
    name: string;
    vendor: string;
    vram_total_gb: number;
    vram_free_gb: number;
    vram_used_gb?: number;
    vram_used_percent?: number;
    gpu_utilization_percent?: number;
    temperature_c?: number;
    driver_version?: string;
    detected: boolean;
  };
  cuda: { available: boolean; version: string; cudnn_version: string; compute_capability: string; device_count?: number };
  disk: { total_gb: number; free_gb: number; used_gb?: number; used_percent?: number };
  python_version: string;
  pytorch_version: string;
  os: { name: string; version: string };
  recommended_device: string;
  recommended_model_tier: string;
  recommended_models: Record<string, { id: string; name: string; engine: string; voice_cloning: boolean } | null>;
}

// ── Models ──
export interface ModelInfo {
  id: string;
  name: string;
  language: string;
  engine: string;
  description: string;
  size_gb: number;
  min_ram_gb: number;
  recommended_ram_gb: number;
  min_vram_gb: number;
  recommended_vram_gb: number;
  cpu_supported: boolean;
  cuda_supported: boolean;
  voice_cloning: boolean;
  languages_supported: string[];
  quality_score: number;
  speed_score: number;
  status: 'not_installed' | 'downloading' | 'installed' | 'error';
  is_active: boolean;
}

// ── Voices ──
export interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  duration_seconds: number;
  sample_rate: number;
  quality: string;
  quality_score: number;
  created_at: string;
  has_prompt?: boolean;
  ref_text?: string;
}

export interface AudioAnalysis {
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  rms_volume: number;
  peak_volume: number;
  silence_ratio: number;
  clipping_detected: boolean;
  noise_level: string;
  noise_score: number;
  quality: string;
  quality_score: number;
  warnings: string[];
  is_usable: boolean;
}

// ── TTS ──
export interface TTSRequest {
  text: string;
  language: string;
  voice_id?: string;
  instruct?: string;
  engine_id?: string;
  speed: number;
  pitch: number;
  volume: number;
  num_step?: number;
  guidance_scale?: number;
  denoise?: boolean;
  duration?: number;
  output_format: string;
}

export interface JobProgress {
  job_id: string;
  status: string;
  progress: number;
  progress_percent: number;
  stage: string;
  message: string;
  result?: {
    output_id: string;
    duration_seconds: number;
    wav_url: string;
    mp3_url: string;
    download_wav_url: string;
    download_mp3_url: string;
    model: string;
    language: string;
  };
  error?: string;
}

// ── History ──
export interface HistoryEntry {
  id: string;
  language: string;
  model: string;
  voice_profile: string;
  text: string;
  duration_seconds: number;
  format: string;
  wav_path: string;
  mp3_path: string;
  created_at: string;
}

export interface HistoryStats {
  generated_count: number;
  total_duration_seconds: number;
  total_duration_formatted: string;
  voice_profiles_count: number;
}

// ── Download Progress ──
export interface DownloadProgress {
  model_id: string;
  status: string;
  progress: number;
  progress_percent: number;
  downloaded_mb: number;
  total_mb: number;
  message: string;
}
