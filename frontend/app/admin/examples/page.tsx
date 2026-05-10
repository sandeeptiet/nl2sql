"use client";

import { useState, useEffect } from "react";
import { FewShotExample } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

const QUERY_TYPES = [
  "SELECT_SIMPLE",
  "SELECT_AGGREGATE",
  "SELECT_JOIN",
  "SELECT_TEMPORAL",
];

type ModalMode = "add" | "edit";

interface ModalState {
  mode: ModalMode;
  example?: FewShotExample;
}

export default function ExamplesPage() {
  const [examples, setExamples] = useState<FewShotExample[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("");
  const [modal, setModal] = useState<ModalState | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  async function load(type = filterType) {
    setLoading(true);
    const params = new URLSearchParams();
    if (type) params.set("query_type", type);
    const r = await fetch(`${API_BASE}/api/v1/admin/examples?${params}`);
    const d = await r.json();
    setExamples(d.examples);
    setLoading(false);
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleFilterChange(type: string) {
    setFilterType(type);
    load(type);
  }

  async function handleDelete(id: number) {
    await fetch(`${API_BASE}/api/v1/admin/examples/${id}`, { method: "DELETE" });
    setDeleteId(null);
    load();
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Examples Manager</h1>
        <button
          onClick={() => setModal({ mode: "add" })}
          className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg"
        >
          + Add Example
        </button>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        <select
          value={filterType}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All types</option>
          {QUERY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <span className="text-sm text-gray-400 self-center">{examples.length} examples</span>
      </div>

      {/* List */}
      {loading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : (
        <div className="space-y-2">
          {examples.map((ex) => (
            <div key={ex.id} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">{ex.question}</p>
                  <pre className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap">
                    {ex.sql}
                  </pre>
                </div>
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {ex.query_type && (
                    <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-2 py-0.5 rounded-full">
                      {ex.query_type}
                    </span>
                  )}
                  <div className="flex gap-1">
                    <button
                      onClick={() => setModal({ mode: "edit", example: ex })}
                      className="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-700 px-2 py-0.5 rounded"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteId(ex.id)}
                      className="text-xs text-red-500 hover:text-red-700 border border-red-200 dark:border-red-900 px-2 py-0.5 rounded"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {examples.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">No examples found.</p>
          )}
        </div>
      )}

      {/* Add / Edit Modal */}
      {modal && (
        <ExampleModal
          mode={modal.mode}
          example={modal.example}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); }}
        />
      )}

      {/* Delete confirm */}
      {deleteId !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl p-6 w-80">
            <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Delete example?</p>
            <p className="text-xs text-gray-400 mb-4">This will also rebuild the FAISS index.</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeleteId(null)}
                className="text-sm px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteId)}
                className="text-sm px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ExampleModal({
  mode,
  example,
  onClose,
  onSaved,
}: {
  mode: ModalMode;
  example?: FewShotExample;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [question, setQuestion] = useState(example?.question ?? "");
  const [sql, setSql] = useState(example?.sql ?? "");
  const [queryType, setQueryType] = useState(example?.query_type ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSubmit() {
    if (!question.trim() || !sql.trim()) return;
    setSaving(true);
    const body = { question, sql, query_type: queryType || null };
    if (mode === "add") {
      await fetch(`${API_BASE}/api/v1/admin/examples`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } else {
      await fetch(`${API_BASE}/api/v1/admin/examples/${example!.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    setSaving(false);
    onSaved();
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {mode === "add" ? "Add Example" : "Edit Example"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-1">Question</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={2}
              className="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
              placeholder="e.g. Top 5 customers by total orders"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-1">SQL</label>
            <textarea
              value={sql}
              onChange={(e) => setSql(e.target.value)}
              rows={5}
              className="w-full text-xs font-mono border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-gray-950 text-green-400 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
              placeholder="SELECT ..."
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-1">Query Type</label>
            <select
              value={queryType}
              onChange={(e) => setQueryType(e.target.value)}
              className="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">— None —</option>
              {QUERY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
        <div className="flex gap-2 justify-end px-5 pb-5">
          <button
            onClick={onClose}
            className="text-sm px-4 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !question.trim() || !sql.trim()}
            className="text-sm px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg"
          >
            {saving ? "Saving…" : mode === "add" ? "Add" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
