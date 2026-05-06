"use client";

const SUGGESTIONS = [
  "Top 5 customers by total orders",
  "Monthly revenue for 2024",
  "Products with the most reviews",
  "Average order value by category",
  "Orders placed in the last 30 days",
  "Customers who haven't ordered in 90 days",
];

interface SuggestedQueriesProps {
  onSelect: (question: string) => void;
}

export default function SuggestedQueries({ onSelect }: SuggestedQueriesProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center px-4">
      {SUGGESTIONS.map((s) => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-700 dark:hover:text-blue-400 border border-gray-200 dark:border-gray-700 rounded-full px-3 py-1.5 transition-colors"
        >
          {s}
        </button>
      ))}
    </div>
  );
}
