import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Download, Volume2, FastForward, Rewind } from 'lucide-react';

interface AudioPlayerProps {
  wavUrl?: string;
  mp3Url?: string;
  downloadWavUrl?: string;
  downloadMp3Url?: string;
}

const SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

export default function AudioPlayer({ wavUrl, mp3Url, downloadWavUrl, downloadMp3Url }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [volume, setVolume] = useState(1.0);

  const src = wavUrl || mp3Url;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    setPlaying(false);
    setCurrentTime(0);

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => {
      setDuration(audio.duration);
      audio.playbackRate = playbackRate;
    };
    const onEnded = () => setPlaying(false);

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoadedMetadata);
    audio.addEventListener('ended', onEnded);

    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoadedMetadata);
      audio.removeEventListener('ended', onEnded);
    };
  }, [src]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const handleSpeedChange = (rate: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const skipTime = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.max(0, Math.min(duration, audio.currentTime + seconds));
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const v = parseFloat(e.target.value);
    audio.volume = v;
    setVolume(v);
  };

  const formatTime = (t: number) => {
    if (isNaN(t)) return '0:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (!src) return null;

  return (
    <div className="audio-player animate-in" style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
      <audio ref={audioRef} src={src} preload="metadata" />

      {/* Primary playback bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        {/* Play/Pause Button */}
        <button
          className="play-btn"
          onClick={togglePlay}
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: 'var(--accent-primary)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: 'none',
            cursor: 'pointer',
            flexShrink: 0,
          }}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? <Pause size={20} /> : <Play size={20} style={{ marginLeft: 2 }} />}
        </button>

        {/* Rewind / Fast Forward */}
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => skipTime(-5)}
          title="Lùi 5 giây"
          style={{ padding: 6 }}
        >
          <Rewind size={16} />
        </button>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => skipTime(5)}
          title="Tua tới 5 giây"
          style={{ padding: 6 }}
        >
          <FastForward size={16} />
        </button>

        {/* Progress Seekbar */}
        <div style={{ display: 'flex', alignItems: 'center', flex: 1, gap: 10 }}>
          <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--text-muted)', minWidth: 36 }}>
            {formatTime(currentTime)}
          </span>
          <input
            type="range"
            min={0}
            max={duration || 0}
            step={0.05}
            value={currentTime}
            onChange={handleSeek}
            style={{ flex: 1, cursor: 'pointer' }}
          />
          <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--text-muted)', minWidth: 36 }}>
            {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Speed & Volume Controls row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        {/* Playback Speed Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)', marginRight: 4, fontWeight: 600 }}>
            Tốc độ phát:
          </span>
          {SPEED_OPTIONS.map((rate) => (
            <button
              key={rate}
              type="button"
              className={`btn btn-sm ${playbackRate === rate ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                fontSize: 11,
                padding: '3px 7px',
                fontWeight: playbackRate === rate ? 700 : 400,
                borderRadius: 4,
              }}
              onClick={() => handleSpeedChange(rate)}
            >
              {rate}x
            </button>
          ))}
        </div>

        {/* Volume & Downloads */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Volume Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Volume2 size={15} color="var(--text-muted)" />
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={handleVolumeChange}
              style={{ width: 60, cursor: 'pointer' }}
              title={`Âm lượng: ${Math.round(volume * 100)}%`}
            />
          </div>

          {/* Download Buttons */}
          <div style={{ display: 'flex', gap: 6 }}>
            {downloadWavUrl && (
              <a href={downloadWavUrl} className="btn btn-secondary btn-sm" download title="Download WAV">
                <Download size={13} /> WAV
              </a>
            )}
            {downloadMp3Url && (
              <a href={downloadMp3Url} className="btn btn-secondary btn-sm" download title="Download MP3">
                <Download size={13} /> MP3
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
