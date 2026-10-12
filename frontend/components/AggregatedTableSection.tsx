"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp, ArrowRight, Settings2 } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./AggregatedTableSection.module.css";

// Values transcribed from the supplied product screenshot.
const rows = [
  { company: "AAPL", average: 5, revenue: 5, income: 5, debt: 5, profitability: 5, quarter: "1Q/2026", results: 1 },
  { company: "AMZN", average: 5, revenue: 5, income: 4, debt: 4, profitability: 5, quarter: "1Q/2026", results: 1 },
  { company: "ARISTA", average: 5, revenue: 5, income: 5, debt: 5, profitability: 4, quarter: "1Q/2026", results: 2 },
  { company: "BTG", average: 5, revenue: 5, income: 5, debt: 5, profitability: 5, quarter: "1Q/2026", results: 2 },
  { company: "GOOGL", average: 5, revenue: 5, income: 4, debt: 4, profitability: 5, quarter: "1Q/2026", results: 1 },
  { company: "ITAU", average: 5, revenue: 4, income: 5, debt: 5, profitability: 5, quarter: "4Q/2025", results: 2 },
  { company: "MARVELL", average: 5, revenue: 5, income: 5, debt: 4, profitability: 4, quarter: "4Q/2026", results: 1 },
  { company: "META", average: 5, revenue: 5, income: 3, debt: 4, profitability: 5, quarter: "1Q/2026", results: 1 },
];
const keys = ["average", "revenue", "income", "debt", "profitability", "quarter", "results"] as const;
type Column = typeof keys[number];
const columnWidths: Record<Column, string> = { average: "11%", revenue: "12%", income: "12%", debt: "10%", profitability: "14%", quarter: "13%", results: "14%" };

export default function AggregatedTableSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const labels: Record<Column, string> = {
    average: english ? "Average" : "Média", revenue: english ? "Net Revenue" : "Receita líquida",
    income: english ? "Net Income" : "Lucro líquido", debt: english ? "Net Debt" : "Dívida líquida",
    profitability: english ? "Profitability" : "Rentabilidade", quarter: english ? "Last Quarter" : "Último trimestre",
    results: english ? "Analyzed Results" : "Resultados analisados",
  };
  const [columns, setColumns] = useState<Column[]>([...keys]);
  const [sort, setSort] = useState<{key: Column; descending: boolean}>({key: "average", descending: true});
  const sortedRows = [...rows].sort((a, b) => {
    const left = a[sort.key], right = b[sort.key];
    const comparison = typeof left === "number" && typeof right === "number" ? left - right : String(left).localeCompare(String(right));
    return sort.descending ? -comparison : comparison;
  });

  return <section className={styles.section} aria-labelledby="aggregated-table-heading">
    <div className={styles.container}>
      <div className={styles.introduction}>
        <h2 id="aggregated-table-heading">{english ? "Compare all your analyses " : "Compare todas as suas análises "}<span>{english ? "in one place" : "em um só lugar"}</span></h2>
        <p>{english ? "Bring company scores together and compare the fundamentals at a glance." : "Reúna as notas das empresas e compare os fundamentos de um olhar."}</p>
      </div>
      <div className={styles.frame}>
      <div className={styles.screen}>
      <header className={styles.header}>
        <div><h3>{english ? "Aggregated Table" : "Tabela Agregada"}</h3><p>{english ? "Consolidated view of company performance." : "Visão consolidada do desempenho das empresas."}</p></div>
        <details className={styles.configure}>
          <summary><Settings2 size={20} />{english ? "Configure Columns" : "Configurar colunas"}</summary>
          <fieldset><legend>{english ? "Visible columns" : "Colunas visíveis"}</legend>{keys.map(key => <label key={key}><input type="checkbox" checked={columns.includes(key)} onChange={() => setColumns(current => current.includes(key) ? current.filter(column => column !== key) : keys.filter(column => column === key || current.includes(column)))} />{labels[key]}</label>)}</fieldset>
        </details>
      </header>
      <div className={styles.scroll} tabIndex={0} role="region" aria-label={english ? "Company comparison table" : "Tabela de comparação de empresas"}>
        <table><thead><tr><th scope="col">{english ? "Company" : "Empresa"}</th>{columns.map(key => <th key={key} scope="col" style={{width: columnWidths[key]}} aria-sort={sort.key === key ? (sort.descending ? "descending" : "ascending") : "none"}><button onClick={() => setSort({key, descending: sort.key === key ? !sort.descending : true})}><span className={key === "average" || key === "profitability" ? undefined : styles.wrapHeading}>{labels[key]}</span>{sort.key === key && (sort.descending ? <ArrowDown size={15} /> : <ArrowUp size={15} />)}</button></th>)}</tr></thead>
          <tbody>{sortedRows.map(row => <tr key={row.company}><th scope="row">{row.company}</th>{columns.map(key => <td key={key} className={keys.indexOf(key) < 5 ? (row[key] === 3 ? styles.caution : styles.score) : undefined}>{row[key]}</td>)}</tr>)}</tbody>
        </table>
      </div>
      </div>
      </div>
      <Link className={styles.start} href="/dashboard">{english ? "Start comparing" : "Começar a comparar"}<ArrowRight size={16} /></Link>
      <p className={styles.caption}>{english ? "Product preview — compare your saved analyses in one place." : "Demonstração do produto — compare suas análises salvas em um só lugar."}</p>
    </div>
  </section>;
}
