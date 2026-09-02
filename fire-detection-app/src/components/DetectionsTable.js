import React from 'react';
import './DetectionsTable.css';

const badgeClass = {
  'Vegetation Fire': 'badge-fire',
  'Industrial Heat Source': 'badge-industrial',
  'Persistent Thermal Anomaly': 'badge-persistent',
  'Unclassified': 'badge-unclassified',
};

export default function DetectionsTable({ data }) {
  return (
    <div className="table-wrap">
      <div className="table-header-row">
        <h3>Recent Detections</h3>
        <span className="table-count">{data.length} results</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Location</th>
              <th>Classification</th>
              <th>Confidence</th>
              <th>FRP (MW)</th>
              <th>Satellite</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 8).map(d => (
              <tr key={d.id}>
                <td className="loc-cell">{d.location}</td>
                <td><span className={`badge ${badgeClass[d.classification]}`}>{d.classification}</span></td>
                <td>
                  <div className="conf-bar-wrap">
                    <div className="conf-bar" style={{ width: `${d.confidence}%` }} />
                    <span>{d.confidence}%</span>
                  </div>
                </td>
                <td>{d.frp}</td>
                <td>{d.satellite}</td>
                <td className="muted">{d.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}