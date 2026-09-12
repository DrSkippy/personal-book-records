import { apiClient } from './client';

export interface ChatHistoryMessage {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_call_id?: string;
  tool_calls?: Array<{
    id: string;
    type: 'function';
    function: { name: string; arguments: string };
  }>;
}

export type ChatTraceEvent =
  | { type: 'assistant'; content: string }
  | {
      type: 'tool';
      toolCallId?: string;
      toolName: string;
      toolArgs: Record<string, unknown>;
      toolResult: unknown;
    };

export interface ChatResponse {
  history: ChatHistoryMessage[];
  trace: ChatTraceEvent[];
}

/**
 * Send the running conversation (sans system prompt, which the backend
 * owns) to the server-side AI Chat endpoint. The backend runs the full
 * tool-calling loop against ai_agent.chat_host/chat_model/chat_api_key and
 * returns the updated history plus a display trace of what happened.
 */
export const sendChatMessage = (history: ChatHistoryMessage[]): Promise<ChatResponse> =>
  apiClient.post<ChatResponse>('/chat', { messages: history }).then(r => r.data);
