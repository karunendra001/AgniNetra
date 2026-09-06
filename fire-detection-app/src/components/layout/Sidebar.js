import React from 'react';
import { LayoutDashboard, Map, Flame, BarChart3, Settings, Satellite } from 'lucide-react';
import './Sidebar.css';

const navItems = [
  { icon: <LayoutDashboard size={19} />, label: 'Dashboard' },
  { icon: <Map size={19} />, label: 'Live Map' },
  { icon: <Flame size={19} />, label: 'Detections' },
  { icon: <BarChart3 size={19} />, label: 'Analytics' },
  { icon: <Settings size={19} />, label: 'Settings' },
];

export default function Sidebar({ activeTab, setActiveTab, live = false, lastSyncLabel = null }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Satellite size={24} color="var(--tech-blue)" />
        <span>Agni<b>Netra</b></span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <div
            key={item.label}
            className={`sidebar-link ${activeTab === item.label ? 'active' : ''}`}
            onClick={() => setActiveTab(item.label)}
          >
            {item.icon}
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className={`status-dot ${live ? '' : 'offline'}`} />
        <div>
          <p className="status-text">FIRMS Feed</p>
          <p className="status-sub">
            {live ? `Live${lastSyncLabel ? ` · synced ${lastSyncLabel}` : ''}` : 'Offline — backend down'}
          </p>
        </div>
      </div>
    </aside>
  );
}