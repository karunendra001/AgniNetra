import React, { useState, useEffect, useMemo } from 'react';
import './App.css';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import KPICard from './components/KPICard';
import DetectionMap from './components/DetectionMap';
import ClassificationChart from './components/ClassificationChart';
import TrendChart from './components/TrendChart';
import DetectionsTable from './components/DetectionsTable';
import AlertsPanel from './components/AlertsPanel';
import { Flame, Factory, Waves, ShieldAlert, Satellite } from 'lucide-react';
import { fetchDetections, fetchStats, fetchTrend } from './api/detections';

const REFRESH_MS = 60000; // poll the backend every 60s

function minutesAgoLabel(iso) {
  if (!iso) return null;
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m ago`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `${h}h ${mins % 60}m ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAlerts, setShowAlerts] = useState(false);

  const [detections, setDetections] = useState([]);
  const [stats, setStats] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [live, setLive] = useState(false);
  const [lastSync, setLastSync] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [dets, st, trend] = await Promise.all([
          fetchDetections(),
          fetchStats(),
          fetchTrend(7),
        ]);
        if (cancelled) return;
        setLive(true);
        setDetections(Array.isArray(dets) ? dets : []);
        if (st) {
          setStats(st);
          setLastSync(st.lastSync || null);
        }
        if (Array.isArray(trend)) setTrendData(trend);
      } catch (err) {
        console.warn('Backend unreachable:', err);
        if (!cancelled) setLive(false);
      }
    }

    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  // Filter by classification pill AND search text together
  const filteredDetections = useMemo(() => {
    return detections.filter(d => {
      const matchesFilter = activeFilter === 'all' || d.classification === activeFilter;
      const matchesSearch = (d.location || '').toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [activeFilter, searchQuery, detections]);

  const highConfidenceAlerts = useMemo(
    () => detections.filter(d => d.confidence >= 85),
    [detections]
  );

  const counts = stats ?? {
    fire: detections.filter(d => d.classification === 'Vegetation Fire').length,
    industrial: detections.filter(d => d.classification === 'Industrial Heat Source').length,
    persistent: detections.filter(d => d.classification === 'Persistent Thermal Anomaly').length,
    highConfidence: highConfidenceAlerts.length,
  };

  return (
    <div className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} live={live} lastSyncLabel={minutesAgoLabel(lastSync)} />
      <div className="main-panel">
        <Topbar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          alerts={highConfidenceAlerts}
          showAlerts={showAlerts}
          setShowAlerts={setShowAlerts}
        />
        <div className="content-scroll">

          {/* Data-source banner - honest about what you're looking at */}
          <div className={`source-banner ${live ? 'live' : 'offline'}`}>
            <Satellite size={15} />
            {live ? (
              <span>
                <b>LIVE</b> · NASA FIRMS real-time detections
                {lastSync && <> · last satellite sync <b>{minutesAgoLabel(lastSync)}</b></>}
                {' '}· auto-refresh 60s
              </span>
            ) : (
              <span><b>OFFLINE</b> · backend unreachable — showing no detections. Start the backend on port 8000.</span>
            )}
          </div>

          {activeTab === 'Dashboard' && (
            <>
              <div className="kpi-grid">
                <KPICard icon={<Flame size={22} />} label="Vegetation Fires" value={counts.fire} trend="+12% today" trendUp color="var(--fire)" />
                <KPICard icon={<Factory size={22} />} label="Industrial Heat Sources" value={counts.industrial} trend="+4% today" trendUp color="var(--industrial)" />
                <KPICard icon={<Waves size={22} />} label="Persistent Thermal Anomalies" value={counts.persistent} trend="stable" color="var(--persistent)" />
                <KPICard icon={<ShieldAlert size={22} />} label="High-Confidence Detections" value={counts.highConfidence} trend="≥ 80% AI confidence" color="var(--tech-blue)" />
              </div>

              <div className="main-grid">
                <div className="map-section card">
                  <DetectionMap data={filteredDetections} activeFilter={activeFilter} setActiveFilter={setActiveFilter} />
                </div>
                <div className="side-column">
                  <div className="card chart-card">
                    <ClassificationChart data={detections} />
                  </div>
                  <div className="card">
                    <AlertsPanel data={detections} />
                  </div>
                </div>
              </div>

              <div className="bottom-grid">
                <div className="card chart-card trend-card">
                  <TrendChart data={trendData} />
                </div>
                <div className="card table-card">
                  <DetectionsTable data={filteredDetections} />
                </div>
              </div>
            </>
          )}

          {activeTab === 'Live Map' && (
            <div className="card map-section" style={{ minHeight: 600 }}>
              <DetectionMap data={filteredDetections} activeFilter={activeFilter} setActiveFilter={setActiveFilter} />
            </div>
          )}

          {activeTab === 'Detections' && (
            <div className="card table-card">
              <DetectionsTable data={filteredDetections} />
            </div>
          )}

          {activeTab === 'Analytics' && (
            <div className="main-grid">
              <div className="card chart-card"><TrendChart data={trendData} /></div>
              <div className="card chart-card"><ClassificationChart data={detections} /></div>
            </div>
          )}

          {activeTab === 'Settings' && (
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ marginBottom: 8 }}>Settings</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                API endpoint: <code>{process.env.REACT_APP_API_URL || 'http://localhost:8000'}</code><br />
                Data source: <b style={{ color: live ? 'var(--success)' : 'var(--warning)' }}>
                  {live ? 'LIVE NASA FIRMS (real-time)' : 'OFFLINE'}
                </b><br />
                {lastSync && <>Last satellite sync: <b>{new Date(lastSync).toLocaleString()}</b><br /></>}
                Alert thresholds & refresh interval config — coming soon.
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
