import { useState } from 'react';
import { Settings as SettingsIcon, Save, RotateCcw } from 'lucide-react';

export default function Settings() {
  const [defaultLang, setDefaultLang] = useState('en');
  const [defaultFormat, setDefaultFormat] = useState('wav');
  const [autoDownload, setAutoDownload] = useState(true);
  const [autoSelect, setAutoSelect] = useState(true);
  const [saved, setSaved] = useState(false);

  function handleSave() {
    // Settings are stored in config.yaml on the backend
    // For now, this UI shows the concept
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function handleReset() {
    setDefaultLang('en');
    setDefaultFormat('wav');
    setAutoDownload(true);
    setAutoSelect(true);
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configure application preferences</p>
      </div>

      <div style={{ maxWidth: 640 }}>
        {/* TTS Settings */}
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 className="card-title" style={{ marginBottom: 20 }}>Text to Speech</h3>
          <div className="form-group">
            <label className="form-label">Default Language</label>
            <select className="form-select" value={defaultLang} onChange={(e) => setDefaultLang(e.target.value)}>
              <option value="en">🇺🇸 English</option>
              <option value="vi">🇻🇳 Vietnamese</option>
              <option value="ja">🇯🇵 Japanese</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Default Output Format</label>
            <select className="form-select" value={defaultFormat} onChange={(e) => setDefaultFormat(e.target.value)}>
              <option value="wav">WAV (Lossless)</option>
              <option value="mp3">MP3 (Compressed)</option>
            </select>
          </div>
        </div>

        {/* Model Settings */}
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 className="card-title" style={{ marginBottom: 20 }}>Models</h3>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoDownload}
                onChange={(e) => setAutoDownload(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--accent-primary)' }}
              />
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>Auto-download models</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Automatically download recommended models when needed
                </div>
              </div>
            </label>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoSelect}
                onChange={(e) => setAutoSelect(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--accent-primary)' }}
              />
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>Auto-select best model</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Automatically choose the optimal model based on your hardware
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Privacy */}
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 className="card-title" style={{ marginBottom: 12 }}>Privacy & Security</h3>
          <div className="alert alert-success" style={{ margin: 0 }}>
            <SettingsIcon size={16} />
            <div>
              <strong>All data stays local</strong>
              <p style={{ fontSize: 12, marginTop: 4 }}>
                Voice samples, embeddings, and generated audio are processed and stored
                entirely on your machine. Nothing is uploaded to external servers.
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-primary" onClick={handleSave}>
            <Save size={16} /> Save Settings
          </button>
          <button className="btn btn-secondary" onClick={handleReset}>
            <RotateCcw size={16} /> Reset Defaults
          </button>
          {saved && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--success)', fontSize: 14 }}>
              ✓ Settings saved
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
