// Types mirroring the FastAPI backend schemas (app/schemas.py).

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  llm_calls: number;
}

export interface ToolCallTrace {
  tool: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

export interface ChatResponse {
  answer: string;
  tool_calls: ToolCallTrace[];
  iterations: number;
  usage: TokenUsage;
  /** Model that actually answered */
  model: string;
}

export interface ModelsResponse {
  /** Model used when a request doesn't specify one */
  default: string;
  models: string[];
}

export interface ModelUsage {
  model: string;
  requests: number;
  total_tokens: number;
}

export interface EndpointUsage {
  endpoint: string;
  requests: number;
  total_tokens: number;
}

export interface TimePoint {
  bucket: string;
  total_tokens: number;
  requests: number;
}

export interface UsageEvent {
  id: number;
  ts: string;
  endpoint: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  llm_calls: number;
  latency_ms: number;
}

export interface UsageSummary {
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  avg_latency_ms: number;
  by_model: ModelUsage[];
  by_endpoint: EndpointUsage[];
  timeseries: TimePoint[];
  recent: UsageEvent[];
}

export interface HealthResponse {
  status: string;
  model: string;
  openai_configured: boolean;
  vector_documents: number;
  tools: string[];
}
