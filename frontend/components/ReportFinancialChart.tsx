"use client";

import { useEffect, useRef } from "react";
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip } from "chart.js";
import type { FullReport } from "./FullReports";
import { formatReportMoney } from "../lib/reportNumbers";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

type Props = { rows: NonNullable<FullReport["financial_history"]>; field: "revenue" | "net_income" | "free_cash_flow"; title: string; locale: string };

export default function ReportFinancialChart({ rows, field, title, locale }: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const values = rows.filter(row => row[field] !== null);
  const currency = values[0]?.currency;
  const usable = values.length > 0 && new Set(values.map(row => row.currency)).size === 1;
  useEffect(() => {
    if (!canvas.current || !usable) return;
    const chart = new Chart(canvas.current, {
      type: "bar",
      data: { labels: rows.map(row => row.period.match(/\d{4}/)?.[0] || row.period), datasets: [{
        label: title, data: rows.map(row => row[field]), borderRadius: 4,
        backgroundColor: rows.map(row => (row[field] ?? 0) < 0 ? "#be4555" : "#29476a"), maxBarThickness: 100,
      }] },
      options: { responsive: true, maintainAspectRatio: false,
        animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 350 },
        plugins: { tooltip: { callbacks: { label: context => formatReportMoney(context.parsed.y, currency, locale) } } },
        scales: { x: { grid: { display: false }, ticks: { color: "#64748b", maxRotation: 0 } },
          y: { beginAtZero: true, border: { display: false }, grid: { color: "#e2e8f0" },
            ticks: { color: "#64748b", maxTicksLimit: 5, callback: value => formatReportMoney(Number(value), null, locale) } } },
      },
    });
    return () => chart.destroy();
  }, [rows, field, title, locale, currency, usable]);
  if (!usable) return null;
  return <figure className="mt-5 min-w-0 rounded-xl bg-[#f8faf9] p-4 sm:p-6">
    <figcaption className="flex items-center justify-between gap-3 text-sm font-semibold text-slate-700">{title}<span className="text-[10px] font-medium text-slate-400">{currency}</span></figcaption>
    <div className="relative mt-4 h-56 w-full"><canvas ref={canvas} role="img" aria-label={title} aria-describedby={`chart-${field}-data`} /></div>
    <table id={`chart-${field}-data`} className="sr-only"><caption>{title}</caption><tbody>{values.map(row => <tr key={row.period}><th scope="row">{row.period}</th><td>{formatReportMoney(row[field], row.currency, locale)}</td></tr>)}</tbody></table>
  </figure>;
}
