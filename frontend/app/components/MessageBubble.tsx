"use client";

import { QueryResponse } from "../lib/types";
import ResultsTable from "./ResultsTable";
import ResultChart from "./ResultChart";
import SqlPreview from "./SqlPreview";

interface UserBubbleProps {
  content: string;
}

interface BotBubbleProps {
  response: QueryResponse;
}

export function UserBubble({ content }: UserBubbleProps) {
  return (
    <div className="flex justify-end mb-4">
      <div className="max-w-[70%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
        {content}
      </div>
    </div>
  );
}

export function BotBubble({ response }: BotBubbleProps) {
  const hasResults = response.table.length > 0 && response.columns.length > 0;

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[90%] w-full">
        <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm mb-2">
          {response.error ? (
            <p className="text-red-500">{response.error}</p>
          ) : (
            <p className="text-gray-800 dark:text-gray-200">{response.nl_summary}</p>
          )}
          {hasResults && (
            <div className="flex gap-2 mt-2">
              <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full">
                {response.row_count} rows
              </span>
              <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full">
                {response.latency_ms.toFixed(0)} ms
              </span>
            </div>
          )}
        </div>

        {hasResults && (
          <div className="space-y-3">
            <ResultsTable columns={response.columns} rows={response.table} />
            {response.chart_type && (
              <ResultChart
                columns={response.columns}
                rows={response.table}
                chartType={response.chart_type}
              />
            )}
            <SqlPreview
              sql={response.sql}
              transpiledSql={response.transpiled_sql}
              transpiledDialect={response.transpiled_dialect}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export function LoadingSkeleton() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 w-48">
        <div className="flex gap-1.5 items-center">
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
