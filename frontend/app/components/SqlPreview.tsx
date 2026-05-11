"use client";

import { useState } from "react";

interface SqlPreviewProps {
  sql: string;
}

export default function SqlPreview({ sql }: SqlPreviewProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(sql).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
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
        <div className="relative bg-gray-950 p-3">
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
          <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-x-auto pr-14">
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
}
