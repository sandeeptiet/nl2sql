export interface SchemaColumn {
  name: string;
  type: string;
  description: string | null;
  is_sensitive: boolean;
}

export interface SchemaTable {
  table: string;
  columns: SchemaColumn[];
  foreign_keys: unknown[];
}

export interface FewShotExample {
  id: number;
  question: string;
  sql: string;
  query_type: string | null;
  created_at: string;
}

export interface QueryLog {
  id: number;
  nl_input: string;
  generated_sql: string | null;
  query_type: string | null;
  status: string;
  latency_ms: number | null;
  row_count: number | null;
  error_msg: string | null;
  created_at: string;
}

export interface Guardrail {
  operation: string;
  is_blocked: boolean;
}

export interface ModelConfig {
  llm_provider: string;
  model_name: string;
  temperature: number;
  dialect: string;
  max_tokens: number;
}
