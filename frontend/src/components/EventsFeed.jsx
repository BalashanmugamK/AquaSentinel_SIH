import React from 'react';
import { BellRing, CheckCircle2, AlertOctagon, AlertTriangle, Clock } from 'lucide-react';

export default function EventsFeed({ events }) {
  const eventList = events || [];

  return (
    <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BellRing size={18} color="var(--primary)" />
          <h3 className="font-heading" style={{ fontSize: '1rem', fontWeight: '600', color: '#fff' }}>
            Event Alert Log
          </h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          {eventList.filter(e => e.status === 'ACTIVE').length} Active Alerts
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '380px' }}>
        {eventList.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            <CheckCircle2 size={32} color="var(--status-normal)" style={{ margin: '0 auto 8px', opacity: 0.7 }} />
            No active or past warning events recorded.
          </div>
        ) : (
          eventList.map((ev) => {
            const isActive = ev.status === 'ACTIVE';
            const isFault = ev.event_type === 'SENSOR_FAULT_SUSPECTED';

            let tagColor = isActive ? (isFault ? 'var(--status-fault)' : 'var(--status-anomaly)') : 'var(--text-dim)';
            let tagBg = isActive ? (isFault ? 'var(--status-fault-bg)' : 'var(--status-anomaly-bg)') : 'rgba(255,255,255,0.04)';

            return (
              <div
                key={ev.id}
                style={{
                  background: 'rgba(8, 14, 28, 0.6)',
                  border: `1px solid ${isActive ? tagColor : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: '10px',
                  padding: '12px 14px',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {isFault ? (
                      <AlertTriangle size={14} color={tagColor} />
                    ) : (
                      <AlertOctagon size={14} color={tagColor} />
                    )}
                    <span className="font-mono" style={{ fontSize: '0.8rem', fontWeight: '700', color: tagColor }}>
                      {ev.event_type}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      fontSize: '0.65rem',
                      fontWeight: '700',
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: tagBg,
                      color: tagColor,
                      border: `1px solid ${tagColor}`
                    }}>
                      {ev.severity}
                    </span>
                    <span style={{
                      fontSize: '0.65rem',
                      fontWeight: '600',
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: isActive ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.15)',
                      color: isActive ? '#fca5a5' : '#86efac'
                    }}>
                      {ev.status}
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.35', marginBottom: '6px' }}>
                  {ev.details || 'Event logged by anomaly engine.'}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                  <Clock size={11} />
                  <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  <span>• Node {ev.device_id}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
