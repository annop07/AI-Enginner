"use client";

import { useEffect, useMemo, useState } from "react";
import { IconCheck, IconChevronDown, IconSearch } from "@tabler/icons-react";
import { getModels } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

/** Family label for grouping: "qwen3.7-max" → "qwen", "gpt-5.1" → "gpt". */
function family(id: string): string {
  const head = id.split("-")[0];
  return head.replace(/[\d.]+$/, "") || head;
}

function groupModels(models: string[]): [string, string[]][] {
  const groups = new Map<string, string[]>();
  for (const id of models) {
    const key = family(id);
    const list = groups.get(key);
    if (list) list.push(id);
    else groups.set(key, [id]);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}

export function ModelPicker({
  value,
  onChange,
  disabled,
}: {
  /** Selected model id, or "" to use the backend default */
  value: string;
  onChange: (model: string) => void;
  disabled?: boolean;
}) {
  const [models, setModels] = useState<string[]>([]);
  const [fallback, setFallback] = useState("");
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await getModels();
        if (cancelled) return;
        setModels(res.models);
        setFallback(res.default);
      } catch {
        if (!cancelled) setError(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q ? models.filter((m) => m.toLowerCase().includes(q)) : models;
    return groupModels(filtered);
  }, [models, query]);

  // Show what will actually be charged — the pick, or the backend default.
  const shown = value || fallback || "default";

  return (
    <DropdownMenu onOpenChange={setOpen} open={open}>
      <DropdownMenuTrigger
        render={
          <Button
            aria-label={`Model: ${shown}. Change model`}
            className="h-7 max-w-45 gap-1 rounded-md px-2 font-mono font-normal text-xs"
            disabled={disabled || error}
            type="button"
            variant="ghost"
          />
        }
      >
        <span className="truncate">{error ? "models unavailable" : shown}</span>
        <IconChevronDown className="shrink-0 opacity-60" size={14} />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-72 rounded-2xl p-2">
        <div className="relative mb-2">
          <IconSearch
            className="-translate-y-1/2 absolute top-1/2 left-2 text-muted-foreground"
            size={14}
          />
          <Input
            autoFocus
            className="h-8 pl-7 text-xs"
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${models.length} models…`}
            value={query}
          />
        </div>

        <div className="max-h-72 overflow-y-auto">
          {groups.length === 0 && (
            <p className="px-2 py-6 text-center text-muted-foreground text-xs">
              No model matches “{query}”.
            </p>
          )}
          {groups.map(([label, ids]) => (
            <div className="mb-1" key={label}>
              <p className="px-2 py-1 font-medium text-[10px] text-muted-foreground uppercase tracking-wide">
                {label}
              </p>
              {ids.map((id) => (
                <button
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left font-mono text-xs transition-colors",
                    "hover:bg-accent focus-visible:bg-accent focus-visible:outline-none",
                    id === value && "bg-accent",
                  )}
                  key={id}
                  onClick={() => {
                    onChange(id);
                    setOpen(false);
                    setQuery("");
                  }}
                  type="button"
                >
                  <IconCheck
                    className={cn(
                      "shrink-0",
                      id === value ? "opacity-100" : "opacity-0",
                    )}
                    size={14}
                  />
                  <span className="truncate">{id}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
