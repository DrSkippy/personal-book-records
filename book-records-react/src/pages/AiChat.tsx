import { useState, useRef } from 'react';
import PageLayout from '../components/layout/PageLayout';
import ChatInterface from '../components/chat/ChatInterface';
import type { ChatMessage } from '../types';
import { Send, Trash2, FileText, AlignLeft } from 'lucide-react';
import { ollamaChat, executeTool } from '../api/ollama';
import type { OllamaMessage } from '../api/ollama';

const SYSTEM_PROMPT = `You are a helpful assistant for a personal book collection. You can search books, look up reading history, tags, and estimates using the tools provided. Be concise and friendly.`;

export default function AiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [markdownEnabled, setMarkdownEnabled] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  // Maintain the full Ollama-format history (includes assistant tool_call messages)
  const ollamaHistoryRef = useRef<OllamaMessage[]>([
    { role: 'system', content: SYSTEM_PROMPT },
  ]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    let displayMessages: ChatMessage[] = [...messages, userMsg];
    setMessages(displayMessages);
    setInput('');
    setIsLoading(true);

    // Append user message to Ollama history
    ollamaHistoryRef.current.push({ role: 'user', content: text });

    try {
      const MAX_ITERATIONS = 10;
      let iterations = 0;

      while (iterations < MAX_ITERATIONS) {
        iterations++;

        const response = await ollamaChat(ollamaHistoryRef.current);
        const msg = response.choices[0].message;

        if (msg.tool_calls && msg.tool_calls.length > 0) {
          // Record the assistant's tool_calls turn in Ollama history
          ollamaHistoryRef.current.push({
            role: 'assistant',
            content: msg.content ?? '',
            tool_calls: msg.tool_calls,
          });

          // Execute each tool call sequentially
          for (const tc of msg.tool_calls) {
            const toolName = tc.function.name;
            const toolArgs = JSON.parse(tc.function.arguments || '{}') as Record<string, unknown>;
            const toolResultStr = await executeTool(toolName, toolArgs);
            let toolResult: unknown;
            try {
              toolResult = JSON.parse(toolResultStr);
            } catch {
              toolResult = toolResultStr;
            }

            // Add tool result to display
            const toolMsg: ChatMessage = {
              id: `tool-${Date.now()}-${tc.id}`,
              role: 'tool',
              content: '',
              toolCallId: tc.id,
              toolName,
              toolArgs,
              toolResult,
            };
            displayMessages = [...displayMessages, toolMsg];
            setMessages(displayMessages);

            // Add tool result to Ollama history
            ollamaHistoryRef.current.push({
              role: 'tool',
              content: toolResultStr,
              tool_call_id: tc.id,
            });
          }

          // Loop back to get the next response
          continue;
        }

        // No tool calls — this is the final assistant reply
        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: msg.content ?? 'No response.',
        };
        displayMessages = [...displayMessages, assistantMsg];
        setMessages(displayMessages);

        // Record in Ollama history for future turns
        ollamaHistoryRef.current.push({
          role: 'assistant',
          content: msg.content ?? '',
        });
        break;
      }
    } catch (err) {
      console.error('[AiChat] Ollama error:', err);
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, the AI backend is unavailable. Please check the Ollama server and try again.',
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
    ollamaHistoryRef.current = [{ role: 'system', content: SYSTEM_PROMPT }];
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
          Powered by Ollama ({import.meta.env.VITE_OLLAMA_MODEL}) — reads your book collection via API tools.
        </p>
      </div>
    </PageLayout>
  );
}
