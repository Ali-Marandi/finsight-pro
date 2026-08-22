import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Trash2, Settings, AlertCircle } from 'lucide-react';
import { getApiClient } from '../lib/api';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import Spinner from '../components/Spinner';

interface ChatMsg {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  modelUsed?: string;
}

const SUGGESTED_QUESTIONS = [
  { en: 'What\'s the overall financial health?', fa: 'وضعیت کلی مالی چطوره؟' },
  { en: 'Which ratios need attention?', fa: 'کدام نسبت‌ها مشکل دارن؟' },
  { en: 'Give me improvement suggestions', fa: 'پیشنهاد بهبود بده' },
  { en: 'What\'s the bankruptcy risk?', fa: 'ریسک ورشکستگی چقدره؟' },
  { en: 'Analyze profitability', fa: 'سودآوری رو تحلیل کن' },
  { en: 'Check liquidity position', fa: 'وضعیت نقدینگی رو بررسی کن' },
];

function parseMarkdown(text: string): string {
  // Basic markdown rendering to HTML
  let html = text
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-cascade-charcoal mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-cascade-charcoal mt-4 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-cascade-charcoal mt-4 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-cascade-charcoal">$1</strong>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 text-cascade-charcoal/80">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 text-cascade-charcoal/80">$1</li>')
    .replace(/\n- /g, '\n<li class="ml-4 text-cascade-charcoal/80">')
    .replace(/\n(\d+\. )/g, '\n<li class="ml-4 text-cascade-charcoal/80">$1')
    .replace(/→ (.+)$/gm, '&nbsp;&nbsp;→ <span class="text-cascade-gold">$1</span>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
  
  // Emoji indicators
  html = html.replace(/🟢/g, '<span class="text-emerald-500">&#x1F7E2;</span>');
  html = html.replace(/🟡/g, '<span class="text-amber-500">&#x1F7E1;</span>');
  html = html.replace(/🔴/g, '<span class="text-red-500">&#x1F534;</span>');
  
  return html;
}

export default function AICopilot() {
  const { currentAnalysis, analyses } = useAnalysisStore();
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>(
    currentAnalysis?.analysisId || ''
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update selected analysis when current changes
  useEffect(() => {
    if (currentAnalysis?.analysisId && !selectedAnalysisId) {
      setSelectedAnalysisId(currentAnalysis.analysisId);
    }
  }, [currentAnalysis]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMsg = { role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const client = await getApiClient();
      const { data } = await client.post('/ai/chat', {
        message: text.trim(),
        analysis_id: selectedAnalysisId || null,
        conversation_history: messages.map((m) => ({ role: m.role, content: m.content })),
      });

      const aiMsg: ChatMsg = {
        role: 'assistant',
        content: data.response || 'No response received.',
        sources: data.sources || [],
        modelUsed: data.model_used || 'unknown',
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const aiMsg: ChatMsg = {
        role: 'assistant',
        content: `Connection error: ${err.message || 'Cannot reach AI service'}. Make sure the backend API is running.`,
        sources: [],
        modelUsed: 'error',
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cascade-gold to-amber-600 rounded-xl flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">AI Financial Copilot</h1>
            <p className="text-xs text-cascade-sage">
              {selectedAnalysisId ? `Analyzing: ${currentAnalysis?.companyName || 'Selected Analysis'}` : 'No analysis selected — ask general questions'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Analysis selector */}
          {analyses.length > 0 && (
            <select
              value={selectedAnalysisId}
              onChange={(e) => setSelectedAnalysisId(e.target.value)}
              className="text-xs bg-white border border-cascade-mist rounded-lg px-3 py-2 text-cascade-charcoal focus:outline-none focus:ring-2 focus:ring-cascade-gold/30"
            >
              <option value="">No context (general)</option>
              {analyses.map((a) => (
                <option key={a.analysisId} value={a.analysisId}>
                  {a.companyName} — {a.period}
                </option>
              ))}
            </select>
          )}
          <button
            onClick={clearChat}
            className="p-2 text-cascade-sage hover:text-cascade-charcoal hover:bg-cascade-mist rounded-lg transition-colors"
            title="Clear chat"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto rounded-xl bg-white border border-cascade-mist p-4 space-y-4 scrollbar-thin">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-cascade-gold/10 rounded-2xl flex items-center justify-center mb-4">
              <Bot size={32} className="text-cascade-gold" />
            </div>
            <h3 className="text-lg font-semibold text-cascade-charcoal mb-2">Financial AI Assistant</h3>
            <p className="text-sm text-cascade-sage max-w-md mb-6">
              Ask me anything about financial statements, ratios, predictions, or get actionable insights.
              <br />
              <span className="text-xs">Works built-in or connect your own LLM in Settings.</span>
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q.en)}
                  className="text-left text-xs px-3 py-2.5 bg-cascade-stone hover:bg-cascade-mist rounded-lg text-cascade-charcoal/70 hover:text-cascade-charcoal transition-colors border border-transparent hover:border-cascade-mist"
                >
                  {q.en}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 bg-gradient-to-br from-cascade-gold to-amber-600 rounded-lg flex items-center justify-center shrink-0 mt-1">
                <Bot size={16} className="text-white" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-cascade-charcoal text-white rounded-tr-md'
                  : 'bg-cascade-stone text-cascade-charcoal rounded-tl-md border border-cascade-mist'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }}
                />
              ) : (
                msg.content
              )}
              {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-cascade-mist/50">
                  <span className="text-[10px] text-cascade-sage">
                    Source: {msg.sources.join(', ')}
                    {msg.modelUsed !== 'rule-based' && ` | Model: ${msg.modelUsed}`}
                  </span>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 bg-cascade-charcoal/10 rounded-lg flex items-center justify-center shrink-0 mt-1">
                <User size={16} className="text-cascade-charcoal/60" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 items-start">
            <div className="w-8 h-8 bg-gradient-to-br from-cascade-gold to-amber-600 rounded-lg flex items-center justify-center shrink-0">
              <Bot size={16} className="text-white" />
            </div>
            <div className="bg-cascade-stone border border-cascade-mist rounded-2xl rounded-tl-md px-4 py-3">
              <div className="flex items-center gap-2 text-cascade-sage">
                <Spinner size={16} />
                <span className="text-xs">Analyzing financial data...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about financial health, ratios, predictions..."
          rows={2}
          className="w-full bg-white border border-cascade-mist rounded-xl px-4 py-3 pr-12 text-sm text-cascade-charcoal placeholder-cascade-sage focus:outline-none focus:ring-2 focus:ring-cascade-gold/30 resize-none scrollbar-thin"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-3 bottom-3 w-8 h-8 bg-cascade-gold hover:bg-cascade-gold/90 disabled:bg-cascade-mist disabled:text-cascade-sage text-white rounded-lg flex items-center justify-center transition-colors"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
