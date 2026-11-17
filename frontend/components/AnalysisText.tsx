import React from "react";
import { splitBold, splitTables } from "../lib/analysisText";

const bold = (text: string) => splitBold(text).map((part, index) =>
  part.bold ? <strong key={index} className="font-bold text-slate-900">{part.text}</strong> : <React.Fragment key={index}>{part.text}</React.Fragment>);

// Analysis prose with **bold** and Markdown pipe tables, rendered as escaped React nodes.
// A last column of figures (e.g. price changes) is right-aligned and colored; text columns stay plain.
const numeric = (cell: string) => /^[−+-]?\s*(?:R\$|US\$|\$)?\s*\d/.test(cell.trim());

export default function AnalysisText({ text }: { text: string }) {
  return <>{splitTables(text).map((block, index) => {
    if (block.kind === "text") return <React.Fragment key={index}>{bold(block.text.replace(/^\n+|\n+$/g, ""))}</React.Fragment>;
    const figures = block.rows.length > 0 && block.rows.every(row => numeric(row[row.length - 1] || ""));
    return <div key={index} className="not-prose my-5 overflow-x-auto rounded-2xl border border-slate-200 whitespace-normal">
        <table className="w-full min-w-[520px] border-collapse text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>{block.header.map((cell, column) => <th key={column} className={`px-4 py-3 font-semibold ${figures && column === block.header.length - 1 ? "text-right" : ""}`}>{bold(cell)}</th>)}</tr>
          </thead>
          <tbody>{block.rows.map((row, line) => <tr key={line} className="border-t border-slate-100 align-top">
            {row.map((cell, column) => <td key={column} className={`px-4 py-2.5 tabular-nums ${column === 0 ? "font-medium text-slate-800" : "text-slate-600"} ${figures && column === row.length - 1 ? `text-right font-semibold ${cell.startsWith("−") || cell.startsWith("-") ? "text-red-600" : cell.startsWith("+") ? "text-emerald-600" : ""}` : ""}`}>{bold(cell)}</td>)}
          </tr>)}</tbody>
        </table>
      </div>;
  })}</>;
}
