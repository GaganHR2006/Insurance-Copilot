import { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';

const now = () => new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

const WELCOME = {
  id: 1,
  role: 'ai',
  content: "Hello! I'm your Insurance Copilot. Upload a policy and ask me anything — coverage details, exclusions, claim procedures, or anything else.",
  time: now(),
};

export default function Chatbot() {
  const [messages, setMessages] = useState([WELCOME]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [policyContext, setPolicyContext] = useState(() => {
    return localStorage.getItem('insurance_policy_context') || '';
  });
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || isTyping) return;

    const userMsg = { id: Date.now(), role: 'user', content: text, time: now() };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, policy_context: policyContext }),
      });
      const data = await res.json();
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer || 'Sorry, I could not process that.',
        time: now(),
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: '⚠️ Could not reach the AI backend. Make sure the FastAPI server is running on port 8000.',
        time: now(),
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="page-enter flex flex-col" style={{ height: 'calc(100vh - 64px - 48px)' }}>
      {/* Optional policy context input */}
      <div className="shrink-0 mb-3">
        <input
          type="text"
          value={policyContext}
          onChange={e => setPolicyContext(e.target.value)}
          placeholder="Optional: paste your policy context here for more precise answers…"
          className="w-full rounded-xl px-4 py-2.5 text-sm font-dm bg-[#0D1322] border border-white/10 text-white focus:border-[#00D4AA] focus:outline-none placeholder:text-[#8892A4] transition-colors"
        />
      </div>

      {/* Message area */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex items-end gap-2 animate-fade-up ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'ai' && (
              <div
                className="flex items-center justify-center rounded-xl shrink-0 mb-1"
                style={{ width: 34, height: 34, background: 'rgba(0,212,170,0.15)', color: '#00D4AA' }}
              >
                <Bot size={17} />
              </div>
            )}

            <div className={`flex flex-col gap-1 max-w-[72%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`px-4 py-3 text-sm font-dm leading-relaxed ${msg.role === 'user'
                  ? 'rounded-2xl rounded-br-sm'
                  : 'rounded-2xl rounded-bl-sm'
                  }`}
                style={
                  msg.role === 'user'
                    ? { background: '#00D4AA', color: '#0A0F1E', fontWeight: 500 }
                    : { background: '#1A2235', color: '#F0F4FF', border: '1px solid rgba(255,255,255,0.06)' }
                }
              >
                {msg.role === 'ai' ? (
                  <div className="flex flex-col gap-1.5">
                    {msg.content.split('\n').filter(l => l.trim()).map((line, i) => {
                      const isBold = line.includes('<b>');
                      const clean = line.replace(/<\/?b>/g, '').replace(/^•\s*/, '');
                      return (
                        <div key={i} className="flex items-start gap-2">
                          <span style={{ color: '#00D4AA', flexShrink: 0, marginTop: 2 }}>•</span>
                          <span style={{ fontWeight: isBold ? 700 : 400, color: isBold ? '#F0F4FF' : '#C8D0E0' }}>
                            {clean}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  msg.content
                )}
              </div>
              <span className="text-[11px] font-dm px-1" style={{ color: '#8892A4' }}>{msg.time}</span>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-end gap-2 animate-fade-up">
            <div
              className="flex items-center justify-center rounded-xl shrink-0"
              style={{ width: 34, height: 34, background: 'rgba(0,212,170,0.15)', color: '#00D4AA' }}
            >
              <Bot size={17} />
            </div>
            <div
              className="flex items-center gap-1.5 px-4 py-3 rounded-2xl rounded-bl-sm"
              style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div
        className="shrink-0 flex items-center gap-3 px-4 py-3 mx-0 mt-2 rounded-2xl"
        style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.07)' }}
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about your policy…"
          className="flex-1 bg-transparent outline-none text-sm font-dm placeholder:font-dm"
          style={{ color: '#F0F4FF' }}
        />
        <button
          onClick={sendMessage}
          disabled={!inputText.trim() || isTyping}
          className="flex items-center justify-center rounded-xl transition-all duration-150 disabled:opacity-40"
          style={{ width: 40, height: 40, background: '#00D4AA', color: '#0A0F1E' }}
        >
          <Send size={17} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
