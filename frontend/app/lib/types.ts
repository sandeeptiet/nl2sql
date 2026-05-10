export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface QueryResponse {
  nl_summary: string;
  table: Record<string, unknown>[];
  columns: string[];
  sql: string;
  query_type: string;
  row_count: number;
  latency_ms: number;
  chart_type: "bar" | "line" | null;
  error: string | null;
  transpiled_sql?: string | null;
  transpiled_dialect?: string | null;
}

export interface BotMessage {
  type: "bot";
  response: QueryResponse;
}

export interface UserMessage {
  type: "user";
  content: string;
}

export type Message = UserMessage | BotMessage;
