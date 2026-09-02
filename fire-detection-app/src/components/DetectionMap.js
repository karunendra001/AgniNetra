import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './DetectionMap.css';

const colorMap = {
  'Vegetation Fire': '#ff4757',
  'Industrial Heat Source': '#ff9f43',
  'Persistent Thermal Anomaly': '#a55eea',
  'Unclassified': '#576574',
};

const filters = ['all', 'Vegetation Fire', 'Industrial Heat Source', 'Persistent Thermal Anomaly'];

export default function DetectionMap({ data, activeFilter, setActiveFilter }) {
  return (
    <div className="detection-map-wrap">
      <div className="map-header">
        <h3>Live Detection Map</h3>
        <div className="map-filters">
          {filters.map(f => (
            <button
              key={f}
              className={`filter-pill ${activeFilter === f ? 'active' : ''}`}
              style={activeFilter === f && f !== 'all' ? { borderColor: colorMap[f], color: colorMap[f] } : {}}
              onClick={() => setActiveFilter(f)}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
        </div>
      </div>

      <MapContainer center={[21.5, 80]} zoom={5} className="leaflet-box" zoomControl={false} attributionControl={false}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
        />
        {data.map(d => (
          <CircleMarker
            key={d.id}
            center={[d.lat, d.lng]}
            radius={6 + d.frp / 30}
            pathOptions={{
              color: colorMap[d.classification],
              fillColor: colorMap[d.classification],
              fillOpacity: 0.55,
              weight: 1.5,
            }}
          >
            <Popup>
              <div className="popup-box">
                <strong>{d.location}</strong>
                <p>{d.classification}</p>
                <div className="popup-grid">
                  <span>Confidence</span><b>{d.confidence}%</b>
                  <span>Brightness</span><b>{d.brightness} K</b>
                  <span>FRP</span><b>{d.frp} MW</b>
                  <span>Satellite</span><b>{d.satellite}</b>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}