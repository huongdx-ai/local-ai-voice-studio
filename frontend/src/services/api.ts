// Local AI Voice Studio — API Service Layer

const API_BASE = 'http://127.0.0.1:8000';

import type {
  SystemInfo,
  ModelInfo,
  VoiceProfile,
  AudioAnalysis,
  TTSRequest,
  JobProgress,
  HistoryEntry,
  HistoryStats,
} from '../types';

// ── Helper ──
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── System ──
export async function getSystemInfo(): Promise<SystemInfo> {
  return fetchJSON<SystemInfo>('/api/system');
}

// ── Models ──
export async function getModels(): Promise<ModelInfo[]> {
  const data = await fetchJSON<{ models: ModelInfo[] }>('/api/models');
  return data.models;
}

export async function downloadModel(
  modelId: string,
  onProgress?: (data: any) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/models/${modelId}/download`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Download request failed');

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          onProgress?.(data);
        } catch {}
      }
    }
  }
}

export async function deleteModel(modelId: string): Promise<void> {
  await fetchJSON(`/api/models/${modelId}`, { method: 'DELETE' });
}

export async function activateModel(modelId: string): Promise<void> {
  await fetchJSON(`/api/models/${modelId}/activate`, { method: 'POST' });
}

// ── Voices ──
export async function getVoices(): Promise<VoiceProfile[]> {
  const data = await fetchJSON<{ voices: VoiceProfile[] }>('/api/voices');
  return data.voices;
}

export async function uploadVoice(
  file: File,
  name: string,
  language: string
): Promise<{ profile: VoiceProfile; analysis: AudioAnalysis }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  formData.append('language', language);

  const res = await fetch(`${API_BASE}/api/voices`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail);
  }
  return res.json();
}

export async function deleteVoice(voiceId: string): Promise<void> {
  await fetchJSON(`/api/voices/${voiceId}`, { method: 'DELETE' });
}

export function getVoiceSampleUrl(voiceId: string): string {
  return `${API_BASE}/api/voices/${voiceId}/sample`;
}

// ── TTS ──
export async function generateSpeech(request: TTSRequest): Promise<{ job_id: string }> {
  return fetchJSON('/api/tts', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export function streamJobProgress(
  jobId: string,
  onProgress: (data: JobProgress) => void,
  onError?: (error: string) => void
): () => void {
  const es = new EventSource(`${API_BASE}/api/tts/${jobId}/progress`);

  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as JobProgress;
      onProgress(data);
      if (data.status === 'completed' || data.status === 'failed') {
        es.close();
      }
    } catch {}
  };

  es.onerror = () => {
    onError?.('Connection lost');
    es.close();
  };

  return () => es.close();
}

export async function getJobStatus(jobId: string): Promise<JobProgress> {
  return fetchJSON<JobProgress>(`/api/tts/${jobId}`);
}

// ── History ──
export async function getHistory(): Promise<HistoryEntry[]> {
  const data = await fetchJSON<{ history: HistoryEntry[] }>('/api/history');
  return data.history;
}

export async function getHistoryStats(): Promise<HistoryStats> {
  return fetchJSON<HistoryStats>('/api/history/stats');
}

export async function deleteHistory(outputId: string): Promise<void> {
  await fetchJSON(`/api/history/${outputId}`, { method: 'DELETE' });
}

// ── Audio ──
export function getAudioUrl(outputId: string, format: string = 'wav'): string {
  return `${API_BASE}/api/audio/${outputId}?format=${format}`;
}

export function getAudioDownloadUrl(outputId: string, format: string = 'wav'): string {
  return `${API_BASE}/api/audio/${outputId}/download?format=${format}`;
}
