"use client";

import { useState, useEffect } from "react";
import { QueryLog } from "../../lib/adminTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATUS_STYLES: Record<string, string> = {
  success: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400",
  error:   "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400",
};

const QUERY_TYPES = [
  "SELECT_SIMPLE",
  "SELECT_AGGREGATE",
  "SELECT_JOIN",
  "SELECT_TEMPORAL",
];

export default function LogsPage() {
  const [logs, setLogs] = useState<QueryLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  async function load(status = filterStatus, type = filterType) {
    setLoading(true);
    const params = new URLSearchParams({ limit: "100" });
    if (status) params.set("status", status);
    if (type) params.set("query_type", type);
    const r = await fetch(`${API_BASE}/api/v1/admin/logs?${params}`);
    const d = await r.json();
    setLogs(d.logs);
    setTotal(d.total);
    setLoading(false);
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleExportCSV() {
    window.open(`${API_BASE}/api/v1/admin/logs/export`, "_blank");
  }

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Query Logs</h1>
        <button
          onClick={handleExportCSV}
          className="text-sm border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 px-3 py-1.5 rounded-lg"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); load(e.target.value, filterType); }}
          className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); load(filterStatus, e.target.value); }}
          className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All types</option>
          {QUERY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <span className="text-sm text-gray-400 self-center">{total} total</span>
      </div>

      {/* Table */}
      {loading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                {["#", "Question", "Type", "Status", "Latency", "Rows", "Time"].map((h) => (
                  <th key={h} className="px-3 py-2 text-left font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {logs.map((log) => (
                <>
                  <tr
                    key={log.id}
                    onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                  >
                    <td className="px-3 py-2 text-gray-400">{log.id}</td>
                    <td className="px-3 py-2 text-gray-700 dark:text-gray-300 max-w-xs truncate">
                      {log.nl_input}
                    </td>
                    <td className="px-3 py-2 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {log.query_type ?? "—"}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[log.status] ?? "bg-gray-100 text-gray-500"}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {log.latency_ms != null ? `${log.latency_ms.toFixed(0)} ms` : "—"}
                    </td>
                    <td className="px-3 py-2 text-gray-500 dark:text-gray-400">
                      {log.row_count ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-gray-400 whitespace-nowrap">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-exp`} className="bg-gray-50 dark:bg-gray-900">
                      <td colSpan={7} className="px-4 py-3">
                        {log.error_msg && (
                          <p className="text-xs text-red-500 mb-2">Error: {log.error_msg}</p>
                        )}
                        <pre className="text-xs font-mono text-green-400 bg-gray-950 rounded p-3 overflow-x-auto whitespace-pre-wrap">
                          {log.generated_sql ?? "No SQL"}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-400">
                    No logs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
