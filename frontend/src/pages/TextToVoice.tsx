import { useState, useEffect } from 'react';
import { Sparkles, ChevronDown, ChevronUp, Globe, Wand2, Sliders, Volume2, Check } from 'lucide-react';
import { generateSpeech, streamJobProgress, getVoices } from '../services/api';
import { getAudioUrl, getAudioDownloadUrl } from '../services/api';
import AudioPlayer from '../components/AudioPlayer';
import ProgressBar from '../components/ProgressBar';
import type { VoiceProfile, JobProgress } from '../types';

const LANGUAGES = [
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
];

const SAMPLE_TEXTS: Record<string, string> = {
  vi: 'Xin chào! Chào mừng bạn đến với Local AI Voice Studio. Hôm nay là một ngày tuyệt vời để sáng tạo âm thanh!',
  en: 'Hello! Welcome to Local AI Voice Studio. Today is a great day to create amazing voiceovers with artificial intelligence!',
  ja: 'こんにちは！Local AI Voice Studioへようこそ。今日は人工知能で素晴らしい音声を生成するのに最適な日です！',
  zh: '你好！欢迎使用本地人工智能语音工作室。今天是用人工智能创造美妙声音的绝佳日子！',
  ko: '안녕하세요! Local AI Voice Studio에 오신 것을 환영합니다. 인공지능으로 멋진 음성을 생성해 보세요!',
};

const VOICE_PRESETS = [
  { id: '', label: '✨ Mặc định (Tự nhiên theo ngôn ngữ)', prompt: '' },
  { id: 'female_young', label: '👩 Nữ - Trẻ trung, tự nhiên (Female, Young Adult)', prompt: 'female, young adult, moderate pitch' },
  { id: 'male_low', label: '👨 Nam - Trầm ấm, phát thanh viên (Male, Low Pitch)', prompt: 'male, low pitch' },
  { id: 'female_high', label: '🌸 Nữ - Dễ thương, trong trẻo (Female, High Pitch)', prompt: 'female, high pitch' },
  { id: 'male_whisper', label: '📖 Nam - Thì thầm, kể chuyện đêm muộn (Male, Whisper)', prompt: 'male, whisper' },
  { id: 'female_whisper', label: '🤫 Nữ - Thì thầm, dịu dàng (Female, Whisper)', prompt: 'female, whisper' },
  { id: 'female_teen', label: '⚡ Nữ - Năng động, thanh thiếu niên (Female, Teenager)', prompt: 'female, teenager, high pitch' },
  { id: 'male_mid', label: '🎙 Nam - Trung niên, đĩnh đạc (Male, Middle-aged)', prompt: 'male, middle-aged, moderate pitch' },
  { id: 'male_vlow', label: '🎬 Nam - Trầm sâu, kịch tính (Male, Very Low Pitch)', prompt: 'male, very low pitch' },
  { id: 'male_elderly', label: '👴 Nam - Lớn tuổi, điềm đạm (Male, Elderly)', prompt: 'male, elderly, low pitch' },
  { id: 'female_elderly', label: '👵 Nữ - Lớn tuổi, phúc hậu (Female, Elderly)', prompt: 'female, elderly, moderate pitch' },
  { id: 'child', label: '👶 Giọng trẻ em (Child)', prompt: 'child, high pitch' },
  { id: 'custom', label: '✍️ Tùy chỉnh từ khóa (female, male, low pitch, whisper, child...)', prompt: '' },
];

const EXPRESSION_TAGS = [
  { tag: '[laughter]', label: '😂 Laughter' },
  { tag: '[sigh]', label: '😮‍💨 Sigh' },
  { tag: '[gasp]', label: '😲 Gasp' },
  { tag: '[whisper]', label: '🤫 Whisper' },
  { tag: '[giggle]', label: '🤭 Giggle' },
  { tag: '[cough]', label: '😷 Cough' },
];

export default function TextToVoice() {
  const [language, setLanguage] = useState('vi');
  const [text, setText] = useState(SAMPLE_TEXTS['vi']);
  const [voiceId, setVoiceId] = useState<string>('');
  
  // Voice Design states
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [customInstruct, setCustomInstruct] = useState('');

  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [volume, setVolume] = useState(1.0);
  const [numStep, setNumStep] = useState(32);
  const [guidanceScale, setGuidanceScale] = useState(2.0);
  const [denoise, setDenoise] = useState(true);
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

  const handlePresetChange = (presetId: string) => {
    setSelectedPresetId(presetId);
    const preset = VOICE_PRESETS.find((p) => p.id === presetId);
    if (preset && preset.id !== 'custom') {
      setCustomInstruct(preset.prompt);
    }
  };

  const insertTag = (tag: string) => {
    setText((prev) => prev + (prev.endsWith(' ') || prev === '' ? '' : ' ') + tag + ' ');
  };

  // Get active instruction string
  const activeInstruct = selectedPresetId === 'custom' ? customInstruct : (VOICE_PRESETS.find((p) => p.id === selectedPresetId)?.prompt || '');

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
        instruct: activeInstruct.trim() || undefined,
        speed,
        pitch,
        volume,
        num_step: numStep,
        guidance_scale: guidanceScale,
        denoise,
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
        <h1 className="page-title">Text to Voice Studio</h1>
        <p className="page-subtitle">
          High-Fidelity Multilingual TTS, Zero-Shot Voice Cloning & Voice Design powered by OmniVoice 0.2.1
          <span style={{ marginLeft: 8 }} className="badge badge-purple">
            <Globe size={11} style={{ marginRight: 3 }} /> 600+ Languages
          </span>
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24, alignItems: 'start' }}>
        {/* Main Form */}
        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            {/* Language & Voice Selector */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Ngôn ngữ (Language)</label>
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
                <label className="form-label">Giọng Clone Mẫu (Tùy chọn)</label>
                <select
                  className="form-select"
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                >
                  <option value="">✨ Giọng AI Mặc định</option>
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      🎙 {v.name} ({v.language})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Voice Design Preset Selector (Predefined Styles) */}
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Wand2 size={15} color="var(--accent-secondary)" />
                Phong cách & Sắc thái giọng (Voice Design)
              </label>
              <select
                className="form-select"
                value={selectedPresetId}
                onChange={(e) => handlePresetChange(e.target.value)}
              >
                {VOICE_PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>

              {/* Show custom text box only if user explicitly selects Custom */}
              {selectedPresetId === 'custom' && (
                <input
                  className="form-input"
                  style={{ marginTop: 8 }}
                  value={customInstruct}
                  onChange={(e) => setCustomInstruct(e.target.value)}
                  placeholder="Nhập mô tả sắc thái giọng riêng (e.g. Nữ giọng truyền cảm sâu lắng, nam phát thanh viên trầm ấm...)"
                />
              )}

              {/* Show selected description preview if a preset is selected */}
              {selectedPresetId !== '' && selectedPresetId !== 'custom' && (
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--accent-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Check size={12} /> Áp dụng sắc thái: <em>"{activeInstruct}"</em>
                </div>
              )}
            </div>

            {/* Expressive Tags Bar */}
            <div style={{ marginBottom: 12 }}>
              <label className="form-label" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Chèn nhanh âm thanh cảm xúc:
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {EXPRESSION_TAGS.map((t) => (
                  <button
                    key={t.tag}
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: 11, padding: '4px 8px' }}
                    onClick={() => insertTag(t.tag)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Text Input */}
            <div className="form-group">
              <label className="form-label">Nội dung văn bản (Text)</label>
              <textarea
                className="form-textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Nhập văn bản cần chuyển thành giọng nói..."
                rows={6}
                maxLength={5000}
              />
              <div className="char-count">
                {text.length} / 5,000 ký tự
              </div>
            </div>

            {/* Advanced Settings Toggle */}
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowAdvanced(!showAdvanced)}
              style={{ marginBottom: showAdvanced ? 16 : 0, width: '100%', display: 'flex', justifyContent: 'space-between' }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Sliders size={15} /> Tùy chỉnh nâng cao (Tốc độ, Cao độ, Diffusion)
              </span>
              {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showAdvanced && (
              <div style={{ padding: '16px 0', borderTop: '1px solid var(--border)' }}>
                {/* Speed & Pitch */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 12 }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Tốc độ sinh âm (Speed): {speed.toFixed(1)}x</label>
                    <input
                      type="range"
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      value={speed}
                      onChange={(e) => setSpeed(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Độ cao (Pitch Shift): {pitch > 0 ? '+' : ''}{pitch}</label>
                    <input
                      type="range"
                      min={-12}
                      max={12}
                      step={1}
                      value={pitch}
                      onChange={(e) => setPitch(parseFloat(e.target.value))}
                    />
                  </div>
                </div>

                {/* Diffusion Steps & Guidance Scale */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 12 }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Diffusion Steps: {numStep}</label>
                    <input
                      type="range"
                      min={16}
                      max={64}
                      step={4}
                      value={numStep}
                      onChange={(e) => setNumStep(parseInt(e.target.value))}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Guidance Scale: {guidanceScale.toFixed(1)}</label>
                    <input
                      type="range"
                      min={1.0}
                      max={5.0}
                      step={0.2}
                      value={guidanceScale}
                      onChange={(e) => setGuidanceScale(parseFloat(e.target.value))}
                    />
                  </div>
                </div>

                {/* Volume & Format */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, alignItems: 'center' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Âm lượng: {Math.round(volume * 100)}%</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={volume}
                      onChange={(e) => setVolume(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Định dạng file</label>
                    <select className="form-select" value={format} onChange={(e) => setFormat(e.target.value)}>
                      <option value="wav">WAV (24kHz Lossless)</option>
                      <option value="mp3">MP3 (Compressed)</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: 8, paddingTop: 18 }}>
                    <input
                      type="checkbox"
                      id="denoiseCheck"
                      checked={denoise}
                      onChange={(e) => setDenoise(e.target.checked)}
                    />
                    <label htmlFor="denoiseCheck" style={{ fontSize: 13, cursor: 'pointer' }}>
                      Lọc nhiễu hậu kỳ (Denoise)
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Generate Action Button */}
          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%', height: 48, fontSize: 16 }}
            onClick={handleGenerate}
            disabled={generating || !text.trim()}
          >
            {generating ? (
              <>
                <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                Đang tạo giọng nói AI...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Tạo giọng nói ngay (Generate Voice)
              </>
            )}
          </button>

          {/* Error display */}
          {error && (
            <div className="alert alert-error" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}
        </div>

        {/* Right Panel: Progress & Audio Player */}
        <div>
          {/* Real-time SSE Progress */}
          {generating && progress && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h3 className="card-title" style={{ marginBottom: 16 }}>Tiến trình xử lý</h3>
              <ProgressBar
                progress={progress.progress}
                stage={progress.stage}
                message={progress.message}
              />
            </div>
          )}

          {/* Audio Output Result */}
          {result && (
            <div className="card" style={{ border: '1px solid #10b981' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Volume2 size={18} color="#10b981" />
                  Âm thanh đã tạo
                </h3>
                <span className="badge badge-success">
                  {result.language.toUpperCase()} • 24 kHz
                </span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 14 }}>
                Thời lượng: <strong>{result.duration_seconds}s</strong> • Model: <strong>{result.model}</strong>
              </div>
              <AudioPlayer
                wavUrl={getAudioUrl(result.output_id, 'wav')}
                mp3Url={getAudioUrl(result.output_id, 'mp3')}
                downloadWavUrl={getAudioDownloadUrl(result.output_id, 'wav')}
                downloadMp3Url={getAudioDownloadUrl(result.output_id, 'mp3')}
              />
            </div>
          )}

          {/* Tips Card */}
          {!generating && !result && (
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: 12 }}>Hướng dẫn & Mẹo</h3>
              <ul style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.8, paddingLeft: 16, margin: 0 }}>
                <li><strong>Phong cách giọng:</strong> Chọn sẵn trong menu <em>"Phong cách & Sắc thái giọng"</em> (nữ nhẹ nhàng, nam trầm ấm, MC tin tức, anime, kể chuyện...).</li>
                <li><strong>Trình phát âm thanh:</strong> Cho phép đổi tốc độ nghe trực tiếp (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x) và tua tới/lùi 5s.</li>
                <li><strong>Âm thanh cảm xúc:</strong> Bấm các nút như <code>[laughter]</code> hoặc <code>[whisper]</code> để lồng ghép tiếng cười, thì thầm tự nhiên.</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
