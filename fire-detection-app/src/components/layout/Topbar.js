import React from 'react';
import { Search, Bell, Calendar } from 'lucide-react';
import './Topbar.css';

export default function Topbar({ searchQuery, setSearchQuery, alerts, showAlerts, setShowAlerts }) {
  return (
    <header className="topbar">
      <div>
        <h1>Thermal Anomaly Command Center</h1>
        <p>India Region · NASA FIRMS (VIIRS/MODIS) + OSM Cross-Reference</p>
      </div>

      <div className="topbar-actions">
        <div className="search-box">
          <Search size={16} />
          <input
            placeholder="Search location, facility..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <button className="icon-btn">
          <Calendar size={18} />
        </button>

        <div style={{ position: 'relative' }}>
          <button className="icon-btn" onClick={() => setShowAlerts(!showAlerts)}>
            <Bell size={18} />
            {alerts.length > 0 && <span className="notif-dot" />}
          </button>

          {showAlerts && (
            <div className="notif-dropdown">
              <p className="notif-dropdown-title">Recent Alerts</p>
              {alerts.slice(0, 5).map(a => (
                <div key={a.id} className="notif-item">
                  <span>{a.location}</span>
                  <span className="notif-conf">{a.confidence}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        
      </div>
    </header>
  );
}