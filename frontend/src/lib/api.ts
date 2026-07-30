// Thin typed client for the FastAPI backend.
import type {
  ChatResponse,
  HealthResponse,
  ModelsResponse,
  UsageSummary,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${detail.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return json(await fetch(`${BASE}/health`, { cache: "no-store" }));
}

export async function getUsageSummary(): Promise<UsageSummary> {
  return json(await fetch(`${BASE}/usage/summary`, { cache: "no-store" }));
}

export async function getModels(): Promise<ModelsResponse> {
  return json(await fetch(`${BASE}/models`, { cache: "no-store" }));
}

export async function sendChat(
  message: string,
  model?: string,
): Promise<ChatResponse> {
  return json(
    await fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Omit `model` entirely when unset so the backend uses its default.
      body: JSON.stringify(model ? { message, model } : { message }),
    }),
  );
}
