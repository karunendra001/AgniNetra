import React from 'react';
import './AlertsPanel.css';
import { emojiOf } from '../fireTypes';

export default function AlertsPanel({ data }) {
  const highPriority = data.filter(d => d.confidence >= 85).slice(0, 4);

  return (
    <div className="alerts-panel">
      <h3>Priority Alerts</h3>
      <p className="alerts-sub">High-confidence anomalies (≥85%)</p>
      <div className="alerts-list">
        {highPriority.map(a => (
          <div key={a.id} className="alert-row">
            <span className="alert-emoji" title={a.classification}>{emojiOf(a.classification)}</span>
            <div className="alert-text">
              <p className="alert-loc">{a.location}</p>
              <p className="alert-meta">{a.classification} · {a.confidence}% confidence</p>
            </div>
            <span className="alert-time">{a.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}