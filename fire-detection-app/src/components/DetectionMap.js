import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './DetectionMap.css';
import { colorOf, emojiOf, CLASSIFICATIONS } from '../fireTypes';

// Google Maps tile endpoints (satellite/hybrid/roads) served as a plain tile
// layer - the most robust way to get real Google imagery inside Leaflet.
// NOTE: unofficial tile endpoint; fine for a hackathon demo. The JS API key in
// .env remains available for official APIs (Geocoding, Places) later.
const GOOGLE_TILES = {
  satellite: 'https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
  hybrid: 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
  roadmap: 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
};
const GOOGLE_SUBDOMAINS = ['0', '1', '2', '3'];

const ESRI_DARK = {
  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  attribution: '&copy; Esri &copy; OpenStreetMap contributors',
};

export default function DetectionMap({ data, activeFilter, setActiveFilter }) {
  const counts = CLASSIFICATIONS.reduce((acc, c) => {
    acc[c] = data.filter(d => d.classification === c).length;
    return acc;
  }, {});

  return (
    <div className="detection-map-wrap">
      <div className="map-header">
        <h3>Live Detection Map</h3>
        <div className="map-filters">
          {['all', ...CLASSIFICATIONS].map(f => (
            <button
              key={f}
              className={`filter-pill ${activeFilter === f ? 'active' : ''}`}
              style={activeFilter === f && f !== 'all' ? { borderColor: colorOf(f), color: colorOf(f) } : {}}
              onClick={() => setActiveFilter(f)}
            >
              {f === 'all' ? '🌍 All' : `${emojiOf(f)} ${f}`}
            </button>
          ))}
        </div>
      </div>

      <MapContainer center={[21.5, 80]} zoom={5} className="leaflet-box" zoomControl={false} attributionControl={false}>
<<<<<<< HEAD
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="🛰️ Google Satellite">
            <TileLayer
              url={GOOGLE_TILES.satellite}
              subdomains={GOOGLE_SUBDOMAINS}
              maxNativeZoom={20}
              maxZoom={22}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="🌍 Google Hybrid">
            <TileLayer
              url={GOOGLE_TILES.hybrid}
              subdomains={GOOGLE_SUBDOMAINS}
              maxNativeZoom={20}
              maxZoom={22}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="🗺️ Google Roads">
            <TileLayer
              url={GOOGLE_TILES.roadmap}
              subdomains={GOOGLE_SUBDOMAINS}
              maxNativeZoom={20}
              maxZoom={22}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="🌗 Dark (fallback)">
            <TileLayer url={ESRI_DARK.url} attribution={ESRI_DARK.attribution} />
          </LayersControl.BaseLayer>
        </LayersControl>

=======
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
        />
>>>>>>> 95ea0d0 (changed the theme to light)
        {data.map(d => (
          <CircleMarker
            key={d.id}
            center={[d.lat, d.lng]}
            radius={Math.min(11, 5 + (d.frp || 0) / 12)}
            pathOptions={{
              color: colorOf(d.classification),
              fillColor: colorOf(d.classification),
              fillOpacity: 0.75,
              weight: 1,
            }}
          >
            <Popup>
              <div className="popup-box">
                <strong>{emojiOf(d.classification)} {d.location}</strong>
                <p>{d.classification}</p>
                <div className="popup-grid">
                  <span>Confidence</span><b>{d.confidence}%</b>
                  <span>Brightness</span><b>{d.brightness} K</b>
                  <span>FRP</span><b>{d.frp} MW</b>
                  <span>Satellite</span><b>{d.satellite}</b>
                  <span>Seen</span><b>{d.time}</b>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="map-legend">
        <p className="legend-title">Heat Source Types</p>
        {CLASSIFICATIONS.map(c => (
          <div key={c} className="legend-item">
            <span
              className="legend-dot"
              style={{ background: colorOf(c), boxShadow: `0 0 6px ${colorOf(c)}` }}
            />
            <span className="legend-label">{emojiOf(c)} {c}</span>
            <span className="legend-count">{counts[c]}</span>
          </div>
        ))}
        <p className="legend-note">dot size = fire energy (FRP)</p>
      </div>
    </div>
  );
}
