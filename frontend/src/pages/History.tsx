import { useState, useEffect } from 'react';
import { Clock, Play, Download, Trash2, Search, Filter, AlertTriangle, Music, Sparkles } from 'lucide-react';
import { getHistory, deleteHistory, clearAllHistory, getAudioUrl, getAudioDownloadUrl } from '../services/api';
import AudioPlayer from '../components/AudioPlayer';
import type { HistoryEntry } from '../types';

const LANG_FLAGS: Record<string, string> = {
  vi: '🇻🇳 Tiếng Việt',
  en: '🇺🇸 English',
  ja: '🇯🇵 Japanese',
  zh: '🇨🇳 Chinese',
  ko: '🇰🇷 Korean',
  fr: '🇫🇷 French',
  de: '🇩🇪 German',
  es: '🇪🇸 Spanish',
};

export default function History() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePlayerId, setActivePlayerId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('all');
  const [isClearing, setIsClearing] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const data = await getHistory();
      setHistory(data);
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Bạn có chắc muốn xóa bản ghi này?')) return;
    try {
      await deleteHistory(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
      if (activePlayerId === id) setActivePlayerId(null);
    } catch {}
  }

  async function handleClearAll() {
    setIsClearing(true);
    try {
      await clearAllHistory();
      setHistory([]);
      setActivePlayerId(null);
      setShowConfirmModal(false);
    } catch (e: any) {
      alert(`Lỗi khi xóa lịch sử: ${e.message}`);
    } finally {
      setIsClearing(false);
    }
  }

  function formatDate(iso: string) {
    try {
      const d = new Date(iso);
      return d.toLocaleString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  // Filtered list
  const filteredHistory = history.filter((entry) => {
    const matchSearch =
      entry.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.voice_profile.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.model.toLowerCase().includes(searchQuery.toLowerCase());
    const matchLang = selectedLang === 'all' || entry.language === selectedLang;
    return matchSearch && matchLang;
  });

  const totalDurationSeconds = history.reduce((acc, h) => acc + (h.duration_seconds || 0), 0);

  return (
    <div className="animate-in">
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="page-title">Lịch Sử Tạo Giọng Nói</h1>
          <p className="page-subtitle">Xem, phát lại, tải về và quản lý các bản thu âm đã tạo</p>
        </div>

        {history.length > 0 && (
          <button
            className="btn btn-danger"
            onClick={() => setShowConfirmModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Trash2 size={16} /> Xóa toàn bộ lịch sử ({history.length})
          </button>
        )}
      </div>

      {/* Stats Summary Bar */}
      {history.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 28 }}>
          <div className="card stat-card">
            <div className="stat-icon purple">
              <Music size={24} />
            </div>
            <div>
              <div className="stat-value">{history.length}</div>
              <div className="stat-label">Tổng số bản ghi</div>
            </div>
          </div>
          <div className="card stat-card">
            <div className="stat-icon green">
              <Clock size={24} />
            </div>
            <div>
              <div className="stat-value">{totalDurationSeconds.toFixed(1)}s</div>
              <div className="stat-label">Tổng thời lượng phát</div>
            </div>
          </div>
          <div className="card stat-card">
            <div className="stat-icon blue">
              <Sparkles size={24} />
            </div>
            <div>
              <div className="stat-value">OmniVoice</div>
              <div className="stat-label">Mô hình AI sử dụng</div>
            </div>
          </div>
        </div>
      )}

      {/* Filter & Search Bar */}
      {history.length > 0 && (
        <div className="card" style={{ padding: '16px 20px', marginBottom: 24, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 240 }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
            <input
              className="form-input"
              style={{ paddingLeft: 38 }}
              placeholder="Tìm kiếm theo nội dung, tên giọng..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter size={16} color="var(--text-muted)" />
            <select
              className="form-select"
              style={{ width: 180 }}
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
            >
              <option value="all">Tất cả ngôn ngữ</option>
              <option value="vi">🇻🇳 Tiếng Việt</option>
              <option value="en">🇺🇸 English</option>
              <option value="ja">🇯🇵 Japanese</option>
              <option value="zh">🇨🇳 Chinese</option>
              <option value="ko">🇰🇷 Korean</option>
              <option value="fr">🇫🇷 French</option>
            </select>
          </div>
        </div>
      )}

      {/* History Content */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 10, padding: 32 }}>
          <div className="spinner" /> Đang tải lịch sử...
        </div>
      ) : history.length === 0 ? (
        <div className="card empty-state">
          <Clock size={54} />
          <h3>Chưa có lịch sử tạo giọng</h3>
          <p>Hãy vào mục "Text to Voice" để tạo các bản thu âm đầu tiên bằng OmniVoice!</p>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="card empty-state">
          <Search size={48} />
          <h3>Không tìm thấy kết quả</h3>
          <p>Không có bản thu nào khớp với từ khóa tìm kiếm hoặc bộ lọc hiện tại.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filteredHistory.map((entry) => (
            <div
              key={entry.id}
              className="card"
              style={{
                padding: 22,
                marginBottom: 0,
                border: activePlayerId === entry.id ? '1px solid var(--accent-primary)' : '1px solid var(--border)',
                background: activePlayerId === entry.id ? 'rgba(139, 92, 246, 0.06)' : 'var(--bg-card)',
              }}
            >
              {/* Row Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="badge badge-purple" style={{ fontSize: 13, padding: '4px 10px' }}>
                    {LANG_FLAGS[entry.language] || entry.language.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    🎙 {entry.voice_profile || 'Default Voice'}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    • {formatDate(entry.created_at)}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="badge badge-success" style={{ fontFamily: 'var(--font-mono)' }}>
                    {entry.duration_seconds}s
                  </span>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setActivePlayerId(activePlayerId === entry.id ? null : entry.id)}
                    style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    <Play size={13} /> {activePlayerId === entry.id ? 'Thu gọn' : 'Phát'}
                  </button>
                  <a
                    href={getAudioDownloadUrl(entry.id, 'wav')}
                    className="btn btn-secondary btn-sm"
                    download
                    title="Tải file WAV"
                  >
                    <Download size={13} /> WAV
                  </a>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(entry.id)}
                    title="Xóa bản ghi này"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              {/* Text content */}
              <p style={{
                fontSize: 14,
                color: 'var(--text-primary)',
                lineHeight: 1.6,
                margin: '8px 0 0',
                background: 'var(--bg-tertiary)',
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
              }}>
                "{entry.text}"
              </p>

              {/* Expanded Audio Player */}
              {activePlayerId === entry.id && (
                <div style={{ marginTop: 16 }}>
                  <AudioPlayer
                    wavUrl={getAudioUrl(entry.id, 'wav')}
                    mp3Url={getAudioUrl(entry.id, 'mp3')}
                    downloadWavUrl={getAudioDownloadUrl(entry.id, 'wav')}
                    downloadMp3Url={getAudioDownloadUrl(entry.id, 'mp3')}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Confirmation Modal for Clear All */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 20,
        }}>
          <div className="card" style={{ maxWidth: 440, width: '100%', padding: 28, border: '1px solid rgba(239, 68, 68, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--error)' }}>
                <AlertTriangle size={24} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Xác nhận xóa toàn bộ?</h3>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 24 }}>
              Hành động này sẽ xóa vĩnh viễn <strong>{history.length} bản thu âm</strong> và toàn bộ file âm thanh đã tạo trên đĩa. Bạn không thể hoàn tác hành động này.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button className="btn btn-secondary" onClick={() => setShowConfirmModal(false)} disabled={isClearing}>
                Hủy bỏ
              </button>
              <button className="btn btn-danger" onClick={handleClearAll} disabled={isClearing}>
                {isClearing ? 'Đang xóa...' : 'Đồng ý xóa toàn bộ'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
