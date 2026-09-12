import { useState, useRef } from 'react';
import PageLayout from '../components/layout/PageLayout';
import ChatInterface from '../components/chat/ChatInterface';
import type { ChatMessage } from '../types';
import { Send, Trash2, FileText, AlignLeft } from 'lucide-react';
import { sendChatMessage } from '../api/chat';
import type { ChatHistoryMessage } from '../api/chat';

export default function AiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [markdownEnabled, setMarkdownEnabled] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const historyRef = useRef<ChatHistoryMessage[]>([]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    historyRef.current = [...historyRef.current, { role: 'user', content: text }];

    try {
      const { history, trace } = await sendChatMessage(historyRef.current);
      historyRef.current = history;

      const newMessages: ChatMessage[] = trace.map((event, i) =>
        event.type === 'tool'
          ? {
              id: `tool-${Date.now()}-${i}`,
              role: 'tool',
              content: '',
              toolCallId: event.toolCallId,
              toolName: event.toolName,
              toolArgs: event.toolArgs,
              toolResult: event.toolResult,
            }
          : {
              id: `assistant-${Date.now()}-${i}`,
              role: 'assistant',
              content: event.content,
            }
      );
      setMessages((prev) => [...prev, ...newMessages]);
    } catch (err) {
      console.error('[AiChat] chat request failed:', err);
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, the AI backend is unavailable. Please try again shortly.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleClear = () => {
    setMessages([]);
    setInput('');
    historyRef.current = [];
  };

  return (
    <PageLayout>
      <div className="space-y-4 max-w-3xl mx-auto">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">
            AI Book Assistant
          </h1>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMarkdownEnabled((v) => !v)}
              title={markdownEnabled ? 'Switch to plain text' : 'Switch to Markdown'}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm border transition-colors ${
                markdownEnabled
                  ? 'bg-primary text-white border-primary hover:bg-umber'
                  : 'bg-surface text-slate border-gray-300 hover:bg-gray-200'
              }`}
            >
              {markdownEnabled ? <FileText size={15} /> : <AlignLeft size={15} />}
              {markdownEnabled ? 'MD' : 'TXT'}
            </button>
            <button
              onClick={handleClear}
              className="flex items-center gap-2 bg-surface border border-gray-300 text-slate px-4 py-2 rounded-lg text-sm hover:bg-gray-200"
            >
              <Trash2 size={16} /> Clear
            </button>
          </div>
        </div>

        <ChatInterface messages={messages} isLoading={isLoading} markdownEnabled={markdownEnabled} />

        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about your book collection..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="flex items-center gap-2 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
          >
            <Send size={16} /> Send
          </button>
        </div>

        <p className="text-xs text-slate text-center">
          Reads your book collection via API tools.
        </p>
      </div>
    </PageLayout>
  );
}
