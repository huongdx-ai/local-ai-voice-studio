import { useState, useEffect, useRef } from 'react';
import { Mic2, Upload, Trash2, Play, Plus, AlertCircle, Sparkles, CheckCircle2, Square, Mic } from 'lucide-react';
import { getVoices, uploadVoice, deleteVoice, getVoiceSampleUrl } from '../services/api';
import type { VoiceProfile, AudioAnalysis } from '../types';

const LANG_NAMES: Record<string, string> = {
  en: '🇺🇸 English',
  vi: '🇻🇳 Vietnamese',
  ja: '🇯🇵 Japanese',
  zh: '🇨🇳 Mandarin',
  ko: '🇰🇷 Korean',
  fr: '🇫🇷 French',
  de: '🇩🇪 German',
  es: '🇪🇸 Spanish',
};

export default function MyVoices() {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadLang, setUploadLang] = useState('vi');
  const [refText, setRefText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [error, setError] = useState('');

  // Microphone recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);

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

  // ── Recording handlers ──
  const startRecording = async () => {
    setError('');
    setRecordedBlob(null);
    setSelectedFile(null);
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setRecordedBlob(audioBlob);
        const recordedFile = new File([audioBlob], `recorded_${Date.now()}.wav`, { type: 'audio/wav' });
        setSelectedFile(recordedFile);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(100);
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (e: any) {
      setError(`Microphone access failed: ${e.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0]);
      setRecordedBlob(null);
      if (!uploadName) {
        setUploadName(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  async function handleUpload() {
    if (!selectedFile || !uploadName.trim()) {
      setError('Please provide a voice name and select an audio sample.');
      return;
    }

    setUploading(true);
    setError('');
    setAnalysis(null);

    try {
      const result = await uploadVoice(
        selectedFile,
        uploadName.trim(),
        uploadLang,
        refText.trim() || undefined
      );
      setAnalysis(result.analysis);
      setVoices((prev) => [result.profile, ...prev.filter((v) => v.id !== result.profile.id)]);
      setUploadName('');
      setRefText('');
      setSelectedFile(null);
      setRecordedBlob(null);
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
          <p className="page-subtitle">
            Upload or record 3-10s voice samples for instant zero-shot cloning with OmniVoice
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(!showUpload)}>
          <Plus size={16} /> {showUpload ? 'Close' : 'Add Voice Sample'}
        </button>
      </div>

      {/* Upload & Record Panel */}
      {showUpload && (
        <div className="card" style={{ marginBottom: 24, border: '1px solid var(--accent-primary)' }}>
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={18} color="var(--accent-secondary)" />
              Clone New Voice (Zero-Shot)
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Voice Name *</label>
              <input
                className="form-input"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                placeholder="e.g. Anh Nam - Giọng đọc truyền cảm"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Language</label>
              <select className="form-select" value={uploadLang} onChange={(e) => setUploadLang(e.target.value)}>
                {Object.entries(LANG_NAMES).map(([code, label]) => (
                  <option key={code} value={code}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Reference text transcript (optional for higher accuracy) */}
          <div className="form-group" style={{ marginBottom: 16 }}>
            <label className="form-label">
              Reference Audio Transcript (Optional - Helps OmniVoice achieve higher fidelity)
            </label>
            <input
              className="form-input"
              value={refText}
              onChange={(e) => setRefText(e.target.value)}
              placeholder="Enter exact words spoken in the audio clip if known..."
            />
          </div>

          {/* Audio Input Options: File Upload or Record */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* File Upload Box */}
            <div
              style={{
                border: '2px dashed var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 20,
                textAlign: 'center',
                background: 'var(--bg-tertiary)',
                cursor: 'pointer',
              }}
              onClick={() => fileRef.current?.click()}
            >
              <input
                type="file"
                ref={fileRef}
                accept=".wav,.mp3,.m4a,.flac,.ogg,.webm,.aac"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <Upload size={24} color="var(--accent-secondary)" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontWeight: 600, fontSize: 14 }}>Upload Audio File</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Supports WAV, MP3, M4A, FLAC, OGG, WebM (3-15s recommended)
              </div>
            </div>

            {/* Microphone Record Box */}
            <div
              style={{
                border: `2px dashed ${isRecording ? '#ef4444' : 'var(--border)'}`,
                borderRadius: 'var(--radius-md)',
                padding: 20,
                textAlign: 'center',
                background: isRecording ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-tertiary)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isRecording ? (
                <div>
                  <div style={{ color: '#ef4444', fontWeight: 700, fontSize: 16, marginBottom: 8 }}>
                    ● Recording: {recordingSeconds}s
                  </div>
                  <button className="btn btn-danger btn-sm" onClick={stopRecording}>
                    <Square size={14} /> Stop Recording
                  </button>
                </div>
              ) : (
                <div>
                  <Mic size={24} color="var(--accent-secondary)" style={{ margin: '0 auto 8px' }} />
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>Record From Mic</div>
                  <button className="btn btn-secondary btn-sm" onClick={startRecording}>
                    <Mic size={14} /> Start Record (5-10s)
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Selected File / Recorded Audio Indicator */}
          {selectedFile && (
            <div style={{
              padding: '10px 14px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 13,
              color: '#10b981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
            }}>
              <span>✓ Selected Audio: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              {recordedBlob && (
                <audio controls src={URL.createObjectURL(recordedBlob)} style={{ height: 28 }} />
              )}
            </div>
          )}

          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%' }}
            onClick={handleUpload}
            disabled={uploading || !uploadName.trim() || !selectedFile}
          >
            {uploading ? (
              <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Processing & Extracting VoiceClonePrompt...</>
            ) : (
              <><Sparkles size={18} /> Process & Save Voice Profile</>
            )}
          </button>

          {error && <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>}

          {/* Audio Quality Analysis Result */}
          {analysis && (
            <div style={{ marginTop: 16, padding: 16, background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h4 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>✓ Voice Sample Analyzed & Cached</h4>
                <span className="badge badge-success">Prompt Extracted</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, fontSize: 13 }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Duration:</span> {analysis.duration_seconds}s</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Sample Rate:</span> {(analysis.sample_rate / 1000).toFixed(1)} kHz</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Channels:</span> {analysis.channels === 1 ? 'Mono' : 'Stereo'}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Noise Level:</span> {analysis.noise_level}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Clipping:</span> {analysis.clipping_detected ? 'Detected' : 'None'}</div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Quality Rating: </span>
                  <span style={{ fontWeight: 700, color: qualityColor(analysis.quality) }}>{analysis.quality}</span>
                </div>
              </div>
              {analysis.warnings.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  {analysis.warnings.map((w, i) => (
                    <div key={i} className="alert alert-warning" style={{ margin: '4px 0', padding: '6px 10px', fontSize: 12 }}>
                      <AlertCircle size={14} /> {w}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Voice Profiles Grid */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="spinner" /> Loading voice profiles...
        </div>
      ) : voices.length === 0 ? (
        <div className="empty-state">
          <Mic2 size={48} />
          <h3>No Voice Profiles Yet</h3>
          <p>Upload or record a 3-10 second clean audio clip to clone your first voice</p>
        </div>
      ) : (
        <div className="card-grid">
          {voices.map((v) => (
            <div key={v.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 'var(--radius-md)',
                    background: 'var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Mic2 size={22} color="var(--accent-secondary)" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{v.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {LANG_NAMES[v.language] || v.language}
                    </div>
                  </div>
                </div>
                <span className="badge badge-purple" style={{ fontSize: 11 }}>
                  <CheckCircle2 size={11} style={{ marginRight: 3 }} /> Zero-Shot
                </span>
              </div>

              {v.ref_text && (
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic', margin: 0, lineHeight: 1.4 }}>
                  "{v.ref_text}"
                </p>
              )}

              <div style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                <span>{v.duration_seconds}s • 24.0 kHz</span>
                <span>
                  Quality: <strong style={{ color: qualityColor(v.quality) }}>{v.quality}</strong>
                </span>
              </div>

              <div style={{ marginTop: 'auto', paddingTop: 8 }}>
                <audio controls src={getVoiceSampleUrl(v.id)} style={{ width: '100%', height: 32, marginBottom: 8 }} />
                <div style={{ display: 'flex', gap: 8 }}>
                  <a href={getVoiceSampleUrl(v.id)} download={`voice_${v.id}.wav`} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
                    <Play size={14} /> Download Sample
                  </a>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(v.id)} title="Delete Voice">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
