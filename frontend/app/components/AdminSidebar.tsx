"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/admin/schema",     label: "Schema Manager" },
  { href: "/admin/examples",   label: "Examples Manager" },
  { href: "/admin/logs",       label: "Query Logs" },
  { href: "/admin/guardrails", label: "Guardrails Config" },
  { href: "/admin/config",     label: "Model Config" },
];

export default function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-52 flex-shrink-0 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex flex-col">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <Link href="/" className="text-sm font-semibold text-gray-800 dark:text-gray-200 hover:text-blue-600">
          ← nl2sql
        </Link>
        <p className="text-xs text-gray-400 mt-0.5">Admin Panel</p>
      </div>
      <nav className="p-2 space-y-0.5">
        {NAV.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
              pathname.startsWith(href)
                ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
