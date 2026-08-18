import { useState, useEffect } from 'react';
import {
  Zap,
  Cpu,
  HardDrive,
  Activity,
  Box,
  Mic2,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  MemoryStick,
  MonitorSpeaker,
  Thermometer,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getSystemInfo, getModels, getHistoryStats } from '../services/api';
import type { SystemInfo, ModelInfo, HistoryStats } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const onNavigate = (path: string) => navigate(path === 'tts' ? '/tts' : `/${path}`);
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [sys, mods, st] = await Promise.all([
        getSystemInfo(),
        getModels(),
        getHistoryStats(),
      ]);
      setSystem(sys);
      setModels(mods);
      setStats(st);
    } catch {
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const installedModels = models.filter((m) => m.status === 'installed').length;

  if (loading) {
    return (
      <div className="animate-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ width: 40, height: 40, margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--text-muted)' }}>Detecting hardware & loading system info...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in">
      {/* Hero */}
      <div className="hero-banner">
        <div>
          <div className="hero-title">Local AI Voice Studio</div>
          <div className="hero-subtitle">
            Multilingual Text-to-Speech & Zero-Shot Voice Cloning — 100% Private & Local
          </div>
        </div>
        <button
          className="btn btn-primary btn-lg"
          onClick={() => onNavigate('tts')}
          style={{ whiteSpace: 'nowrap' }}
        >
          <Sparkles size={18} />
          Create Voice
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Top Stats */}
      <div className="card-grid" style={{ marginBottom: 24 }}>
        <div className="card stat-card">
          <div className="stat-icon purple"><Activity size={24} /></div>
          <div>
            <div className="stat-value">{stats?.generated_count ?? 0}</div>
            <div className="stat-label">Audio Generations</div>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon green"><Clock size={24} /></div>
          <div>
            <div className="stat-value">{stats?.total_duration_formatted ?? '0h 0m'}</div>
            <div className="stat-label">Total Audio Generated</div>
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
        {/* System Status & Hardware Detection */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity size={20} color="var(--accent-secondary)" />
              Hardware Detection & VRAM
            </h2>
            <button
              className="btn btn-ghost btn-sm"
              onClick={handleRefresh}
              disabled={refreshing}
              title="Refresh hardware stats"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>

          {system && (
            <div>
              <SysRow icon={<Cpu size={16} />} label="CPU" value={system.cpu.name} />
              
              {/* RAM */}
              <div style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <MemoryStick size={16} /> System RAM
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>
                    {system.ram.available_gb} GB free / {system.ram.total_gb} GB total ({system.ram.used_percent}% used)
                  </span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${system.ram.used_percent}%`, background: 'var(--accent-secondary)', borderRadius: 3 }} />
                </div>
              </div>

              {/* GPU & VRAM */}
              <SysRow
                icon={<MonitorSpeaker size={16} />}
                label="GPU Device"
                value={system.gpu.detected ? system.gpu.name : 'Not detected'}
              />

              {system.gpu.detected && (
                <div style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <HardDrive size={16} /> GPU VRAM
                    </span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-secondary)' }}>
                      {system.gpu.vram_free_gb} GB free / {system.gpu.vram_total_gb} GB total
                      {system.gpu.vram_used_percent !== undefined && ` (${system.gpu.vram_used_percent}% used)`}
                    </span>
                  </div>
                  <div style={{ height: 8, background: 'rgba(255,255,255,0.08)', borderRadius: 4, overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${system.gpu.vram_used_percent || 20}%`,
                        background: 'linear-gradient(90deg, #10b981, #f59e0b, #ef4444)',
                        borderRadius: 4,
                      }}
                    />
                  </div>
                </div>
              )}

              {system.gpu.temperature_c ? (
                <SysRow
                  icon={<Thermometer size={16} />}
                  label="GPU Temperature"
                  value={`${system.gpu.temperature_c} °C`}
                />
              ) : null}

              {system.gpu.driver_version && system.gpu.driver_version !== 'N/A' && (
                <SysRow label="NVIDIA Driver" value={system.gpu.driver_version} />
              )}

              <SysRow
                label="CUDA Acceleration"
                value={system.cuda.available ? `v${system.cuda.version} (Capability ${system.cuda.compute_capability})` : 'Not available'}
                badge={system.cuda.available}
              />
              <SysRow label="PyTorch Engine" value={system.pytorch_version} />
              <SysRow label="Python Environment" value={system.python_version} />
              <SysRow label="Disk Storage" value={`${system.disk.free_gb} GB free / ${system.disk.total_gb} GB`} />

              <div style={{
                marginTop: 16,
                padding: '12px 16px',
                background: 'var(--accent-glow)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Zap size={18} color="var(--accent-secondary)" />
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--accent-secondary)' }}>
                    Compute Device: {system.recommended_device.toUpperCase()}
                  </span>
                </div>
                <span className="badge badge-purple" style={{ textTransform: 'uppercase' }}>
                  {system.recommended_model_tier}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Model & Engine Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Active TTS Engine</h2>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('models')}>
              Manage Models
            </button>
          </div>

          <div style={{
            padding: 16,
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 16,
            border: '1px solid var(--border)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
                🎙 OmniVoice 0.2.1
              </div>
              <span className="badge badge-success">Active & Ready</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
              Massively multilingual diffusion-based zero-shot voice synthesis engine by <strong>k2-fsa</strong>.
              Supports <strong>600+ languages</strong>, zero-shot voice cloning from audio samples, and natural language voice design.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Supported Languages</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>600+ (EN, VI, JA, etc.)</div>
            </div>
            <div style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Voice Cloning</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#10b981', marginTop: 2 }}>Zero-Shot Ready</div>
            </div>
            <div style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Sample Rate</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>24,000 Hz Studio</div>
            </div>
            <div style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Inference Speed</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8', marginTop: 2 }}>RTF ~0.025 (40x RT)</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onNavigate('tts')}>
              <Sparkles size={16} /> Open Voice Studio
            </button>
            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => onNavigate('voices')}>
              <Mic2 size={16} /> Clone New Voice
            </button>
          </div>
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
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 0',
        borderBottom: '1px solid var(--border)',
        fontSize: 13,
      }}
    >
      <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
        {icon}
        {label}
      </span>
      {badge !== undefined ? (
        <span className={`badge ${badge ? 'badge-success' : 'badge-danger'}`}>{value}</span>
      ) : (
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{value}</span>
      )}
    </div>
  );
}
