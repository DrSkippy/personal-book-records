import { useRef, useEffect } from 'react';
import type { ChatMessage } from '../../types';
import ToolCallResult from './ToolCallResult';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  markdownEnabled: boolean;
}

const mdComponents: React.ComponentProps<typeof ReactMarkdown>['components'] = {
  p:          ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong:     ({ children }) => <strong className="font-semibold">{children}</strong>,
  em:         ({ children }) => <em className="italic">{children}</em>,
  ul:         ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
  ol:         ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>,
  li:         ({ children }) => <li className="leading-snug">{children}</li>,
  h1:         ({ children }) => <h1 className="text-base font-bold mb-1 mt-2">{children}</h1>,
  h2:         ({ children }) => <h2 className="text-sm font-bold mb-1 mt-2">{children}</h2>,
  h3:         ({ children }) => <h3 className="text-sm font-semibold mb-1 mt-1">{children}</h3>,
  code:       ({ children, className }) =>
    className
      ? <code className="block bg-white/60 rounded px-2 py-1 text-xs font-mono overflow-x-auto mb-2">{children}</code>
      : <code className="bg-white/60 rounded px-1 text-xs font-mono">{children}</code>,
  pre:        ({ children }) => <pre className="mb-2">{children}</pre>,
  blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/50 pl-3 italic opacity-80 mb-2">{children}</blockquote>,
  a:          ({ href, children }) => <a href={href} className="underline hover:opacity-80" target="_blank" rel="noreferrer">{children}</a>,
  hr:         () => <hr className="border-slate/20 my-2" />,
  table:      ({ children }) => <div className="overflow-x-auto mb-2"><table className="text-xs border-collapse w-full">{children}</table></div>,
  thead:      ({ children }) => <thead className="bg-primary/20">{children}</thead>,
  tbody:      ({ children }) => <tbody>{children}</tbody>,
  tr:         ({ children }) => <tr className="border-b border-gray-200 even:bg-white/40">{children}</tr>,
  th:         ({ children }) => <th className="px-2 py-1 text-left font-semibold border border-gray-200">{children}</th>,
  td:         ({ children }) => <td className="px-2 py-1 border border-gray-200">{children}</td>,
};

export default function ChatInterface({ messages, isLoading, markdownEnabled }: ChatInterfaceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white rounded-xl border border-gray-200 min-h-96 max-h-[60vh]">
      {messages.map((msg) => {
        if (msg.role === 'tool') {
          return (
            <ToolCallResult
              key={msg.id}
              toolName={msg.toolName || 'tool'}
              args={msg.toolArgs}
              result={msg.toolResult}
            />
          );
        }
        return (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
            )}
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-secondary text-white rounded-br-sm'
                  : 'bg-surface text-slate rounded-bl-sm'
              }`}
            >
              {msg.role === 'assistant' && markdownEnabled
                ? <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{msg.content}</ReactMarkdown>
                : msg.content}
            </div>
            {msg.role === 'user' && (
              <div className="shrink-0 w-8 h-8 bg-umber rounded-full flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
            )}
          </div>
        );
      })}
      {isLoading && (
        <div className="flex gap-3 justify-start">
          <div className="shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <div className="bg-surface px-4 py-3 rounded-2xl rounded-bl-sm">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-slate rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-slate rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-slate rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
