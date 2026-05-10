"use client";

import { useState } from "react";

interface SqlPreviewProps {
  sql: string;
  transpiledSql?: string | null;
  transpiledDialect?: string | null;
}

export default function SqlPreview({ sql, transpiledSql, transpiledDialect }: SqlPreviewProps) {
  const [open, setOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  function handleCopy(text: string, key: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 1500);
    });
  }

  function Block({ label, text, copyKey }: { label: string; text: string; copyKey: string }) {
    return (
      <div className="relative bg-gray-950 p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] uppercase tracking-wider text-gray-500">{label}</span>
          <button
            onClick={() => handleCopy(text, copyKey)}
            className="text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded transition-colors"
          >
            {copiedKey === copyKey ? "Copied!" : "Copy"}
          </button>
        </div>
        <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
          {text}
        </pre>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <span className="font-medium uppercase tracking-wide">SQL</span>
        <span>{open ? "▲ Hide" : "▼ Show"}</span>
      </button>

      {open && (
        <div className="divide-y divide-gray-800">
          <Block label="MySQL (executed)" text={sql} copyKey="primary" />
          {transpiledSql && transpiledDialect && (
            <Block
              label={`${transpiledDialect.toUpperCase()} (transpiled)`}
              text={transpiledSql}
              copyKey="transpiled"
            />
          )}
        </div>
      )}
    </div>
  );
}
