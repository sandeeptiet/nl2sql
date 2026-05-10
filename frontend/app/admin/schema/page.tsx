"use client";

import { useState, useEffect } from "react";
import { SchemaTable, SchemaColumn } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function SchemaPage() {
  const [tables, setTables] = useState<SchemaTable[]>([]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/admin/schema`)
      .then((r) => r.json())
      .then((d) => {
        setTables(d.tables);
        if (d.tables.length > 0) setOpen({ [d.tables[0].table]: true });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-gray-400">Loading…</p>;

  return (
    <div className="max-w-4xl">
      <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schema Manager</h1>
      <div className="space-y-2">
        {tables.map((t) => (
          <div key={t.table} className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <button
              onClick={() => setOpen((o) => ({ ...o, [t.table]: !o[t.table] }))}
              className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
            >
              <span className="font-medium text-sm text-gray-800 dark:text-gray-200">{t.table}</span>
              <span className="flex items-center gap-2 text-xs text-gray-400">
                <span>{t.columns.length} columns</span>
                <span>{open[t.table] ? "▲" : "▼"}</span>
              </span>
            </button>

            {open[t.table] && (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                <div className="grid grid-cols-[120px_100px_1fr_80px_60px] gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-900/50 text-xs font-medium text-gray-400 uppercase tracking-wide">
                  <span>Column</span>
                  <span>Type</span>
                  <span>Description</span>
                  <span>Sensitive</span>
                  <span></span>
                </div>
                {t.columns.map((col) => (
                  <ColumnRow
                    key={col.name}
                    tableName={t.table}
                    column={col}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ColumnRow({ tableName, column }: { tableName: string; column: SchemaColumn }) {
  const [description, setDescription] = useState(column.description ?? "");
  const [isSensitive, setIsSensitive] = useState(column.is_sensitive);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save(overrides?: Partial<{ description: string; isSensitive: boolean }>) {
    setSaving(true);
    await fetch(`${API_BASE}/api/v1/admin/schema/column`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table_name: tableName,
        column_name: column.name,
        description: overrides?.description ?? description,
        is_sensitive: overrides?.isSensitive ?? isSensitive,
      }),
    });
    setSaving(false);
    setDirty(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  function toggleSensitive() {
    const next = !isSensitive;
    setIsSensitive(next);
    save({ isSensitive: next });
  }

  return (
    <div className="grid grid-cols-[120px_100px_1fr_80px_60px] gap-2 items-center px-4 py-2">
      <span className="text-xs font-mono text-gray-700 dark:text-gray-300 truncate">{column.name}</span>
      <span className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded px-1.5 py-0.5 font-mono truncate">
        {column.type}
      </span>
      <input
        type="text"
        value={description}
        onChange={(e) => { setDescription(e.target.value); setDirty(true); setSaved(false); }}
        placeholder="Add description…"
        className="text-xs border border-gray-200 dark:border-gray-700 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full"
      />
      <div className="flex justify-center">
        <button
          onClick={toggleSensitive}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
            isSensitive ? "bg-red-500" : "bg-gray-300 dark:bg-gray-600"
          }`}
        >
          <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${isSensitive ? "translate-x-4.5" : "translate-x-0.5"}`} />
        </button>
      </div>
      <div className="flex justify-end">
        {saved ? (
          <span className="text-xs text-green-600">Saved!</span>
        ) : dirty ? (
          <button
            onClick={() => save()}
            disabled={saving}
            className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-0.5 rounded disabled:opacity-50"
          >
            {saving ? "…" : "Save"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
