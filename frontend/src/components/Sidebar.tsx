import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Mic2,
  Library,
  Box,
  Clock,
  Settings,
  AudioWaveform,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/tts', icon: Mic2, label: 'Text to Voice' },
  { to: '/voices', icon: Library, label: 'My Voices' },
  { to: '/models', icon: Box, label: 'Models' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <AudioWaveform size={20} />
        </div>
        <div>
          <h1>AI Voice Studio</h1>
          <span>Local • Private • Fast</span>
        </div>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `nav-link${isActive ? ' active' : ''}`
            }
          >
            <item.icon size={20} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          v1.0.0 • All processing local
        </div>
      </div>
    </aside>
  );
}
