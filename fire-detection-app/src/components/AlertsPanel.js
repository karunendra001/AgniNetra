import React, { useState, useEffect } from 'react';
import './AlertsPanel.css';
import { emojiOf } from '../fireTypes';
import api from '../api/detections';

/**
 * Real alert feed.
 *
 * Primary source: GET /api/alerts — the backend's alert log. These are
 * detections that passed the alert rule (industrial/persistent class,
 * ML confidence >= threshold, within ALERT_RADIUS_KM of a named OSM
 * facility) — pushed to ntfy and emailed to the concerned authorities
 * when those channels are linked.
 *
 * Fallback: if no alerts have fired yet, show the highest-confidence
 * detections from the live feed so the panel is never empty in a demo.
 */
export default function AlertsPanel({ data }) {
  const [alerts, setAlerts] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [pushOn, setPushOn] = useState(
    typeof Notification !== 'undefined' && Notification.permission === 'granted'
  );
  const seenIds = React.useRef(new Set());
  const primed = React.useRef(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await api.get('/api/alerts', { params: { limit: 8 } });
        if (!cancelled) setAlerts(Array.isArray(res.data) ? res.data : []);
      } catch {
        if (!cancelled) setAlerts([]);
      } finally {
        if (!cancelled) setLoaded(true);
      }
    }
    load();
    const timer = setInterval(load, 60000); // same cadence as dashboard refresh
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  // Browser push: raise a native notification for every new alert row.
  // Permission must be granted once via the button (or the browser's bell icon).
  useEffect(() => {
    if (!pushOn || typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    if (!primed.current) {
      // first load after enabling: remember existing rows, don't replay history
      alerts.forEach(a => seenIds.current.add(a.id));
      primed.current = true;
      return;
    }
    alerts.filter(a => !seenIds.current.has(a.id)).forEach(a => {
      seenIds.current.add(a.id);
      try {
        new Notification('🚨 AgniNetra: ' + a.classification, {
          body: `${a.address || a.facility_name || ''}\n` +
                `${Math.round(a.ml_confidence)}% · ` +
                `${a.facility_distance_m ? (a.facility_distance_m / 1000).toFixed(1) + ' km from facility' : 'near facility'}`,
          tag: 'agninetra-' + a.id,
        });
      } catch { /* notification API unavailable */ }
    });
  }, [alerts, pushOn]);

  async function enablePush() {
    if (typeof Notification === 'undefined') return;
    const perm = await Notification.requestPermission();
    setPushOn(perm === 'granted');
    if (perm === 'granted') {
      new Notification('🔥 AgniNetra alerts on', {
        body: 'You will now get a pop-up for every new fire alert — even in another tab.',
      });
    }
  }

  const hasRealAlerts = alerts.length > 0;
  // Fallback view: top high-confidence detections from the live feed
  const fallback = (data || []).filter(d => d.confidence >= 85).slice(0, 4);

  return (
    <div className="alerts-panel">
      <div className="alerts-head">
        <div>
          <h3>Priority Alerts</h3>
          <p className="alerts-sub">
            {hasRealAlerts
              ? 'Industrial / persistent sources near named facilities'
              : 'High-confidence anomalies (≥85%) — no facility alerts fired yet'}
          </p>
        </div>
        {!pushOn ? (
          <button className="push-btn" onClick={enablePush} title="Get a pop-up for every new alert">
            🔔 Enable pop-ups
          </button>
        ) : (
          <span className="push-on" title="Browser notifications are active">🔔 on</span>
        )}
      </div>

      <div className="alerts-list">
        {hasRealAlerts &&
          alerts.map(a => {
            // 'logged' = stored & shown here; delivery is a bonus channel
            const chip =
              a.status === 'sent' ? { t: '✅ delivered', c: 'chip-sent' }
              : a.status === 'failed' ? { t: '⚠️ send failed', c: 'chip-failed' }
              : { t: '📋 logged', c: 'chip-logged' };
            return (
              <div key={`a-${a.id}`} className="alert-row alert-real">
                <span className="alert-emoji" title={a.classification}>
                  {emojiOf(a.classification)}
                </span>
                <div className="alert-text">
                  <p className="alert-loc" title={a.address || a.facility_name}>
                    {a.address || a.facility_name || a.classification}
                  </p>
                  <p className="alert-meta">
                    {a.classification} · {Math.round(a.ml_confidence)}% ·{' '}
                    {a.facility_distance_m
                      ? `${(a.facility_distance_m / 1000).toFixed(1)} km from facility`
                      : 'near facility'}
                  </p>
                </div>
                <span className="alert-right">
                  <span className={`alert-chip ${chip.c}`} title={a.delivery_detail || ''}>
                    {chip.t}
                  </span>
                  <span className="alert-time">
                    {new Date(
                      a.created_at.endsWith('Z') ? a.created_at : a.created_at + 'Z'
                    ).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </span>
              </div>
            );
          })}

        {!hasRealAlerts &&
          fallback.map(a => (
            <div key={`d-${a.id}`} className="alert-row">
              <span className="alert-emoji" title={a.classification}>
                {emojiOf(a.classification)}
              </span>
              <div className="alert-text">
                <p className="alert-loc">{a.location}</p>
                <p className="alert-meta">
                  {a.classification} · {a.confidence}% confidence
                </p>
              </div>
              <span className="alert-time">{a.time}</span>
            </div>
          ))}

        {loaded && !hasRealAlerts && fallback.length === 0 && (
          <p className="alerts-empty">No high-confidence detections right now.</p>
        )}
      </div>

      {hasRealAlerts && (
        <p className="alerts-footer">
          📍 Every alert carries the fire's street address. Chips: <b>delivered</b> =
          pushed via ntfy / emailed to authorities, <b>logged</b> = stored & shown (link
          channels in Settings → Notification Channels), <b>send failed</b> = a linked
          channel errored.
        </p>
      )}
    </div>
  );
}
