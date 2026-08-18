import React from 'react';
import { CheckCircle2, AlertOctagon, AlertTriangle, ShieldCheck, Info } from 'lucide-react';

export default function StatusBanner({ anomaly, sensorHealth }) {
  const isAnomaly = anomaly?.is_anomaly || false;
  const score = anomaly?.anomaly_score || 0.0;
  const isFault = sensorHealth?.status === 'FAULT_SUSPECTED';
  const reasons = anomaly?.reasons || [];

  let bannerConfig = {
    title: '🟢 SYSTEM STATUS: NORMAL',
    subtitle: 'All water quality parameters are within learned baseline boundaries. Sensor telemetry nominal.',
    bgColor: 'var(--status-normal-bg)',
    borderColor: 'var(--status-normal-glow)',
    textColor: 'var(--status-normal)',
    icon: <CheckCircle2 size={28} color="var(--status-normal)" />,
    statusBadge: 'NORMAL (NOMINAL)',
    badgeColor: 'var(--status-normal)'
  };

  if (isFault) {
    bannerConfig = {
      title: '⚠️ SYSTEM STATUS: SENSOR FAULT SUSPECTED',
      subtitle: sensorHealth?.details || `Isolated single-parameter anomaly on ${sensorHealth?.suspect_sensor} probe. Other channels remain nominal.`,
      bgColor: 'var(--status-fault-bg)',
      borderColor: 'var(--status-fault-glow)',
      textColor: 'var(--status-fault)',
      icon: <AlertTriangle size={28} color="var(--status-fault)" />,
      statusBadge: `FAULT ISOLATED (${sensorHealth?.suspect_sensor})`,
      badgeColor: 'var(--status-fault)'
    };
  } else if (isAnomaly) {
    bannerConfig = {
      title: '🔴 SYSTEM STATUS: WATER QUALITY ANOMALY DETECTED',
      subtitle: `Multiple co-varying parameters breached statistical baseline limits. Early warning triggered.`,
      bgColor: 'var(--status-anomaly-bg)',
      borderColor: 'var(--status-anomaly-glow)',
      textColor: 'var(--status-anomaly)',
      icon: <AlertOctagon size={28} color="var(--status-anomaly)" />,
      statusBadge: `ANOMALY ALERT (SCORE: ${score.toFixed(2)})`,
      badgeColor: 'var(--status-anomaly)'
    };
  }

  return (
    <div
      className="glass-panel"
      style={{
        padding: '20px 24px',
        marginBottom: '24px',
        backgroundColor: bannerConfig.bgColor,
        borderColor: bannerConfig.borderColor,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', maxWidth: '72%' }}>
          <div style={{ padding: '8px', borderRadius: '12px', background: 'rgba(0,0,0,0.2)' }}>
            {bannerConfig.icon}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px', flexWrap: 'wrap' }}>
              <h2 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '700', color: '#fff' }}>
                {bannerConfig.title}
              </h2>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: '700',
                padding: '3px 10px',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: `1px solid ${bannerConfig.badgeColor}`,
                color: bannerConfig.badgeColor
              }}>
                {bannerConfig.statusBadge}
              </span>
            </div>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.4' }}>
              {bannerConfig.subtitle}
            </p>

            {reasons.length > 0 && isAnomaly && !isFault && (
              <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Statistical Evidence Reasons:
                </span>
                {reasons.map((r, idx) => (
                  <div key={idx} style={{
                    fontSize: '0.8rem',
                    color: '#fed7d7',
                    background: 'rgba(0, 0, 0, 0.3)',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    borderLeft: '3px solid var(--status-anomaly)'
                  }}>
                    • {r}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Normalized Anomaly Index / Score Card */}
        <div style={{
          minWidth: '220px',
          background: 'rgba(8, 14, 28, 0.7)',
          borderRadius: '10px',
          padding: '12px 16px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          textAlign: 'right'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
            <span>Statistical Anomaly Index</span>
            <Info size={12} color="var(--primary)" />
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: '4px' }}>
            [0.00 – 1.00 Relative Divergence]
          </div>
          <div className="font-mono" style={{ fontSize: '1.7rem', fontWeight: '700', color: bannerConfig.textColor }}>
            {score.toFixed(2)}
          </div>
          <div style={{
            width: '100%',
            height: '6px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '3px',
            marginTop: '6px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min(100, Math.max(5, score * 100))}%`,
              height: '100%',
              background: bannerConfig.badgeColor,
              transition: 'width 0.4s ease'
            }} />
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '4px', textAlign: 'left', lineHeight: '1.2' }}>
            *Measures statistical deviation from learned baseline, not contamination probability.
          </div>
        </div>
      </div>
    </div>
  );
}
