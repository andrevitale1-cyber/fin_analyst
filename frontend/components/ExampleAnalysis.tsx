"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronsDown } from "lucide-react";
import { splitBold, splitTables } from "@/lib/analysisText";
import styles from "./ExampleAnalysis.module.css";

const inline = (text: string): ReactNode[] => splitBold(text).map((part, index) => part.bold ? <strong key={index}>{part.text}</strong> : part.text);

function blocks(text: string) {
  return splitTables(text).flatMap((block, index) => block.kind === "table"
    ? [<div key={index} className={styles.tableWrap}><table>
        <thead><tr>{block.header.map((cell, column) => <th key={column}>{inline(cell)}</th>)}</tr></thead>
        <tbody>{block.rows.map((row, line) => <tr key={line}>{row.map((cell, column) => <td key={column}>{inline(cell)}</td>)}</tr>)}</tbody>
      </table></div>]
    : block.text.split(/\n{2,}/).map(chunk => chunk.trim()).filter(Boolean).map((chunk, part) => {
        const key = `${index}-${part}`, lines = chunk.split("\n");
        if (lines.every(line => line.startsWith("- "))) return <ul key={key}>{lines.map(line => <li key={line}>{inline(line.slice(2))}</li>)}</ul>;
        if (/^\*\*\d+\.\s[^*]+\*\*$/.test(chunk)) return <h5 key={key}>{chunk.slice(2, -2)}</h5>;
        return <p key={key}>{inline(chunk)}</p>;
      }));
}

// Scrollable analysis with a progress bar, a swipe hint and a one-time "peek" scroll that shows there is more to read.
export default function ExampleAnalysis({ text, className, label, hint }: { text: string; className: string; label: string; hint: string }) {
  const region = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const [atEnd, setAtEnd] = useState(false);
  useEffect(() => {
    const element = region.current;
    if (!element) return;
    let automatic = false, touched = false, peeked = false;
    const timers: number[] = [];
    const update = () => {
      const max = element.scrollHeight - element.clientHeight;
      setProgress(max > 0 ? element.scrollTop / max : 1);
      setAtEnd(element.scrollTop >= max - 4);
      if (!automatic && element.scrollTop > 40) setScrolled(true);
    };
    const interact = () => { touched = true; automatic = false; timers.forEach(clearTimeout); };
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting || peeked || touched || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      peeked = true;
      timers.push(window.setTimeout(() => {
        if (touched || element.scrollTop > 0) return;
        automatic = true;
        element.scrollTo({ top: 140, behavior: "smooth" });
        timers.push(window.setTimeout(() => element.scrollTo({ top: 0, behavior: "smooth" }), 1100));
        timers.push(window.setTimeout(() => { automatic = false; }, 2200));
      }, 700));
    }, { threshold: .6 });
    element.addEventListener("scroll", update, { passive: true });
    for (const name of ["pointerdown", "wheel", "touchstart", "keydown"]) element.addEventListener(name, interact, { passive: true });
    observer.observe(element);
    update();
    return () => {
      observer.disconnect(); timers.forEach(clearTimeout);
      element.removeEventListener("scroll", update);
      for (const name of ["pointerdown", "wheel", "touchstart", "keydown"]) element.removeEventListener(name, interact);
    };
  }, [text]);
  return <div className={styles.frame} data-scrolled={scrolled} data-end={atEnd}>
    <div className={styles.progress} aria-hidden="true"><i style={{ transform: `scaleX(${progress})` }} /></div>
    <div ref={region} className={`${className} ${styles.content}`} data-lenis-prevent tabIndex={0} role="region" aria-label={label}>{blocks(text)}</div>
    <div className={styles.fade} aria-hidden="true" />
    <div className={styles.hint} aria-hidden="true"><ChevronsDown size={15} />{hint}</div>
  </div>;
}
