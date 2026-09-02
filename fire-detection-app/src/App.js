import React, { useState, useMemo } from 'react';
import './App.css';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import KPICard from './components/KPICard';
import DetectionMap from './components/DetectionMap';
import ClassificationChart from './components/ClassificationChart';
import TrendChart from './components/TrendChart';
import DetectionsTable from './components/DetectionsTable';
import AlertsPanel from './components/AlertsPanel';
import { Flame, Factory, Waves, ShieldAlert } from 'lucide-react';
import { detections } from './data/mockData';

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAlerts, setShowAlerts] = useState(false);

  // Filter by classification pill AND search text together
  const filteredDetections = useMemo(() => {
    return detections.filter(d => {
      const matchesFilter = activeFilter === 'all' || d.classification === activeFilter;
      const matchesSearch = d.location.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [activeFilter, searchQuery]);

  const highConfidenceAlerts = useMemo(
    () => detections.filter(d => d.confidence >= 85),
    []
  );

  const counts = {
    fire: detections.filter(d => d.classification === 'Vegetation Fire').length,
    industrial: detections.filter(d => d.classification === 'Industrial Heat Source').length,
    persistent: detections.filter(d => d.classification === 'Persistent Thermal Anomaly').length,
    highConfidence: highConfidenceAlerts.length,
  };

  return (
    <div className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-panel">
        <Topbar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          alerts={highConfidenceAlerts}
          showAlerts={showAlerts}
          setShowAlerts={setShowAlerts}
        />
        <div className="content-scroll">

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
                  <TrendChart />
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
              <div className="card chart-card"><TrendChart /></div>
              <div className="card chart-card"><ClassificationChart data={detections} /></div>
            </div>
          )}

          {activeTab === 'Settings' && (
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ marginBottom: 8 }}>Settings</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Coming soon — API endpoint config, alert thresholds, refresh interval.
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;