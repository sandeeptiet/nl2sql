"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ResultChartProps {
  columns: string[];
  rows: Record<string, unknown>[];
  chartType: "bar" | "line";
}

export default function ResultChart({ columns, rows, chartType }: ResultChartProps) {
  const [xKey, yKey] = columns;

  const data = rows.map((row) => ({
    [xKey]: row[xKey],
    [yKey]: parseFloat(String(row[yKey]).replace(",", "")) || 0,
  }));

  const commonProps = {
    data,
    margin: { top: 4, right: 16, left: 0, bottom: 32 },
  };

  const axisProps = {
    xAxis: (
      <XAxis
        dataKey={xKey}
        tick={{ fontSize: 11 }}
        angle={-35}
        textAnchor="end"
        interval="preserveStartEnd"
      />
    ),
    yAxis: <YAxis tick={{ fontSize: 11 }} width={50} />,
    grid: <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />,
    tooltip: <Tooltip />,
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
      <p className="text-xs text-gray-400 mb-2 uppercase tracking-wide">Chart</p>
      <ResponsiveContainer width="100%" height={220}>
        {chartType === "bar" ? (
          <BarChart {...commonProps}>
            {axisProps.grid}
            {axisProps.xAxis}
            {axisProps.yAxis}
            {axisProps.tooltip}
            <Bar dataKey={yKey} fill="#3b82f6" radius={[3, 3, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart {...commonProps}>
            {axisProps.grid}
            {axisProps.xAxis}
            {axisProps.yAxis}
            {axisProps.tooltip}
            <Line
              type="monotone"
              dataKey={yKey}
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
