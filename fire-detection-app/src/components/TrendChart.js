import React from 'react';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';

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
  const trendData =
    Array.isArray(data) && data.length ? data : fallbackTrendData;

  return (
    <div>
      <h3
        style={{
          fontSize: '0.95rem',
          fontWeight: 600,
          marginBottom: 4,
          color: 'var(--text-primary)'
        }}
      >
        7-Day Detection Trend
      </h3>

      <p
        style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginBottom: 14
        }}
      >
        Vegetation fires vs. industrial thermal sources
      </p>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={trendData}>
          <defs>
            <linearGradient
              id="fireGrad"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="#dc2626"
                stopOpacity={0.25}
              />
              <stop
                offset="95%"
                stopColor="#dc2626"
                stopOpacity={0}
              />
            </linearGradient>

            <linearGradient
              id="indGrad"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="#ea8a00"
                stopOpacity={0.25}
              />
              <stop
                offset="95%"
                stopColor="#ea8a00"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e2e8f0"
          />

          <XAxis
            dataKey="day"
            stroke="#64748b"
            fontSize={11}
          />

          <YAxis
            stroke="#64748b"
            fontSize={11}
          />

          <Tooltip
            contentStyle={{
              background: '#ffffff',
              border: '1px solid #dbe3ec',
              borderRadius: 8,
              fontSize: 12,
              color: '#172033',
              boxShadow: '0 6px 18px rgba(15, 23, 42, 0.12)'
            }}
          />

          <Area
            type="monotone"
            dataKey="fires"
            stroke="#dc2626"
            fill="url(#fireGrad)"
            strokeWidth={2}
          />

          <Area
            type="monotone"
            dataKey="industrial"
            stroke="#ea8a00"
            fill="url(#indGrad)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}