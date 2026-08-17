import { useState, useEffect } from 'react';
import { Clock, Play, Download, Trash2, RotateCcw } from 'lucide-react';
import { getHistory, deleteHistory, getAudioUrl, getAudioDownloadUrl } from '../services/api';
import type { HistoryEntry } from '../types';

const LANG_FLAGS: Record<string, string> = { en: '🇺🇸', vi: '🇻🇳', ja: '🇯🇵' };

export default function History() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [playingId, setPlayingId] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setHistory(await getHistory());
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this generation?')) return;
    try {
      await deleteHistory(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
    } catch {}
  }

  function handlePlay(id: string) {
    if (playingId === id) {
      setPlayingId(null);
      return;
    }
    setPlayingId(id);
    const audio = new Audio(getAudioUrl(id, 'wav'));
    audio.play();
    audio.onended = () => setPlayingId(null);
  }

  function formatDate(iso: string) {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Generation History</h1>
        <p className="page-subtitle">View and manage your past voice generations</p>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="spinner" /> Loading history...
        </div>
      ) : history.length === 0 ? (
        <div className="empty-state">
          <Clock size={48} />
          <h3>No Generations Yet</h3>
          <p>Start generating voices to see them here</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Language</th>
                  <th>Voice</th>
                  <th>Text</th>
                  <th>Model</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: 13 }}>{formatDate(entry.created_at)}</td>
                    <td>
                      <span style={{ fontSize: 16 }}>{LANG_FLAGS[entry.language] || '🌐'}</span>
                    </td>
                    <td style={{ fontSize: 13 }}>{entry.voice_profile}</td>
                    <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                      {entry.text}
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{entry.model}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{entry.duration_seconds}s</td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button
                          className="btn btn-icon btn-secondary"
                          onClick={() => handlePlay(entry.id)}
                          title="Play"
                          style={{ width: 30, height: 30 }}
                        >
                          <Play size={14} />
                        </button>
                        <a
                          href={getAudioDownloadUrl(entry.id, 'wav')}
                          className="btn btn-icon btn-secondary"
                          title="Download"
                          download
                          style={{ width: 30, height: 30 }}
                        >
                          <Download size={14} />
                        </a>
                        <button
                          className="btn btn-icon btn-danger"
                          onClick={() => handleDelete(entry.id)}
                          title="Delete"
                          style={{ width: 30, height: 30 }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
