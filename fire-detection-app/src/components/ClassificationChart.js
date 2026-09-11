import React from 'react';

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

const COLORS = [
  '#dc2626', // Fire
  '#ea8a00', // Industrial
  '#7c3aed', // Persistent
  '#64748b'  // Unclassified
];

export default function ClassificationChart({ data }) {
  const counts = {};

  data.forEach(d => {
    counts[d.classification] =
      (counts[d.classification] || 0) + 1;
  });

  const chartData = Object.entries(counts).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div>
      <h3
        style={{
          fontSize: '0.95rem',
          fontWeight: 600,
          marginBottom: 6,
          color: 'var(--text-primary)'
        }}
      >
        Thermal Source Classification
      </h3>

      <p
        style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginBottom: 10
        }}
      >
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
              <Cell
                key={entry.name}
                fill={COLORS[i % COLORS.length]}
                stroke="none"
              />
            ))}
          </Pie>

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

          <Legend
            layout="vertical"
            verticalAlign="middle"
            align="right"
            wrapperStyle={{
              fontSize: 11,
              lineHeight: '20px',
              color: '#64748b'
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}