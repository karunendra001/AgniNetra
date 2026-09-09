import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from 'recharts';

const fallbackTrendData = [
  { day: 'Mon', vegetation: 8, industrial: 14, persistent: 1 },
  { day: 'Tue', vegetation: 12, industrial: 16, persistent: 2 },
  { day: 'Wed', vegetation: 6, industrial: 15, persistent: 1 },
  { day: 'Thu', vegetation: 15, industrial: 19, persistent: 3 },
  { day: 'Fri', vegetation: 10, industrial: 17, persistent: 2 },
  { day: 'Sat', vegetation: 18, industrial: 21, persistent: 4 },
  { day: 'Sun', vegetation: 13, industrial: 18, persistent: 2 },
];

// One series per fire type — colors match the map markers and legend exactly.
const SERIES = [
  { key: 'vegetation', name: '🔥 Vegetation Fires', color: '#ff4757' },
  { key: 'industrial', name: '🏭 Industrial Heat Sources', color: '#ff9f43' },
  { key: 'persistent', name: '♨️ Persistent Anomalies', color: '#a55eea' },
];

export default function TrendChart({ data }) {
  const trendData = Array.isArray(data) && data.length ? data : fallbackTrendData;
  return (
    <div>
      <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 4 }}>
        7-Day Detection Trend by Fire Type
      </h3>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 14 }}>
        Daily counts per classified type — same colors as the map markers
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={trendData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <defs>
            {SERIES.map(s => (
              <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={s.color} stopOpacity={0.4} />
                <stop offset="95%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2338" />
          <XAxis dataKey="day" stroke="#5c6785" fontSize={11} />
          <YAxis stroke="#5c6785" fontSize={11} />
          <Tooltip contentStyle={{ background: '#131a2b', border: '1px solid #263049', borderRadius: 8, fontSize: 12 }} />
          <Legend
            verticalAlign="top"
            height={30}
            iconType="circle"
            wrapperStyle={{ fontSize: 11 }}
          />
          {SERIES.map(s => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              fill={`url(#grad-${s.key})`}
              strokeWidth={2}
              connectNulls
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
