import { useState, useEffect } from 'react';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { generateSpeech, streamJobProgress, getVoices } from '../services/api';
import { getAudioUrl, getAudioDownloadUrl } from '../services/api';
import AudioPlayer from '../components/AudioPlayer';
import ProgressBar from '../components/ProgressBar';
import type { VoiceProfile, JobProgress } from '../types';

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'vi', name: 'Vietnamese', flag: '🇻🇳' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
];

const SAMPLE_TEXTS: Record<string, string> = {
  en: 'Hello. Today is a beautiful day. I am learning Japanese and I want to improve my listening skills.',
  vi: 'Xin chào. Hôm nay là một ngày rất đẹp. Tôi đang học tiếng Nhật và muốn cải thiện khả năng nghe của mình.',
  ja: 'こんにちは。今日はとてもいい天気ですね。これから日本語の勉強を始めたいと思います。',
};

export default function TextToVoice() {
  const [language, setLanguage] = useState('en');
  const [text, setText] = useState(SAMPLE_TEXTS['en']);
  const [voiceId, setVoiceId] = useState<string>('');
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [volume, setVolume] = useState(1.0);
  const [format, setFormat] = useState('wav');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [result, setResult] = useState<JobProgress['result'] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getVoices().then(setVoices).catch(() => {});
  }, []);

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (!text || text === SAMPLE_TEXTS[language]) {
      setText(SAMPLE_TEXTS[lang] || '');
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setGenerating(true);
    setProgress(null);
    setResult(null);
    setError('');

    try {
      const { job_id } = await generateSpeech({
        text: text.trim(),
        language,
        voice_id: voiceId || undefined,
        speed,
        pitch,
        volume,
        output_format: format,
      });

      streamJobProgress(
        job_id,
        (data) => {
          setProgress(data);
          if (data.status === 'completed' && data.result) {
            setResult(data.result);
            setGenerating(false);
          }
          if (data.status === 'failed') {
            setError(data.error || 'Generation failed');
            setGenerating(false);
          }
        },
        (err) => {
          setError(err);
          setGenerating(false);
        }
      );
    } catch (e: any) {
      setError(e.message);
      setGenerating(false);
    }
  };

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Text to Voice</h1>
        <p className="page-subtitle">Generate natural speech from text using AI</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24, alignItems: 'start' }}>
        {/* Main Form */}
        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            {/* Language & Voice */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Language</label>
                <select
                  className="form-select"
                  value={language}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.flag} {l.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Voice</label>
                <select
                  className="form-select"
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                >
                  <option value="">Default Voice</option>
                  {voices
                    .filter((v) => v.language === language || !voiceId)
                    .map((v) => (
                      <option key={v.id} value={v.id}>
                        🎙 {v.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {/* Text Input */}
            <div className="form-group">
              <label className="form-label">Text</label>
              <textarea
                className="form-textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text to convert to speech..."
                rows={6}
                maxLength={5000}
              />
              <div className="char-count">
                {text.length} / 5,000 characters
              </div>
            </div>

            {/* Advanced Settings Toggle */}
            <button
              className="btn btn-secondary"
              onClick={() => setShowAdvanced(!showAdvanced)}
              style={{ marginBottom: showAdvanced ? 16 : 0, width: '100%' }}
            >
              {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              Advanced Settings
            </button>

            {showAdvanced && (
              <div style={{ padding: '16px 0' }}>
                <div className="form-group">
                  <label className="form-label">Speed</label>
                  <div className="slider-container">
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>0.5x</span>
                    <input
                      type="range"
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      value={speed}
                      onChange={(e) => setSpeed(parseFloat(e.target.value))}
                    />
                    <span className="slider-value">{speed.toFixed(1)}x</span>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Pitch</label>
                  <div className="slider-container">
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>-12</span>
                    <input
                      type="range"
                      min={-12}
                      max={12}
                      step={1}
                      value={pitch}
                      onChange={(e) => setPitch(parseFloat(e.target.value))}
                    />
                    <span className="slider-value">{pitch > 0 ? '+' : ''}{pitch}</span>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Volume</label>
                  <div className="slider-container">
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>0%</span>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={volume}
                      onChange={(e) => setVolume(parseFloat(e.target.value))}
                    />
                    <span className="slider-value">{Math.round(volume * 100)}%</span>
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Format</label>
                    <select className="form-select" value={format} onChange={(e) => setFormat(e.target.value)}>
                      <option value="wav">WAV</option>
                      <option value="mp3">MP3</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Generate Button */}
          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%' }}
            onClick={handleGenerate}
            disabled={generating || !text.trim()}
          >
            {generating ? (
              <>
                <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Generate Voice
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="alert alert-error" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}
        </div>

        {/* Right Panel: Progress + Result */}
        <div>
          {/* Progress */}
          {generating && progress && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h3 className="card-title" style={{ marginBottom: 16 }}>Generating...</h3>
              <ProgressBar
                progress={progress.progress}
                stage={progress.stage}
                message={progress.message}
              />
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: 16 }}>Generated Audio</h3>
              <div style={{ marginBottom: 12 }}>
                <span className="badge badge-success" style={{ marginRight: 8 }}>
                  {result.language.toUpperCase()}
                </span>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  {result.duration_seconds}s • {result.model}
                </span>
              </div>
              <AudioPlayer
                wavUrl={getAudioUrl(result.output_id, 'wav')}
                mp3Url={getAudioUrl(result.output_id, 'mp3')}
                downloadWavUrl={getAudioDownloadUrl(result.output_id, 'wav')}
                downloadMp3Url={getAudioDownloadUrl(result.output_id, 'mp3')}
              />
            </div>
          )}

          {/* Tips */}
          {!generating && !result && (
            <div className="card" style={{ opacity: 0.7 }}>
              <h3 className="card-title" style={{ marginBottom: 12 }}>Tips</h3>
              <ul style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.8, paddingLeft: 16 }}>
                <li>Use 3-10 second voice samples for best cloning</li>
                <li>Keep text under 500 characters for fastest results</li>
                <li>GPU mode is 5-10x faster than CPU</li>
                <li>Clean audio samples produce better clones</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
