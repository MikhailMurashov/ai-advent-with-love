export interface User {
  id: string
  username: string
  created_at: string
}

export interface SessionInfo {
  id: string
  user_id: string
  title: string
  strategy_type: string
  model_key: string
  system_prompt: string
  created_at: string
  updated_at: string
}

export interface CreateSessionParams {
  user_id: string
  model_key: string
  strategy_type: string
  system_prompt: string
  title: string
  id?: string
}

export interface DbMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  tool_calls: string | null
  tokens_prompt: number | null
  tokens_completion: number | null
  elapsed_s: number | null
  created_at: string
}

export interface TokenStats {
  prompt_tokens: number
  completion_tokens: number
  elapsed_s: number
}

export type DisplayMessage =
  | { kind: 'message'; role: 'user' | 'assistant'; content: string; stats?: TokenStats }
  | { kind: 'tool_step'; name: string; args: object; result: string; toolCallId: string }

export interface WsTokenEvent {
  type: 'token'
  content: string
}

export interface WsToolStepEvent {
  type: 'tool_step'
  name: string
  args: object
  tool_call_id: string
  content: string
}

export interface WsDoneEvent {
  type: 'done'
  stats: TokenStats
}

export interface WsErrorEvent {
  type: 'error'
  message: string
}

export interface WsNotificationEvent {
  type: 'notification'
  content: string
}

export type WsServerEvent = WsTokenEvent | WsToolStepEvent | WsDoneEvent | WsErrorEvent | WsNotificationEvent

export interface WsSendPayload {
  content: string
  params?: {
    model?: string
    temperature?: number
  }
}

export interface MCPServer {
  id: string
  name: string
  url: string
  description: string
  enabled: boolean
  created_at: string
}

export interface CreateMCPServerParams {
  name: string
  url: string
  description: string
  enabled: boolean
}

export interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}
