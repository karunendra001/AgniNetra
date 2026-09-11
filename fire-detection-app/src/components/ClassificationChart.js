import React from 'react';

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip
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

      <ResponsiveContainer width="100%" height={210}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={52}
            outerRadius={80}
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
        </PieChart>
      </ResponsiveContainer>

      {/* wrapped legend under the chart — never overlaps the donut */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '6px 14px',
          justifyContent: 'center',
          marginTop: 2
        }}
      >
        {chartData.map((entry, i) => (
          <span
            key={entry.name}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 11,
              color: '#64748b'
            }}
          >
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: '50%',
                background: COLORS[i % COLORS.length],
                display: 'inline-block'
              }}
            />
            {entry.name}
          </span>
        ))}
      </div>
    </div>
  );
}