import React from 'react';
import { Droplets, ShieldCheck, Activity, Radio } from 'lucide-react';

export default function Header({ isConnected, lastUpdated }) {
  return (
    <header className="glass-panel" style={{ padding: '16px 24px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'var(--primary-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px var(--primary-glow)'
        }}>
          <Droplets size={24} color="#04101e" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="font-heading" style={{ fontSize: '1.4rem', fontWeight: '700', letterSpacing: '-0.02em', color: '#fff' }}>
              AquaSentinel
            </h1>
            <span style={{
              fontSize: '0.7rem',
              padding: '2px 8px',
              borderRadius: '20px',
              background: 'rgba(0, 210, 255, 0.15)',
              border: '1px solid rgba(0, 210, 255, 0.3)',
              color: 'var(--primary)',
              fontWeight: '600'
            }}>
              AGENTIC WATER INTELLIGENCE
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Monitored Target: <strong style={{ color: '#e2e8f0' }}>Simulated Reservoir 01</strong> | Node: <code className="font-mono" style={{ color: 'var(--primary)' }}>AQUA-01</code>
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <Radio size={14} color={isConnected ? 'var(--status-normal)' : 'var(--text-dim)'} className={isConnected ? "pulsing-indicator" : ""} />
          <span>{isConnected ? 'Telemetry Streaming (3s)' : 'Connecting...'}</span>
          {lastUpdated && <span style={{ color: 'var(--text-dim)' }}>• {new Date(lastUpdated).toLocaleTimeString()}</span>}
        </div>

        <div style={{
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          fontSize: '0.75rem',
          color: '#cbd5e1',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <ShieldCheck size={14} color="var(--primary)" />
          <span>Evidence-Based Pattern System</span>
        </div>
      </div>
    </header>
  );
}
