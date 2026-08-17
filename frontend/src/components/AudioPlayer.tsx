import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Download } from 'lucide-react';

interface AudioPlayerProps {
  wavUrl?: string;
  mp3Url?: string;
  downloadWavUrl?: string;
  downloadMp3Url?: string;
}

export default function AudioPlayer({ wavUrl, mp3Url, downloadWavUrl, downloadMp3Url }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  const src = wavUrl || mp3Url;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => setDuration(audio.duration);
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
    } else {
      audio.play();
    }
    setPlaying(!playing);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const handleSpeed = (rate: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const formatTime = (t: number) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (!src) return null;

  return (
    <div className="audio-player animate-in">
      <audio ref={audioRef} src={src} preload="metadata" />
      <div className="audio-controls">
        <button className="play-btn" onClick={togglePlay} title={playing ? 'Pause' : 'Play'}>
          {playing ? <Pause size={20} /> : <Play size={20} style={{ marginLeft: 2 }} />}
        </button>
        <div className="audio-seekbar">
          <span className="audio-time">{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || 0}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
          />
          <span className="audio-time">{formatTime(duration)}</span>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[0.75, 1, 1.25, 1.5, 2].map((r) => (
            <button
              key={r}
              className={`btn btn-sm ${playbackRate === r ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => handleSpeed(r)}
              style={{ fontSize: 11, padding: '4px 8px' }}
            >
              {r}x
            </button>
          ))}
        </div>
      </div>
      <div className="audio-download-btns">
        {downloadWavUrl && (
          <a href={downloadWavUrl} className="btn btn-secondary btn-sm" download>
            <Download size={14} /> WAV
          </a>
        )}
        {downloadMp3Url && (
          <a href={downloadMp3Url} className="btn btn-secondary btn-sm" download>
            <Download size={14} /> MP3
          </a>
        )}
      </div>
    </div>
  );
}
