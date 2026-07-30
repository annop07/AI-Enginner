"use client";

import { useCallback, useEffect, useState } from "react";
import { IconChartDonut } from "@tabler/icons-react";
import { getHealth, getUsageSummary } from "@/lib/api";
import type { HealthResponse, UsageSummary } from "@/lib/types";
import { AskAgent } from "@/components/ask-agent";
import { MetricLine, RecentTable } from "@/components/usage-overview";
import Stats07, { type Stat07Item } from "@/components/stats-07";
import { Badge } from "@/components/ui/badge";

/**
 * Every ring is the same unit — share of all tokens spent — so the four cards
 * read as one scale: what the tokens were spent on, by type and by endpoint.
 */
function compose(data: UsageSummary | null): Stat07Item[] {
  const total = data?.total_tokens ?? 0;
  const pct = (n: number) => (total > 0 ? (n / total) * 100 : 0);

  const base: Stat07Item[] = [
    {
      name: "Prompt tokens",
      capacity: pct(data?.total_prompt_tokens ?? 0),
      current: data?.total_prompt_tokens ?? 0,
      allowed: total,
      unit: "tokens",
    },
    {
      name: "Completion tokens",
      capacity: pct(data?.total_completion_tokens ?? 0),
      current: data?.total_completion_tokens ?? 0,
      allowed: total,
      unit: "tokens",
    },
  ];

  const endpoints = (data?.by_endpoint ?? []).slice(0, 2).map((e) => ({
    name: e.endpoint,
    capacity: pct(e.total_tokens),
    current: e.total_tokens,
    allowed: total,
    unit: "tokens",
  }));

  return [...base, ...endpoints];
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const s = await getUsageSummary();
      setSummary(s);
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    // Initial load runs async so no state is set synchronously during the
    // effect, and `cancelled` stops updates landing after unmount.
    async function load() {
      try {
        const [h, s] = await Promise.all([getHealth(), getUsageSummary()]);
        if (cancelled) return;
        setHealth(h);
        setSummary(s);
        setOffline(false);
      } catch {
        if (!cancelled) setOffline(true);
      }
    }

    void load();
    const id = setInterval(() => void refresh(), 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [refresh]);

  return (
    <main className="mx-auto w-full max-w-6xl space-y-10 px-6 py-10 md:px-8 md:py-14">
      <header className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <IconChartDonut
              aria-hidden
              className="mt-0.5 shrink-0 text-muted-foreground"
              size={24}
              stroke={1.5}
            />
            <div>
              <h1 className="font-heading font-semibold text-2xl text-foreground tracking-tight">
                AI Usage
              </h1>
              <p className="mt-1 text-muted-foreground text-sm">
                Token consumption across the AI Agent Service
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {health && (
              <Badge className="font-normal" variant="outline">
                <span className="text-muted-foreground">default</span>
                <span className="ml-1.5 font-mono">{health.model}</span>
              </Badge>
            )}
            {offline && <Badge variant="destructive">backend offline</Badge>}
          </div>
        </div>
        <MetricLine data={summary} />
      </header>

      {offline && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm">
          Cannot reach the backend at{" "}
          <code className="font-mono">
            {process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}
          </code>
          . Start it with{" "}
          <code className="font-mono">
            uv run uvicorn app.main:app --port 8000
          </code>
          .
        </p>
      )}

      {/* Radial stat cards (shadcn block: @blocks-so/stats-07) */}
      <Stats07
        description="Share of all tokens spent, by type and by endpoint."
        items={compose(summary)}
        title="Token composition"
      />

      <AskAgent onDone={refresh} />

      <RecentTable data={summary} />
    </main>
  );
}
