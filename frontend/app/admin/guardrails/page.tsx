"use client";

import { useState, useEffect } from "react";
import { Guardrail } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
      <p className="text-sm text-gray-400 mb-6">
        Blocked operations are rejected before the SQL generator runs.
      </p>

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
