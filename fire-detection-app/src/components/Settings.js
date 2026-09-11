import React, { useEffect, useState } from 'react';
import './Settings.css';
import api from '../api/detections';

/**
 * Settings tab = system status + model transparency + notification channels.
 *
 * - Model validation card renders the report produced by backend/validate_model.py
 *   (served from GET /api/model/validation) — accuracy, per-class metrics,
 *   feature importance. This is the "prove the AI works" panel for judges.
 * - Notification channels card shows LIVE channel status (GET /api/admin/alert-status):
 *   ntfy phone push, and authority email — a formal incident notice sent FROM an
 *   SMTP sender account TO a list of concerned authorities (DM / SDMA / PCB /
 *   factory safety officers), all linkable here without touching .env.
 */
export default function Settings({ live, lastSync }) {
  const [validation, setValidation] = useState(null);
  const [valError, setValError] = useState(null);
  const [status, setStatus] = useState(null);
  const [testMsg, setTestMsg] = useState(null);
  const [testing, setTesting] = useState(false);

  // ntfy topic state
  const [ntfyTopic, setNtfyTopic] = useState('');
  const [ntfyMsg, setNtfyMsg] = useState(null);
  const [ntfyBusy, setNtfyBusy] = useState(false);

  // email sender state (the mailbox alerts are sent FROM)
  const [emUser, setEmUser] = useState('');
  const [emPass, setEmPass] = useState('');
  const [emMsg, setEmMsg] = useState(null);
  const [emBusy, setEmBusy] = useState(false);

  // authority recipients state (who alerts are sent TO)
  const [authEmails, setAuthEmails] = useState('');
  const [authMsg, setAuthMsg] = useState(null);
  const [authBusy, setAuthBusy] = useState(false);

  function loadStatus() {
    api.get('/api/admin/alert-status').then(res => setStatus(res.data)).catch(() => {});
    api.get('/api/admin/authorities').then(res => {
      if (res.data.emails?.length) setAuthEmails(res.data.emails.join(', '));
    }).catch(() => {});
  }

  useEffect(() => {
    api
      .get('/api/model/validation')
      .then(res => setValidation(res.data))
      .catch(err => setValError(err?.response?.data?.detail || 'Report not generated yet'));
    loadStatus();
    const t = setInterval(loadStatus, 30000);
    return () => clearInterval(t);
  }, []);

  async function linkNtfy() {
    setNtfyBusy(true); setNtfyMsg(null);
    try {
      const res = await api.post('/api/admin/ntfy/activate', { topic: ntfyTopic.trim() });
      setNtfyMsg((res.data.ok ? '✅ ' : '❌ ') + res.data.detail);
      if (res.data.ok) loadStatus();
    } catch (err) {
      setNtfyMsg('Failed: ' + (err?.response?.data?.detail || err.message));
    } finally { setNtfyBusy(false); }
  }

  async function linkSender() {
    setEmBusy(true); setEmMsg(null);
    try {
      const res = await api.post('/api/admin/email/sender', {
        user: emUser.trim(), password: emPass.trim(),
      });
      setEmMsg((res.data.ok ? '✅ ' : '❌ ') + res.data.detail);
      if (res.data.ok) loadStatus();
    } catch (err) {
      setEmMsg('Failed: ' + (err?.response?.data?.detail || err.message));
    } finally { setEmBusy(false); }
  }

  async function saveAuthorities() {
    setAuthBusy(true); setAuthMsg(null);
    try {
      const res = await api.post('/api/admin/authorities', { emails: authEmails });
      setAuthMsg((res.data.ok ? '✅ ' : '❌ ') + res.data.detail);
      if (res.data.ok) loadStatus();
    } catch (err) {
      setAuthMsg('Failed: ' + (err?.response?.data?.detail || err.message));
    } finally { setAuthBusy(false); }
  }

  async function sendTestAlert() {
    setTesting(true);
    setTestMsg(null);
    try {
      const res = await api.post('/api/admin/test-alert');
      const { sent, results, address, subject } = res.data;
      const lines = [`Subject: ${subject || 'AgniNetra test alert'}`];
      for (const [ch, r] of Object.entries(results || {})) {
        lines.push(`${r.ok ? '✅' : '❌'} ${ch}: ${r.detail}`);
      }
      if (address) lines.push(`📍 resolved address: ${address}`);
      setTestMsg(sent.length ? `Sent via ${sent.join(' + ')}\n` + lines.join('\n')
                             : lines.join('\n') || 'No channel configured.');
      loadStatus();
    } catch (err) {
      setTestMsg('Failed: ' + (err?.response?.data?.detail || err.message));
    } finally { setTesting(false); }
  }

  const fmtPct = v => `${(v * 100).toFixed(1)}%`;

  const pill = (ok, label, extra) => (
    <span className={`chan-pill ${ok ? 'chan-ok' : 'chan-warn'}`} title={extra || ''}>
      {ok ? '●' : '○'} {label}
    </span>
  );

  return (
    <div className="settings-wrap">
      {/* ---- system status ---- */}
      <div className="card settings-card">
        <h3>System Status</h3>
        <p className="settings-line">
          API endpoint: <code>{process.env.REACT_APP_API_URL || 'http://localhost:8000'}</code>
        </p>
        <p className="settings-line">
          Data source:{' '}
          <b style={{ color: live ? 'lightgreen' : 'orange' }}>
            {live ? 'LIVE NASA FIRMS (real-time)' : 'OFFLINE'}
          </b>
          {lastSync && (
            <>
              {' '}· last satellite sync <b>{new Date(lastSync).toLocaleString()}</b>
            </>
          )}
        </p>
      </div>

      {/* ---- model validation ---- */}
      <div className="card settings-card">
        <h3>🧠 Model Validation</h3>
        {valError && <p className="settings-muted">⚠️ {valError}</p>}
        {validation && (
          <>
            <div className="val-metrics">
              <div className="val-metric">
                <span className="val-num">{fmtPct(validation.accuracy)}</span>
                <span className="val-label">Accuracy</span>
              </div>
              <div className="val-metric">
                <span className="val-num">{fmtPct(validation.f1)}</span>
                <span className="val-label">F1 (weighted)</span>
              </div>
              <div className="val-metric">
                <span className="val-num">{validation.test_rows.toLocaleString()}</span>
                <span className="val-label">Test rows</span>
              </div>
              <div className="val-metric">
                <span className="val-num">{validation.classes.length}</span>
                <span className="val-label">Classes</span>
              </div>
            </div>
            <p className="settings-muted">
              XGBoost · {validation.train_rows.toLocaleString()} training rows ·
              stratified 80/20 split ·{' '}
              {validation.saved_model_matches
                ? '✅ deployed model verified consistent'
                : '⚠️ deployed model differs from report'}
            </p>

            <h4 className="val-subhead">Per-class performance</h4>
            <table className="val-table">
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Rows</th>
                </tr>
              </thead>
              <tbody>
                {validation.classes.map(c => {
                  const r = validation.per_class[c] || {};
                  return (
                    <tr key={c}>
                      <td>{c.replace(/_/g, ' ')}</td>
                      <td>{fmtPct(r.precision || 0)}</td>
                      <td>{fmtPct(r.recall || 0)}</td>
                      <td>{fmtPct(r['f1-score'] || 0)}</td>
                      <td>{r.support ?? 0}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <h4 className="val-subhead">What the model relies on</h4>
            <div className="feat-bars">
              {validation.feature_importance.slice(0, 5).map(f => (
                <div key={f.feature} className="feat-bar-row">
                  <span className="feat-name">{f.feature.replace(/_/g, ' ')}</span>
                  <div className="feat-track">
                    <div
                      className="feat-fill"
                      style={{ width: `${Math.min(100, f.importance * 100)}%` }}
                    />
                  </div>
                  <span className="feat-val">{fmtPct(f.importance)}</span>
                </div>
              ))}
            </div>
            <p className="settings-muted">
              Full report + charts: <code>backend/reports/MODEL_VALIDATION.md</code>
            </p>
          </>
        )}
      </div>

      {/* ---- notification channels ---- */}
      <div className="card settings-card">
        <h3>🔔 Notification Channels</h3>
        <p className="settings-muted">
          Fires an alert when a high-confidence industrial or persistent thermal
          source is detected within 5 km of a named facility. Alerts are pushed to
          ntfy and emailed as a formal incident notice to the concerned authorities.
          {status?.pipeline && (
            <> Pipeline so far: <b>{status.pipeline.total_alerts}</b> alerts logged
              {' '}(<b>{status.pipeline.sent}</b> delivered · <b>{status.pipeline.logged}</b> logged-only
              {status.pipeline.failed > 0 && <> · <b>{status.pipeline.failed}</b> failed</>}).</>
          )}
        </p>

        {status && (
          <div className="chan-pills">
            {pill(status.ntfy.configured, 'ntfy push',
              status.ntfy.configured ? `topic: ${status.ntfy.topic}` : 'not linked')}
            {pill(status.email.fully_configured, 'Authority email',
              status.email.fully_configured
                ? `${status.email.sender} → ${status.email.authorities.length} authority address(es)`
                : 'sender or recipients missing')}
            {pill(true, `📍 ${status.geocoding.provider}`, status.geocoding.note || '')}
          </div>
        )}
        {status?.geocoding?.note && (
          <p className="settings-muted" style={{ color: '#f1c40f' }}>
            ⚠️ {status.geocoding.note}
          </p>
        )}

        {/* ---- ntfy push (phone channel) ---- */}
        <h4 className="val-subhead">📱 ntfy phone push (1 minute, no account)</h4>
        <ol className="chan-steps">
          <li>Install the free <a href="https://ntfy.sh" target="_blank" rel="noreferrer">ntfy</a> app (Play Store / App Store).</li>
          <li>Pick any topic name below — e.g. <code>agni-fire-26162</code>.</li>
          <li>In the app: <b>Subscribe to topic</b> → type the exact same name. Alerts pop on your phone.</li>
        </ol>
        <div className="chan-row">
          <input className="chan-input" placeholder="agni-fire-26162"
                 value={ntfyTopic} onChange={e => setNtfyTopic(e.target.value)} />
          <button className="test-alert-btn" onClick={linkNtfy} disabled={ntfyBusy || !ntfyTopic.trim()}>
            {ntfyBusy ? '…' : 'Link & test'}
          </button>
        </div>
        {ntfyMsg && <p className="settings-line">{ntfyMsg}</p>}

        {/* ---- authority email ---- */}
        <h4 className="val-subhead">📧 Email alerts to concerned authorities</h4>
        <p className="settings-muted">
          Step 1 — connect the <b>sender</b> account alerts are sent from. Gmail:
          use a 16-char <i>app password</i> (Google Account → Security → App
          passwords), not your login password.
        </p>
        <div className="chan-row">
          <input className="chan-input" type="email" placeholder="sender@gmail.com"
                 value={emUser} onChange={e => setEmUser(e.target.value)} />
          <input className="chan-input" type="password" placeholder="app password"
                 value={emPass} onChange={e => setEmPass(e.target.value)} />
          <button className="test-alert-btn" onClick={linkSender}
                  disabled={emBusy || !emUser.trim() || !emPass.trim()}>
            {emBusy ? '…' : 'Connect sender'}
          </button>
        </div>
        {emMsg && <p className="settings-line">{emMsg}</p>}

        <p className="settings-muted">
          Step 2 — list the <b>authorities</b> who should receive the formal alert
          (comma-separated): District Magistrate, State Disaster Management
          Authority, Pollution Control Board, factory safety officers, your team.
          Every alert email is a formatted incident notice with location,
          confidence, satellite source and a map link — ready to forward.
        </p>
        <div className="chan-row">
          <textarea
            className="chan-input chan-textarea"
            rows={3}
            placeholder={'dm@district.gov.in, sdma@state.gov.in, safety@plant.co.in'}
            value={authEmails}
            onChange={e => setAuthEmails(e.target.value)}
          />
          <button className="test-alert-btn" onClick={saveAuthorities}
                  disabled={authBusy || !authEmails.trim()}>
            {authBusy ? '…' : 'Save authorities'}
          </button>
        </div>
        {authMsg && <p className="settings-line">{authMsg}</p>}

        {/* ---- test ---- */}
        <button className="test-alert-btn" onClick={sendTestAlert} disabled={testing}>
          {testing ? 'Sending…' : '🧪 Send test alert'}
        </button>
        {testMsg && <p className="settings-line" style={{ whiteSpace: 'pre-line' }}>{testMsg}</p>}
      </div>
    </div>
  );
}
