import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#ff4757', '#ff9f43', '#a55eea', '#576574'];

export default function ClassificationChart({ data }) {
  const counts = {};
  data.forEach(d => { counts[d.classification] = (counts[d.classification] || 0) + 1; });
  const chartData = Object.entries(counts).map(([name, value]) => ({ name, value }));

  return (
    <div>
      <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 6 }}>AI Classification Breakdown</h3>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 10 }}>
        FIRMS hotspots cross-referenced with OSM infrastructure tags
      </p>
      <ResponsiveContainer width="100%" height={230}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
          >
            {chartData.map((entry, i) => (
              <Cell key={entry.name} fill={COLORS[i % COLORS.length]} stroke="none" />
            ))}
          </Pie>
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12, color: 'var(--text-primary)' }} />
          <Legend
            layout="vertical"
            verticalAlign="middle"
            align="right"
            wrapperStyle={{ fontSize: 11, lineHeight: '20px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}