"use client";

import { useState, useEffect } from "react";
import { ModelConfig } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PROVIDERS = ["anthropic", "openai"];
const MODELS: Record<string, string[]> = {
  anthropic: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
  openai:    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
};
const DIALECTS = ["mysql", "postgresql", "sqlite", "mssql"];

export default function ConfigPage() {
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/admin/config`)
      .then((r) => r.json())
      .then((d) => setConfig(d))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    if (!config) return;
    setSaving(true);
    await fetch(`${API_BASE}/api/v1/admin/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function update<K extends keyof ModelConfig>(key: K, value: ModelConfig[K]) {
    setConfig((prev) => prev ? { ...prev, [key]: value } : prev);
    setSaved(false);
  }

  if (loading || !config) return <p className="text-sm text-gray-400">Loading…</p>;

  const availableModels = MODELS[config.llm_provider] ?? [];

  return (
    <div className="max-w-md">
      <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-6">Model Config</h1>

      <div className="space-y-5">
        {/* LLM Provider */}
        <Field label="LLM Provider">
          <select
            value={config.llm_provider}
            onChange={(e) => {
              const p = e.target.value;
              update("llm_provider", p);
              update("model_name", MODELS[p]?.[0] ?? "");
            }}
            className={selectCls}
          >
            {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </Field>

        {/* Model Name */}
        <Field label="Model Name">
          <select
            value={config.model_name}
            onChange={(e) => update("model_name", e.target.value)}
            className={selectCls}
          >
            {availableModels.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </Field>

        {/* Dialect */}
        <Field label="SQL Dialect">
          <select
            value={config.dialect}
            onChange={(e) => update("dialect", e.target.value)}
            className={selectCls}
          >
            {DIALECTS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>

        {/* Temperature */}
        <Field label={`Temperature — ${config.temperature.toFixed(1)}`}>
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={config.temperature}
            onChange={(e) => update("temperature", parseFloat(e.target.value))}
            className="w-full accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0 — precise</span>
            <span>1 — creative</span>
          </div>
        </Field>

        {/* Max Tokens */}
        <Field label="Max Tokens">
          <input
            type="number"
            min={100}
            max={8000}
            step={100}
            value={config.max_tokens}
            onChange={(e) => update("max_tokens", parseInt(e.target.value, 10))}
            className={inputCls}
          />
          <p className="text-xs text-gray-400 mt-1">Max tokens for SQL generation response (100–8000)</p>
        </Field>
      </div>

      <div className="mt-8 flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg"
        >
          {saving ? "Saving…" : "Save Changes"}
        </button>
        {saved && <span className="text-sm text-green-600">Saved!</span>}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}
      </label>
      {children}
    </div>
  );
}

const selectCls =
  "w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500";

const inputCls =
  "w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500";
