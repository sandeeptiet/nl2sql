"use client";

import { useState, useEffect } from "react";
import { Guardrail } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

const DESCRIPTIONS: Record<string, string> = {
  DROP:     "Permanently removes a table or database",
  DELETE:   "Removes rows from a table",
  UPDATE:   "Modifies existing rows",
  INSERT:   "Adds new rows",
  TRUNCATE: "Removes all rows from a table instantly",
  ALTER:    "Modifies table structure",
};

export default function GuardrailsPage() {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/admin/guardrails`)
      .then((r) => r.json())
      .then((d) => setGuardrails(d.guardrails))
      .finally(() => setLoading(false));
  }, []);

  async function toggle(operation: string, current: boolean) {
    setSaving(operation);
    const next = !current;
    await fetch(`${API_BASE}/api/v1/admin/guardrails`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation, is_blocked: next }),
    });
    setGuardrails((prev) =>
      prev.map((g) => (g.operation === operation ? { ...g, is_blocked: next } : g))
    );
    setSaving(null);
  }

  if (loading) return <p className="text-sm text-gray-400">Loading…</p>;

  const blocked = guardrails.filter((g) => g.is_blocked).length;

  return (
    <div className="max-w-xl">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Guardrails Config</h1>
        <span className="text-xs text-gray-400">{blocked} / {guardrails.length} blocked</span>
      </div>
      <p className="text-sm text-gray-400 mb-4">
        Blocked operations are rejected before the SQL generator runs.
      </p>

      <div className="mb-6 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
        <p className="font-medium mb-1">Why is INSERT / UPDATE / DELETE still rejected even when set to “Allowed”?</p>
        <p className="text-xs leading-relaxed">
          QueryMind protects your data with <span className="font-semibold">four layers of safety</span>, and this toggle is just one of them:
        </p>
        <ol className="mt-2 ml-4 list-decimal text-xs leading-relaxed space-y-0.5">
          <li><span className="font-semibold">Question Classifier</span> — only data-lookup questions reach the SQL generator.</li>
          <li><span className="font-semibold">SQL Generator</span> — the AI is instructed to write read-only queries (SELECT) only.</li>
          <li><span className="font-semibold">SQL Validator</span> — this toggle. Last-mile keyword check on the generated SQL.</li>
          <li><span className="font-semibold">Database User</span> — the app connects with a read-only login that the database itself rejects writes from.</li>
        </ol>
        <p className="text-xs leading-relaxed mt-2">
          Allowing an operation here only relaxes layer 3. Lookups and reports always work — write operations are intentionally hard to perform from the chat UI.
        </p>
      </div>

      <div className="space-y-3">
        {guardrails.map((g) => (
          <div
            key={g.operation}
            className="flex items-center justify-between bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{g.operation}</p>
              <p className="text-xs text-gray-400">{DESCRIPTIONS[g.operation] ?? ""}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${g.is_blocked ? "text-red-500" : "text-green-600"}`}>
                {g.is_blocked ? "Blocked" : "Allowed"}
              </span>
              <button
                onClick={() => toggle(g.operation, g.is_blocked)}
                disabled={saving === g.operation}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-60 ${
                  g.is_blocked ? "bg-red-500" : "bg-gray-300 dark:bg-gray-600"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
                    g.is_blocked ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
