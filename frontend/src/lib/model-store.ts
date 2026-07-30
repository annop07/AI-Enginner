/**
 * The selected model, persisted in localStorage.
 *
 * Exposed as an external store rather than effect-synced state: the server has
 * no localStorage, so `getServerSnapshot` returns "" and the client swaps in the
 * stored value on hydration without a cascading render.
 *
 * "" means "let the backend use its default model".
 */
const KEY = "ai-usage:model";

let listeners: (() => void)[] = [];

export function subscribeModel(callback: () => void): () => void {
  listeners = [...listeners, callback];
  // Keep other tabs in sync too.
  window.addEventListener("storage", callback);
  return () => {
    listeners = listeners.filter((l) => l !== callback);
    window.removeEventListener("storage", callback);
  };
}

export function getModelSnapshot(): string {
  return localStorage.getItem(KEY) ?? "";
}

export function getModelServerSnapshot(): string {
  return "";
}

export function setStoredModel(model: string): void {
  localStorage.setItem(KEY, model);
  for (const l of listeners) l();
}
