import React, { useState } from 'react';
import { LineChart, Activity, Layers } from 'lucide-react';

export default function TrendChart({ history, baseline }) {
  const [selectedMetric, setSelectedMetric] = useState('all');

  const readings = history?.readings || [];

  if (readings.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)' }}>
        Waiting for telemetry time-series records...
      </div>
    );
  }

  // Define metric configurations
  const metricConfigs = {
    ph: { label: 'pH Level', color: '#00d2ff', min: 0, max: 14, unit: 'pH' },
    turbidity: { label: 'Turbidity', color: '#38ef7d', min: 0, max: 50, unit: 'NTU' },
    ec: { label: 'Conductivity (EC)', color: '#f59e0b', min: 0, max: 1200, unit: 'µS/cm' },
    temperature: { label: 'Temperature', color: '#ff6b6b', min: 15, max: 40, unit: '°C' }
  };

  const chartWidth = 700;
  const chartHeight = 220;
  const padding = { top: 20, right: 30, bottom: 30, left: 40 };

  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // Generate SVG paths for each metric
  const generatePath = (key) => {
    const config = metricConfigs[key];
    const points = readings.map((r, i) => {
      const x = padding.left + (i / Math.max(1, readings.length - 1)) * innerWidth;
      const val = r[key];
      const clampedVal = Math.max(config.min, Math.min(config.max, val));
      const normalized = (clampedVal - config.min) / (config.max - config.min);
      const y = padding.top + innerHeight - normalized * innerHeight;
      return `${x},${y}`;
    });
    return `M ${points.join(' L ')}`;
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="var(--primary)" />
          <h3 className="font-heading" style={{ fontSize: '1rem', fontWeight: '600', color: '#fff' }}>
            Multi-Parameter Telemetry History
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            ({readings.length} points)
          </span>
        </div>

        {/* Metric Selector Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedMetric('all')}
            style={{
              background: selectedMetric === 'all' ? 'rgba(0, 210, 255, 0.2)' : 'rgba(255,255,255,0.05)',
              border: `1px solid ${selectedMetric === 'all' ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}`,
              color: selectedMetric === 'all' ? '#fff' : 'var(--text-muted)',
              fontSize: '0.75rem',
              padding: '4px 10px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            All Channels
          </button>
          {Object.entries(metricConfigs).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => setSelectedMetric(key)}
              style={{
                background: selectedMetric === key ? `${cfg.color}22` : 'rgba(255,255,255,0.05)',
                border: `1px solid ${selectedMetric === key ? cfg.color : 'rgba(255,255,255,0.1)'}`,
                color: selectedMetric === key ? cfg.color : 'var(--text-muted)',
                fontSize: '0.75rem',
                padding: '4px 10px',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: cfg.color }} />
              {cfg.label}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: 'auto', minWidth: '450px' }}>
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padding.top + innerHeight * pct;
            return (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.07)"
                  strokeDasharray="4 4"
                />
              </g>
            );
          })}

          {/* Time axis */}
          <line
            x1={padding.left}
            y1={chartHeight - padding.bottom}
            x2={chartWidth - padding.right}
            y2={chartHeight - padding.bottom}
            stroke="rgba(255, 255, 255, 0.2)"
          />

          {/* Series lines */}
          {Object.entries(metricConfigs).map(([key, cfg]) => {
            if (selectedMetric !== 'all' && selectedMetric !== key) return null;
            return (
              <g key={key}>
                <path
                  d={generatePath(key)}
                  fill="none"
                  stroke={cfg.color}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ transition: 'd 0.3s ease' }}
                />
                {/* Dots for latest 5 points */}
                {readings.slice(-5).map((r, idx) => {
                  const actualIdx = readings.length - 5 + idx;
                  const x = padding.left + (actualIdx / Math.max(1, readings.length - 1)) * innerWidth;
                  const val = r[key];
                  const clampedVal = Math.max(cfg.min, Math.min(cfg.max, val));
                  const normalized = (clampedVal - cfg.min) / (cfg.max - cfg.min);
                  const y = padding.top + innerHeight - normalized * innerHeight;
                  return (
                    <circle
                      key={idx}
                      cx={x}
                      cy={y}
                      r="3.5"
                      fill={cfg.color}
                      stroke="#070b14"
                      strokeWidth="1.5"
                    />
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend Bar */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {Object.entries(metricConfigs).map(([key, cfg]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '3px', background: cfg.color, borderRadius: '2px' }} />
            <span>{cfg.label} ({cfg.unit})</span>
          </div>
        ))}
      </div>
    </div>
  );
}
