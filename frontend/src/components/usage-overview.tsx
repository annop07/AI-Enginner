"use client";

import type { UsageSummary } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const fmt = (n: number) => Math.round(n).toLocaleString();

/**
 * Raw totals as a compact inline strip. The radial cards (stats-07) carry the
 * visual weight, so these stay quiet — no boxes competing with them.
 */
export function MetricLine({ data }: { data: UsageSummary | null }) {
  const items = [
    { label: "requests", value: data ? fmt(data.total_requests) : "—" },
    { label: "tokens", value: data ? fmt(data.total_tokens) : "—" },
    {
      label: "avg latency",
      value: data ? `${fmt(data.avg_latency_ms)} ms` : "—",
    },
  ];
  return (
    <dl className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
      {items.map((it) => (
        <div className="flex items-baseline gap-1.5" key={it.label}>
          <dd className="font-medium font-mono text-foreground tabular-nums">
            {it.value}
          </dd>
          <dt className="text-muted-foreground">{it.label}</dt>
        </div>
      ))}
    </dl>
  );
}

export function RecentTable({ data }: { data: UsageSummary | null }) {
  const rows = data?.recent ?? [];
  return (
    <Card className="shadow-2xs">
      <CardHeader>
        <CardTitle className="font-medium text-foreground text-xl">
          Recent requests
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Endpoint</TableHead>
                <TableHead>Model</TableHead>
                <TableHead className="text-right">Prompt</TableHead>
                <TableHead className="text-right">Completion</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead className="text-right">Latency</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 && (
                <TableRow>
                  <TableCell
                    className="text-center text-muted-foreground"
                    colSpan={7}
                  >
                    No requests yet — send one above.
                  </TableCell>
                </TableRow>
              )}
              {rows.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="font-mono text-muted-foreground tabular-nums">
                    {e.ts.slice(11, 19)}
                  </TableCell>
                  <TableCell className="font-mono text-foreground">
                    {e.endpoint}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {e.model}
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground tabular-nums">
                    {fmt(e.prompt_tokens)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground tabular-nums">
                    {fmt(e.completion_tokens)}
                  </TableCell>
                  <TableCell className="text-right font-medium font-mono text-foreground tabular-nums">
                    {fmt(e.total_tokens)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground tabular-nums">
                    {fmt(e.latency_ms)} ms
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
