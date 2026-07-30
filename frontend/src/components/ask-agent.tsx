"use client";

import { useRef, useState, useSyncExternalStore } from "react";
import { IconLoader2 } from "@tabler/icons-react";
import { sendChat } from "@/lib/api";
import {
  getModelServerSnapshot,
  getModelSnapshot,
  setStoredModel,
  subscribeModel,
} from "@/lib/model-store";
import type { ChatResponse } from "@/lib/types";
import Ai04 from "@/components/ai-04";
import { Card, CardContent } from "@/components/ui/card";

const fmt = (n: number) => n.toLocaleString();

export function AskAgent({ onDone }: { onDone?: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);
  // "" means "let the backend use its default model".
  const model = useSyncExternalStore(
    subscribeModel,
    getModelSnapshot,
    getModelServerSnapshot,
  );
  // `loading` state updates asynchronously, so rapid submits can slip past it
  // and fire concurrent LLM calls (each one costs tokens). A ref flips
  // synchronously, so it actually blocks the second submit.
  const inFlight = useRef(false);

  async function ask(prompt: string) {
    if (!prompt.trim() || inFlight.current) return;
    inFlight.current = true;
    setLoading(true);
    setError(null);
    try {
      const res = await sendChat(prompt.trim(), model || undefined);
      setResult(res);
      onDone?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Prompt input (shadcn block: @blocks-so/ai-04) */}
      <Ai04 model={model} onModelChange={setStoredModel} onSubmit={ask} />

      {/* Status */}
      <div aria-live="polite" className="text-center text-sm">
        {loading && (
          <span className="inline-flex items-center gap-2 text-muted-foreground">
            <IconLoader2 className="animate-spin motion-reduce:animate-none" size={14} />
            Thinking…
          </span>
        )}
        {!loading && error && <span className="text-destructive">{error}</span>}
        {!loading && !error && result && (
          <span className="text-muted-foreground">
            <span className="font-mono text-foreground">{result.model}</span>
            {" answered in "}
            {result.iterations} iteration
            {result.iterations === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {/* Result: token cost + tool calls + answer */}
      {result && !loading && (
        <Card className="mx-auto max-w-2xl shadow-2xs">
          <CardContent className="space-y-5">
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Prompt" value={fmt(result.usage.prompt_tokens)} />
              <Stat
                label="Completion"
                value={fmt(result.usage.completion_tokens)}
              />
              <Stat label="Total" value={fmt(result.usage.total_tokens)} />
              <Stat label="LLM calls" value={fmt(result.usage.llm_calls)} />
            </dl>

            {result.tool_calls.length > 0 && (
              <div className="space-y-1 border-border border-t pt-4">
                {result.tool_calls.map((t, i) => (
                  <div
                    className="truncate font-mono text-muted-foreground text-xs"
                    key={i}
                    title={`${t.tool}(${JSON.stringify(t.arguments)})`}
                  >
                    <span className="text-foreground">{t.tool}</span>
                    {`(${JSON.stringify(t.arguments)})`}
                  </div>
                ))}
              </div>
            )}

            <p className="whitespace-pre-wrap text-pretty text-foreground text-sm leading-6">
              {result.answer}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted-foreground text-xs">{label}</dt>
      <dd className="font-medium font-mono text-foreground text-lg tabular-nums">
        {value}
      </dd>
    </div>
  );
}
