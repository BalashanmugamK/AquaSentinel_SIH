import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Sparkles, ChevronDown, ChevronUp, Wrench, ShieldAlert } from 'lucide-react';

export default function AgentChat({ onSendMessage, isWaiting, messages }) {
  const [inputMessage, setInputMessage] = useState('');
  const [expandedTools, setExpandedTools] = useState({});
  const chatEndRef = useRef(null);

  const quickPrompts = [
    "How is my water?",
    "Why is this an anomaly?",
    "Is this likely a sensor problem?",
    "What should I do?"
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isWaiting) return;
    onSendMessage(inputMessage);
    setInputMessage('');
  };

  const handleQuickPrompt = (prompt) => {
    if (isWaiting) return;
    onSendMessage(prompt);
  };

  const toggleToolView = (msgIndex) => {
    setExpandedTools(prev => ({ ...prev, [msgIndex]: !prev[msgIndex] }));
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isWaiting]);

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Chat Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(0, 210, 255, 0.15)' }}>
            <Bot size={18} color="var(--primary)" />
          </div>
          <div>
            <h3 className="font-heading" style={{ fontSize: '1rem', fontWeight: '600', color: '#fff' }}>
              Sarvam AI Investigation Agent
            </h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Orchestrated via 6 Read-Only Tools (Grounded Water Intelligence)
            </span>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '420px', paddingRight: '4px', marginBottom: '12px' }}>
        {messages.map((msg, index) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={index}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isUser ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                maxWidth: '92%',
                borderRadius: '12px',
                padding: '12px 16px',
                background: isUser ? 'var(--primary-gradient)' : 'rgba(15, 23, 42, 0.85)',
                border: `1px solid ${isUser ? 'transparent' : 'rgba(0, 210, 255, 0.2)'}`,
                color: isUser ? '#04101e' : '#f1f5f9',
                fontSize: '0.85rem',
                lineHeight: '1.45',
                boxShadow: isUser ? '0 4px 14px rgba(0, 210, 255, 0.25)' : 'none'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', opacity: 0.85, fontSize: '0.75rem', fontWeight: '600' }}>
                  {isUser ? <User size={13} /> : <Bot size={13} color="var(--primary)" />}
                  <span>{isUser ? 'You' : 'AquaSentinel Agent'}</span>
                  {!isUser && msg.provider && (
                    <span style={{ marginLeft: 'auto', fontSize: '0.65rem', padding: '1px 5px', borderRadius: '4px', background: 'rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                      {msg.provider}
                    </span>
                  )}
                </div>

                <div style={{ whiteSpace: 'pre-wrap' }}>
                  {msg.text}
                </div>

                {/* Inspect Tools Accordion */}
                {!isUser && msg.toolsCalled && msg.toolsCalled.length > 0 && (
                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                    <button
                      onClick={() => toggleToolView(index)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--primary)',
                        fontSize: '0.72rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: 0
                      }}
                    >
                      <Wrench size={11} />
                      <span>{expandedTools[index] ? 'Hide' : 'Inspect'} 6 Grounded Tools ({msg.toolsCalled.length} called)</span>
                      {expandedTools[index] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>

                    {expandedTools[index] && (
                      <div style={{
                        marginTop: '6px',
                        padding: '8px',
                        borderRadius: '6px',
                        background: 'rgba(0,0,0,0.4)',
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {msg.toolsCalled.map((tool, tIdx) => (
                          <div key={tIdx} style={{ marginBottom: '4px', color: '#93c5fd' }}>
                            ✓ <strong>{tool.tool_name}()</strong>: <span style={{ color: '#cbd5e1' }}>{JSON.stringify(tool.output_summary)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isWaiting && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary)', fontSize: '0.8rem', padding: '8px' }}>
            <Sparkles size={16} className="pulsing-indicator" />
            <span>Agent investigating tools & telemetry evidence...</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Quick Prompts Pills */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '10px' }}>
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => handleQuickPrompt(qp)}
            disabled={isWaiting}
            style={{
              background: 'rgba(0, 210, 255, 0.08)',
              border: '1px solid rgba(0, 210, 255, 0.25)',
              color: 'var(--primary)',
              fontSize: '0.72rem',
              padding: '4px 8px',
              borderRadius: '6px',
              cursor: isWaiting ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(0, 210, 255, 0.2)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'rgba(0, 210, 255, 0.08)'}
          >
            "{qp}"
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask water question (e.g., 'Why is this an anomaly?')"
          disabled={isWaiting}
          style={{
            flex: 1,
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#fff',
            fontSize: '0.85rem',
            outline: 'none'
          }}
          onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
          onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
        />
        <button
          type="submit"
          disabled={isWaiting || !inputMessage.trim()}
          style={{
            background: 'var(--primary-gradient)',
            border: 'none',
            borderRadius: '8px',
            padding: '0 16px',
            color: '#04101e',
            fontWeight: '600',
            cursor: isWaiting || !inputMessage.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 12px var(--primary-glow)'
          }}
        >
          <Send size={16} />
        </button>
      </form>

      {/* Scientific Disclaimer Footer */}
      <div style={{
        marginTop: '12px',
        padding: '8px 10px',
        borderRadius: '6px',
        background: 'rgba(0,0,0,0.35)',
        border: '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '0.68rem',
        color: 'var(--text-dim)'
      }}>
        <ShieldAlert size={12} color="var(--primary)" style={{ flexShrink: 0 }} />
        <span>The system detects anomalous patterns and generates evidence-based early warnings without claiming specific unverified contaminants.</span>
      </div>
    </div>
  );
}
