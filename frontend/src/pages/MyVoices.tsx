import { useState, useEffect, useRef } from 'react';
import { Mic2, Upload, Trash2, Play, Plus, AlertCircle } from 'lucide-react';
import { getVoices, uploadVoice, deleteVoice, getVoiceSampleUrl } from '../services/api';
import type { VoiceProfile, AudioAnalysis } from '../types';

const LANG_NAMES: Record<string, string> = { en: 'English', vi: 'Vietnamese', ja: 'Japanese' };

export default function MyVoices() {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadLang, setUploadLang] = useState('en');
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadVoices();
  }, []);

  async function loadVoices() {
    try {
      const v = await getVoices();
      setVoices(v);
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file || !uploadName.trim()) return;

    setUploading(true);
    setError('');
    setAnalysis(null);

    try {
      const result = await uploadVoice(file, uploadName.trim(), uploadLang);
      setAnalysis(result.analysis);
      setVoices((prev) => [...prev, result.profile]);
      setUploadName('');
      if (fileRef.current) fileRef.current.value = '';
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this voice profile?')) return;
    try {
      await deleteVoice(id);
      setVoices((prev) => prev.filter((v) => v.id !== id));
    } catch {}
  }

  const qualityColor = (q: string) =>
    q === 'Excellent' ? 'var(--success)' :
    q === 'Good' ? 'var(--info)' :
    q === 'Fair' ? 'var(--warning)' : 'var(--error)';

  return (
    <div className="animate-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">My Voices</h1>
          <p className="page-subtitle">Upload voice samples to create custom voice profiles</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(!showUpload)}>
          <Plus size={16} /> Upload Voice
        </button>
      </div>

      {/* Upload Panel */}
      {showUpload && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 className="card-title" style={{ marginBottom: 16 }}>Upload Voice Sample</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 16, alignItems: 'end' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Voice Name</label>
              <input
                className="form-input"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                placeholder="e.g., My Japanese Voice"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Language</label>
              <select className="form-select" value={uploadLang} onChange={(e) => setUploadLang(e.target.value)}>
                <option value="en">🇺🇸 English</option>
                <option value="vi">🇻🇳 Vietnamese</option>
                <option value="ja">🇯🇵 Japanese</option>
              </select>
            </div>
            <div>
              <input
                type="file"
                ref={fileRef}
                accept=".wav,.mp3,.m4a,.flac"
                style={{ display: 'none' }}
                onChange={() => {}}
              />
              <button className="btn btn-secondary" onClick={() => fileRef.current?.click()}>
                <Upload size={16} /> Choose File
              </button>
            </div>
          </div>
          {fileRef.current?.files?.[0] && (
            <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-muted)' }}>
              Selected: {fileRef.current.files[0].name}
            </div>
          )}
          <button
            className="btn btn-primary"
            style={{ marginTop: 16 }}
            onClick={handleUpload}
            disabled={uploading || !uploadName.trim()}
          >
            {uploading ? (
              <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Uploading...</>
            ) : (
              <><Upload size={16} /> Upload & Analyze</>
            )}
          </button>
          {error && <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>}
          {analysis && (
            <div style={{ marginTop: 16, padding: 16, background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)' }}>
              <h4 style={{ fontSize: 14, marginBottom: 12, color: 'var(--text-primary)' }}>Voice Sample Analysis</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, fontSize: 13 }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Duration:</span> {analysis.duration_seconds}s</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Sample Rate:</span> {(analysis.sample_rate / 1000).toFixed(1)} kHz</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Channels:</span> {analysis.channels === 1 ? 'Mono' : 'Stereo'}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Noise:</span> {analysis.noise_level}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Clipping:</span> {analysis.clipping_detected ? 'Detected' : 'None'}</div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Quality: </span>
                  <span style={{ fontWeight: 600, color: qualityColor(analysis.quality) }}>{analysis.quality}</span>
                </div>
              </div>
              {analysis.warnings.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  {analysis.warnings.map((w, i) => (
                    <div key={i} className="alert alert-warning" style={{ margin: '4px 0', padding: '8px 12px', fontSize: 12 }}>
                      <AlertCircle size={14} /> {w}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Voice Cards */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="spinner" /> Loading voices...
        </div>
      ) : voices.length === 0 ? (
        <div className="empty-state">
          <Mic2 size={48} />
          <h3>No Voice Profiles Yet</h3>
          <p>Upload a voice sample to create your first voice profile</p>
        </div>
      ) : (
        <div className="card-grid">
          {voices.map((v) => (
            <div key={v.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-md)',
                  background: 'var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Mic2 size={20} color="var(--accent-secondary)" />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{v.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {LANG_NAMES[v.language] || v.language}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                <div>{v.duration_seconds}s • {(v.sample_rate / 1000).toFixed(1)} kHz</div>
                <div>
                  Quality: <span style={{ color: qualityColor(v.quality), fontWeight: 600 }}>{v.quality}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                <a href={getVoiceSampleUrl(v.id)} target="_blank" className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
                  <Play size={14} /> Preview
                </a>
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(v.id)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
