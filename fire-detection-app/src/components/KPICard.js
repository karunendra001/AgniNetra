import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp } from 'lucide-react';
import './KPICard.css';

export default function KPICard({ icon, label, value, trend, trendUp, color }) {
  return (
    <motion.div
      className="card kpi-card"
      style={{
        background:
          label === 'Vegetation Fires'
            ? 'var(--card-red)'
            : label === 'Industrial Heat Sources'
            ? 'var(--card-orange)'
            : label === 'Persistent Thermal Anomalies'
            ? 'var(--card-purple)'
            : 'var(--card-blue)',
      }}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className="kpi-icon" style={{ background: `${color}22`, color }}>
        {icon}
      </div>
      <div className="kpi-info">
        <p className="kpi-label">{label}</p>
        <h2 className="kpi-value">{value}</h2>
        <p className={`kpi-trend ${trendUp ? 'up' : ''}`}>
          {trendUp && <TrendingUp size={12} />} {trend}
        </p>
      </div>
    </motion.div>
  );
}