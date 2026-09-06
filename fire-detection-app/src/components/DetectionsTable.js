import React from 'react';
import { Download } from 'lucide-react';
import './DetectionsTable.css';
import { emojiOf } from '../fireTypes';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
        <div className="export-cluster">
          <span className="table-count">{data.length} results</span>
          {[['geojson', 'GeoJSON'], ['kml', 'KML'], ['csv', 'CSV']].map(([fmt, label]) => (
            <a
              key={fmt}
              className="export-btn"
              href={`${API}/api/export?fmt=${fmt}`}
              title={`Download for ${fmt === 'kml' ? 'Google Earth' : fmt === 'geojson' ? 'QGIS / GIS tools' : 'spreadsheets'}`}
            >
              <Download size={12} /> {label}
            </a>
          ))}
        </div>
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
                <td><span className={`badge ${badgeClass[d.classification]}`}>{emojiOf(d.classification)} {d.classification}</span></td>
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