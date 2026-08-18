import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import DemoControls from './components/DemoControls';
import StatusBanner from './components/StatusBanner';
import MetricCards from './components/MetricCards';
import TrendChart from './components/TrendChart';
import EventsFeed from './components/EventsFeed';
import AgentChat from './components/AgentChat';

export default function App() {
  const [latestReading, setLatestReading] = useState(null);
  const [history, setHistory] = useState({ count: 0, readings: [] });
  const [anomaly, setAnomaly] = useState(null);
  const [sensorHealth, setSensorHealth] = useState(null);
  const [events, setEvents] = useState([]);
  const [baseline, setBaseline] = useState(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeScenario, setActiveScenario] = useState('NORMAL');
  const [isInjecting, setIsInjecting] = useState(false);
  const [isWaitingAgent, setIsWaitingAgent] = useState(false);

  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'agent',
      text: '👋 Welcome to AquaSentinel Water Intelligence. I am actively monitoring Node AQUA-01. Click a prompt below or ask any question regarding water quality patterns.',
      provider: 'AquaSentinel Agent',
      toolsCalled: []
    }
  ]);

  // Fetch all backend telemetry and state
  const refreshSystemState = useCallback(async () => {
    try {
      // 1. Latest reading
      const rRes = await fetch('/api/readings/latest?device_id=AQUA-01');
      if (rRes.ok) {
        const rData = await rRes.json();
        setLatestReading(rData);
      }

      // 2. History
      const hRes = await fetch('/api/readings/history?device_id=AQUA-01&limit=25');
      if (hRes.ok) {
        const hData = await hRes.json();
        setHistory(hData);
      }

      // 3. Anomaly
      const aRes = await fetch('/api/anomalies/latest?device_id=AQUA-01');
      if (aRes.ok) {
        const aData = await aRes.json();
        setAnomaly(aData);
      }

      // 4. Health
      const sRes = await fetch('/api/health?device_id=AQUA-01');
      if (sRes.ok) {
        const sData = await sRes.json();
        setSensorHealth(sData);
      }

      // 5. Events
      const eRes = await fetch('/api/events?device_id=AQUA-01&limit=15');
      if (eRes.ok) {
        const eData = await eRes.json();
        setEvents(eData);
      }

      setIsConnected(true);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error("Error refreshing system state:", err);
      setIsConnected(false);
    }
  }, []);

  // Polling cycle every 3 seconds
  useEffect(() => {
    refreshSystemState();
    const interval = setInterval(refreshSystemState, 3000);
    return () => clearInterval(interval);
  }, [refreshSystemState]);

  // Handle Demo Scenario Injection
  const handleTriggerScenario = async (scenarioName) => {
    setIsInjecting(true);
    try {
      const res = await fetch(`/api/demo/scenario/${scenarioName}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setActiveScenario(data.scenario);
        await refreshSystemState();

        // Automatically prompt the agent to explain state change
        if (scenarioName === 'disturbance') {
          handleSendMessage("Why is this an anomaly? What happened?");
        } else if (scenarioName === 'sensor_fault') {
          handleSendMessage("Is this likely a sensor problem?");
        } else {
          handleSendMessage("How is my water?");
        }
      }
    } catch (err) {
      console.error(`Failed to trigger scenario ${scenarioName}:`, err);
    } finally {
      setIsInjecting(false);
    }
  };

  // Handle Chat Message
  const handleSendMessage = async (text) => {
    const userMsg = { sender: 'user', text };
    setChatMessages((prev) => [...prev, userMsg]);
    setIsWaitingAgent(true);

    try {
      const res = await fetch('/api/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: 'web-dashboard' })
      });

      if (res.ok) {
        const data = await res.json();
        const agentMsg = {
          sender: 'agent',
          text: data.response,
          provider: data.provider_used,
          toolsCalled: data.tools_called || []
        };
        setChatMessages((prev) => [...prev, agentMsg]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            sender: 'agent',
            text: '⚠️ Unable to process agent investigation. Please check backend connectivity.',
            provider: 'System Error',
            toolsCalled: []
          }
        ]);
      }
    } catch (err) {
      console.error("Agent error:", err);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: `⚠️ Network error communicating with agent endpoint: ${err.message}`,
          provider: 'Network Error',
          toolsCalled: []
        }
      ]);
    } finally {
      setIsWaitingAgent(false);
    }
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px 20px' }}>
      {/* 1. Header */}
      <Header isConnected={isConnected} lastUpdated={lastUpdated} />

      {/* 2. Demo Controls */}
      <DemoControls
        onTriggerScenario={handleTriggerScenario}
        activeScenario={activeScenario}
        isInjecting={isInjecting}
      />

      {/* 3. Status & Anomaly Banner */}
      <StatusBanner anomaly={anomaly} sensorHealth={sensorHealth} />

      {/* 4. Real-Time Telemetry Cards */}
      <MetricCards
        reading={latestReading}
        baseline={baseline}
        sensorHealth={sensorHealth}
      />

      {/* 5. Main Dashboard Split View */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Left Column: Trend Chart & Event Feed */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <TrendChart history={history} baseline={baseline} />
          <EventsFeed events={events} />
        </div>

        {/* Right Column: AI Investigation Chat */}
        <div style={{ height: '760px' }}>
          <AgentChat
            onSendMessage={handleSendMessage}
            isWaiting={isWaitingAgent}
            messages={chatMessages}
          />
        </div>
      </div>
    </div>
  );
}
