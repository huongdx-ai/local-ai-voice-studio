import { useState, useEffect } from 'react';
import { Download, Trash2, CheckCircle2, Zap, HardDrive, Globe } from 'lucide-react';
import { getModels, downloadModel, deleteModel, activateModel } from '../services/api';
import ProgressBar from '../components/ProgressBar';
import type { ModelInfo, DownloadProgress } from '../types';

export default function Models() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<Record<string, DownloadProgress>>({});

  useEffect(() => {
    loadModels();
  }, []);

  async function loadModels() {
    try {
      setModels(await getModels());
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(modelId: string) {
    setDownloading((prev) => ({
      ...prev,
      [modelId]: { model_id: modelId, status: 'starting', progress: 0, progress_percent: 0, downloaded_mb: 0, total_mb: 0, message: 'Starting...' },
    }));

    await downloadModel(modelId, (data) => {
      setDownloading((prev) => ({ ...prev, [modelId]: data }));
      if (data.status === 'completed' || data.status === 'error') {
        setTimeout(() => {
          setDownloading((prev) => {
            const copy = { ...prev };
            delete copy[modelId];
            return copy;
          });
          loadModels();
        }, 2000);
      }
    });
  }

  async function handleDelete(modelId: string) {
    if (!confirm('Delete this model? You can re-download it later.')) return;
    try {
      await deleteModel(modelId);
      loadModels();
    } catch {}
  }

  async function handleActivate(modelId: string) {
    try {
      await activateModel(modelId);
      loadModels();
    } catch {}
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Models</h1>
        <p className="page-subtitle">Manage TTS and voice cloning models</p>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="spinner" /> Loading models...
        </div>
      ) : (
        <div className="card-grid">
          {models.map((model) => (
            <div key={model.id} className="card" style={{ position: 'relative', overflow: 'hidden' }}>
              {/* Gradient accent bar */}
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: 3,
                background: 'var(--accent-gradient)',
              }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, marginTop: 8 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Globe size={20} color="var(--accent-secondary)" />
                    {model.name}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {model.engine.toUpperCase()} Engine • k2-fsa
                  </div>
                </div>
                {model.status === 'installed' ? (
                  <span className="badge badge-success"><CheckCircle2 size={12} style={{ marginRight: 4 }} /> Installed</span>
                ) : model.status === 'downloading' ? (
                  <span className="badge badge-info animate-pulse">Downloading</span>
                ) : (
                  <span className="badge badge-warning">Not Installed</span>
                )}
              </div>

              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>
                {model.description}
              </p>

              {/* Feature badges */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                <span className="badge badge-purple" style={{ fontSize: 11 }}>
                  <Globe size={10} style={{ marginRight: 3 }} /> 600+ Languages
                </span>
                <span className="badge badge-purple" style={{ fontSize: 11 }}>
                  <Zap size={10} style={{ marginRight: 3 }} /> Voice Cloning
                </span>
                <span className="badge badge-info" style={{ fontSize: 11 }}>
                  EN • VI • JA
                </span>
                {model.cpu_supported && (
                  <span className="badge badge-success" style={{ fontSize: 11 }}>✓ CPU</span>
                )}
                {model.cuda_supported && (
                  <span className="badge badge-success" style={{ fontSize: 11 }}>✓ GPU</span>
                )}
              </div>

              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <HardDrive size={12} /> ~{model.size_gb} GB
                </div>
                <div>
                  Quality: {'★'.repeat(Math.min(5, Math.round(model.quality_score / 2)))}
                </div>
                <div>Min VRAM: {model.min_vram_gb} GB</div>
                <div>
                  Speed: {'★'.repeat(Math.min(5, Math.round(model.speed_score / 2)))}
                </div>
              </div>

              {/* Download progress */}
              {downloading[model.id] && (
                <div style={{ marginBottom: 12 }}>
                  <ProgressBar
                    progress={downloading[model.id].progress}
                    message={downloading[model.id].message}
                  />
                </div>
              )}

              <div style={{ display: 'flex', gap: 8 }}>
                {model.status === 'installed' ? (
                  <>
                    <button
                      className={`btn btn-sm ${model.is_active ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => handleActivate(model.id)}
                      style={{ flex: 1 }}
                    >
                      {model.is_active ? '✓ Active' : 'Use'}
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(model.id)}>
                      <Trash2 size={14} />
                    </button>
                  </>
                ) : (
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => handleDownload(model.id)}
                    disabled={!!downloading[model.id]}
                  >
                    <Download size={14} /> Install OmniVoice
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info card */}
      <div className="card" style={{ marginTop: 24 }}>
        <h3 className="card-title" style={{ marginBottom: 12 }}>About OmniVoice</h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          <strong>OmniVoice</strong> by <a href="https://huggingface.co/k2-fsa/OmniVoice" target="_blank" style={{ color: 'var(--accent-secondary)' }}>k2-fsa</a> is
          a massively multilingual zero-shot TTS model supporting <strong>600+ languages</strong> including
          English, Vietnamese, Japanese, Chinese, Korean, French, German, and many more.
          It uses Diffusion Language Models for high-quality synthesis with an RTF as low as 0.025 (40x faster than real-time).
          Features include zero-shot voice cloning from 3-10 second audio samples and voice design via natural language descriptions.
        </p>
      </div>
    </div>
  );
}
