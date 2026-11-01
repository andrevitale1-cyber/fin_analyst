"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import styles from "./TypingPreview.module.css";

export default function TypingPreview({ children }: { children: ReactNode }) {
  const container = useRef<HTMLDivElement>(null);
  const animated = useRef<HTMLDivElement>(null);
  const [typing, setTyping] = useState(false);
  const finish = useRef(() => {});
  useEffect(() => {
    const root = container.current, copy = animated.current;
    if (!root || !copy) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0, stopped = false;
    const complete = () => { stopped = true; cancelAnimationFrame(frame); setTyping(false); };
    finish.current = complete;
    copy.replaceChildren(...Array.from(root.firstElementChild?.childNodes ?? [], node => node.cloneNode(true)));
    const walker = document.createTreeWalker(copy, NodeFilter.SHOW_TEXT);
    const groups = new Map<Element, { nodes: { node: Text; text: string; start: number }[]; length: number }>();
    while (walker.nextNode()) {
      const node = walker.currentNode as Text, text = node.data;
      const paragraph = node.parentElement?.closest('p, li, h5') ?? copy;
      const group = groups.get(paragraph) ?? { nodes: [], length: 0 };
      group.nodes.push({ node, text, start: group.length }); group.length += text.length;
      groups.set(paragraph, group);
    }
    const duration = 4500;
    const observer = new IntersectionObserver(entries => {
      cancelAnimationFrame(frame);
      if (!entries.some(entry => entry.intersectionRatio >= .2)) { setTyping(false); return; }
      if (reduce.matches || stopped) return;
      const started = performance.now();
      const tick = (now: number) => {
        const cycle = (now - started) % (duration + 7000);
        setTyping(cycle < duration);
        if (cycle < duration) {
          for (const group of groups.values()) {
            const paragraphDuration = Math.min(duration, Math.max(900, group.length * 8));
            const count = Math.ceil(group.length * Math.min(1, cycle / paragraphDuration));
            for (const { node, text, start } of group.nodes) node.data = text.slice(0, Math.max(0, count - start));
          }
        }
        frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    }, { threshold: .2 });
    observer.observe(root.closest('[role="region"]') ?? root);
    const motionChanged = () => { if (reduce.matches) complete(); };
    reduce.addEventListener("change", motionChanged);
    return () => { observer.disconnect(); cancelAnimationFrame(frame); reduce.removeEventListener("change", motionChanged); };
  }, [children]);
  return <div ref={container} className={styles.preview} data-typing={typing} onPointerDown={() => finish.current()} onWheel={() => finish.current()} onKeyDown={() => finish.current()}>
    <div className={styles.original}>{children}</div>
    <div ref={animated} aria-hidden="true" className={styles.animated} />
  </div>;
}
