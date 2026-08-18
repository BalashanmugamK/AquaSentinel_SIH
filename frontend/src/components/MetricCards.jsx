import React from 'react';
import { Gauge, Waves, Zap, Thermometer } from 'lucide-react';

export default function MetricCards({ reading, baseline, sensorHealth }) {
  const metrics = [
    {
      id: 'ph',
      title: 'pH Level',
      value: reading ? reading.ph.toFixed(2) : '--',
      unit: 'pH',
      icon: <Gauge size={20} color="#00d2ff" />,
      nominalRange: '6.5 – 8.5',
      baselineMean: baseline?.ph?.mean ?? 7.2,
      isOutlier: reading ? (reading.ph < 6.5 || reading.ph > 8.5) : false,
      hardwareNote: 'Potentiometer 1 (Pin 34)'
    },
    {
      id: 'turbidity',
      title: 'Turbidity',
      value: reading ? reading.turbidity.toFixed(2) : '--',
      unit: 'NTU',
      icon: <Waves size={20} color="#38ef7d" />,
      nominalRange: '< 5.0 NTU',
      baselineMean: baseline?.turbidity?.mean ?? 1.5,
      isOutlier: reading ? (reading.turbidity > 15.0) : false,
      hardwareNote: 'Potentiometer 2 (Pin 35)'
    },
    {
      id: 'ec',
      title: 'Conductivity (EC)',
      value: reading ? reading.ec.toFixed(1) : '--',
      unit: 'µS/cm',
      icon: <Zap size={20} color="#f59e0b" />,
      nominalRange: '200 – 500 µS/cm',
      baselineMean: baseline?.ec?.mean ?? 320.0,
      isOutlier: reading ? (reading.ec > 800.0) : false,
      hardwareNote: 'Potentiometer 3 (Pin 32)'
    },
    {
      id: 'temperature',
      title: 'Temperature',
      value: reading ? reading.temperature.toFixed(1) : '--',
      unit: '°C',
      icon: <Thermometer size={20} color="#ff6b6b" />,
      nominalRange: '20.0 – 32.0 °C',
      baselineMean: baseline?.temperature?.mean ?? 26.8,
      isOutlier: reading ? (reading.temperature < 10.0 || reading.temperature > 45.0) : false,
      hardwareNote: 'DS18B20 Digital (Pin 4)'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '16px',
      marginBottom: '24px'
    }}>
      {metrics.map((m) => {
        const isFaultSuspect = sensorHealth?.status === 'FAULT_SUSPECTED' && sensorHealth?.suspect_sensor?.toLowerCase() === m.id.toLowerCase();
        
        let cardBorder = 'var(--border-subtle)';
        let statusBadge = { text: 'NOMINAL', color: 'var(--status-normal)', bg: 'var(--status-normal-bg)' };

        if (isFaultSuspect) {
          cardBorder = 'var(--status-fault)';
          statusBadge = { text: 'FAULT SUSPECT', color: 'var(--status-fault)', bg: 'var(--status-fault-bg)' };
        } else if (m.isOutlier) {
          cardBorder = 'var(--status-anomaly)';
          statusBadge = { text: 'OUTLIER', color: 'var(--status-anomaly)', bg: 'var(--status-anomaly-bg)' };
        }

        return (
          <div
            key={m.id}
            className="glass-panel"
            style={{
              padding: '18px 20px',
              borderColor: cardBorder,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)' }}>
                    {m.icon}
                  </div>
                  <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-muted)' }}>
                    {m.title}
                  </span>
                </div>
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: '700',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  color: statusBadge.color,
                  backgroundColor: statusBadge.bg,
                  border: `1px solid ${statusBadge.color}`
                }}>
                  {statusBadge.text}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '8px 0' }}>
                <span className="font-mono" style={{ fontSize: '2rem', fontWeight: '700', color: m.isOutlier || isFaultSuspect ? statusBadge.color : '#fff' }}>
                  {m.value}
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '500' }}>
                  {m.unit}
                </span>
              </div>
            </div>

            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                <span>Baseline Mean:</span>
                <strong style={{ color: 'var(--text-muted)' }}>{m.baselineMean} {m.unit}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Hardware Channel:</span>
                <span style={{ color: 'var(--primary)' }}>{m.hardwareNote}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
