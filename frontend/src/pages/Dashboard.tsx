import { useEffect, useState } from 'react';
import {
  Cpu,
  MemoryStick,
  MonitorSpeaker,
  Mic2,
  Clock,
  Box,
  AudioWaveform,
  Zap,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { getSystemInfo, getHistoryStats, getModels } from '../services/api';
import type { SystemInfo, HistoryStats, ModelInfo } from '../types';

export default function Dashboard() {
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [sys, st, mdls] = await Promise.all([
          getSystemInfo(),
          getHistoryStats().catch(() => null),
          getModels().catch(() => []),
        ]);
        setSystem(sys);
        setStats(st);
        setModels(mdls);
      } catch (e: any) {
        setError(e.message || 'Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="animate-in">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Detecting system hardware...</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-muted)' }}>
          <div className="spinner" /> Loading system information...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="animate-in">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
        </div>
        <div className="alert alert-error">
          <XCircle size={20} />
          <div>
            <strong>Backend Connection Error</strong>
            <p style={{ marginTop: 4, fontSize: 13 }}>{error}</p>
            <p style={{ marginTop: 8, fontSize: 13, color: 'var(--text-muted)' }}>
              Make sure the backend is running: <code>python -m uvicorn backend.app:app</code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const installedModels = models.filter((m) => m.status === 'installed').length;

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">System overview and AI model status</p>
      </div>

      {/* Stats Row */}
      <div className="card-grid" style={{ marginBottom: 24 }}>
        <div className="card stat-card">
          <div className="stat-icon purple"><AudioWaveform size={24} /></div>
          <div>
            <div className="stat-value">{stats?.generated_count ?? 0}</div>
            <div className="stat-label">Generated Voices</div>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon green"><Clock size={24} /></div>
          <div>
            <div className="stat-value">{stats?.total_duration_formatted ?? '0h 0m'}</div>
            <div className="stat-label">Total Audio</div>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon blue"><Box size={24} /></div>
          <div>
            <div className="stat-value">{installedModels}</div>
            <div className="stat-label">Installed Models</div>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon amber"><Mic2 size={24} /></div>
          <div>
            <div className="stat-value">{stats?.voice_profiles_count ?? 0}</div>
            <div className="stat-label">Voice Profiles</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* System Status */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">System Status</h2>
            <span className="badge badge-success">
              <Zap size={12} style={{ marginRight: 4 }} /> Online
            </span>
          </div>
          {system && (
            <div>
              <SysRow icon={<Cpu size={16} />} label="CPU" value={system.cpu.name} />
              <SysRow icon={<MemoryStick size={16} />} label="RAM" value={`${system.ram.total_gb} GB`} />
              <SysRow
                icon={<MonitorSpeaker size={16} />}
                label="GPU"
                value={system.gpu.detected ? system.gpu.name : 'Not detected'}
              />
              {system.gpu.detected && (
                <SysRow label="VRAM" value={`${system.gpu.vram_total_gb} GB`} />
              )}
              <SysRow
                label="CUDA"
                value={system.cuda.available ? `v${system.cuda.version}` : 'Not available'}
                badge={system.cuda.available}
              />
              <SysRow label="PyTorch" value={system.pytorch_version} />
              <SysRow label="Python" value={system.python_version} />
              <SysRow label="Disk Free" value={`${system.disk.free_gb} GB`} />
              <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--accent-glow)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Zap size={16} color="var(--accent-secondary)" />
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-secondary)' }}>
                  Recommended Device: {system.recommended_device.toUpperCase()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Recommended Models */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recommended Models</h2>
          </div>
          {system && (
            <div>
              {(['en', 'vi', 'ja'] as const).map((lang) => {
                const rec = system.recommended_models[lang];
                const langName = { en: 'English', vi: 'Vietnamese', ja: 'Japanese' }[lang];
                const installed = rec ? models.find((m) => m.id === rec.id)?.status === 'installed' : false;
                return (
                  <div
                    key={lang}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '14px 0',
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>
                        {langName}
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                        {rec ? rec.name : 'No model available'}
                      </div>
                    </div>
                    {rec && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {rec.voice_cloning && (
                          <span className="badge badge-purple" style={{ fontSize: 10 }}>
                            Cloning
                          </span>
                        )}
                        {installed ? (
                          <CheckCircle2 size={18} color="var(--success)" />
                        ) : (
                          <span className="badge badge-warning">Not Installed</span>
                        )}
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

function SysRow({
  icon,
  label,
  value,
  badge,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  badge?: boolean;
}) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '10px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 13 }}>
        {icon}
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
          {value}
        </span>
        {badge !== undefined && (
          <span className={`badge ${badge ? 'badge-success' : 'badge-warning'}`}>
            {badge ? '✓' : '✗'}
          </span>
        )}
      </div>
    </div>
  );
}
