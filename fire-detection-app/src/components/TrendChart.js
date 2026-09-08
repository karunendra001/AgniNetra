import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const fallbackTrendData = [
  { day: 'Mon', fires: 8, industrial: 14 },
  { day: 'Tue', fires: 12, industrial: 16 },
  { day: 'Wed', fires: 6, industrial: 15 },
  { day: 'Thu', fires: 15, industrial: 19 },
  { day: 'Fri', fires: 10, industrial: 17 },
  { day: 'Sat', fires: 18, industrial: 21 },
  { day: 'Sun', fires: 13, industrial: 18 },
];

export default function TrendChart({ data }) {
  const trendData = Array.isArray(data) && data.length ? data : fallbackTrendData;
  return (
    <div>
      <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 4 }}>7-Day Detection Trend</h3>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 14 }}>
        Vegetation fires vs. industrial thermal sources
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={trendData}>
          <defs>
            <linearGradient id="fireGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff4757" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ff4757" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="indGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff9f43" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ff9f43" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
          <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
          <YAxis stroke="var(--text-muted)" fontSize={11} />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12, color: 'var(--text-primary)' }} />
          <Area type="monotone" dataKey="fires" stroke="#ff4757" fill="url(#fireGrad)" strokeWidth={2} />
          <Area type="monotone" dataKey="industrial" stroke="#ff9f43" fill="url(#indGrad)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}