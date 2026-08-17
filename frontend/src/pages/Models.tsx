import { useState, useEffect } from 'react';
import { Box, Download, Trash2, CheckCircle2, Zap, HardDrive } from 'lucide-react';
import { getModels, downloadModel, deleteModel, activateModel } from '../services/api';
import ProgressBar from '../components/ProgressBar';
import type { ModelInfo, DownloadProgress } from '../types';

const LANG_NAMES: Record<string, string> = {
  en: 'English', vi: 'Vietnamese', ja: 'Japanese', multi: 'Multilingual',
};

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

  // Group models by language
  const groups: Record<string, ModelInfo[]> = {};
  models.forEach((m) => {
    const key = m.language === 'multi' ? 'multi' : m.language;
    if (!groups[key]) groups[key] = [];
    groups[key].push(m);
  });

  const groupOrder = ['multi', 'en', 'vi', 'ja'];

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
        groupOrder
          .filter((g) => groups[g])
          .map((groupKey) => (
            <div key={groupKey} style={{ marginBottom: 32 }}>
              <h2 style={{
                fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)',
                marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid var(--border)',
              }}>
                {LANG_NAMES[groupKey] || groupKey}
              </h2>
              <div className="card-grid">
                {groups[groupKey].map((model) => (
                  <div key={model.id} className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>{model.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {model.engine.toUpperCase()} Engine
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

                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
                      {model.description}
                    </p>

                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                      <div><HardDrive size={12} style={{ marginRight: 4 }} />{model.size_gb} GB</div>
                      <div>{model.cpu_supported ? '✓ CPU' : '✗ CPU'} / {model.cuda_supported ? '✓ GPU' : '✗ GPU'}</div>
                      <div>Quality: {'★'.repeat(Math.round(model.quality_score / 2))}</div>
                      <div>Speed: {'★'.repeat(Math.round(model.speed_score / 2))}</div>
                      {model.voice_cloning && (
                        <div style={{ gridColumn: 'span 2' }}>
                          <span className="badge badge-purple" style={{ fontSize: 10 }}>
                            <Zap size={10} style={{ marginRight: 2 }} /> Voice Cloning
                          </span>
                        </div>
                      )}
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
                          <Download size={14} /> Download
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
      )}
    </div>
  );
}
