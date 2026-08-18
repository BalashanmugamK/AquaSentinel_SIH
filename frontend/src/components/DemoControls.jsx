import React, { useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, Cpu, RefreshCw } from 'lucide-react';

export default function DemoControls({ onTriggerScenario, activeScenario, isInjecting }) {
  return (
    <div className="glass-panel" style={{ padding: '14px 20px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--primary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Live Demo Scenarios:
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            (Trigger via Wokwi hardware knobs or fast-inject below)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <button
            className={`btn-action ${activeScenario === 'NORMAL' ? 'active' : ''}`}
            onClick={() => onTriggerScenario('normal')}
            disabled={isInjecting}
            style={{ borderColor: activeScenario === 'NORMAL' ? 'transparent' : 'rgba(16, 185, 129, 0.4)' }}
          >
            <CheckCircle2 size={15} color={activeScenario === 'NORMAL' ? '#04101e' : 'var(--status-normal)'} />
            <span>Scenario 1: Normal (🟢 Nominal)</span>
          </button>

          <button
            className={`btn-action ${activeScenario === 'DISTURBANCE' ? 'active' : ''}`}
            onClick={() => onTriggerScenario('disturbance')}
            disabled={isInjecting}
            style={{ borderColor: activeScenario === 'DISTURBANCE' ? 'transparent' : 'rgba(239, 68, 68, 0.4)' }}
          >
            <AlertTriangle size={15} color={activeScenario === 'DISTURBANCE' ? '#04101e' : 'var(--status-anomaly)'} />
            <span>Scenario 2: Disturbance (🔴 Turbidity+EC Spike)</span>
          </button>

          <button
            className={`btn-action ${activeScenario === 'SENSOR_FAULT' ? 'active' : ''}`}
            onClick={() => onTriggerScenario('sensor_fault')}
            disabled={isInjecting}
            style={{ borderColor: activeScenario === 'SENSOR_FAULT' ? 'transparent' : 'rgba(245, 158, 11, 0.4)' }}
          >
            <Cpu size={15} color={activeScenario === 'SENSOR_FAULT' ? '#04101e' : 'var(--status-fault)'} />
            <span>Scenario 3: Sensor Fault (🟡 Isolate pH)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
