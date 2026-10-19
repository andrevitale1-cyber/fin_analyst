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
    const nodes: { node: Text; text: string; start: number }[] = [];
    let total = 0;
    while (walker.nextNode()) {
      const node = walker.currentNode as Text, text = node.data;
      nodes.push({ node, text, start: total }); total += text.length;
    }
    const duration = Math.min(total, 700) * 24;
    const observer = new IntersectionObserver(entries => {
      cancelAnimationFrame(frame);
      if (!entries.some(entry => entry.intersectionRatio >= .2)) { setTyping(false); return; }
      if (reduce.matches || stopped) return;
      const started = performance.now();
      const tick = (now: number) => {
        const cycle = (now - started) % (duration + 7000);
        setTyping(cycle < duration);
        if (cycle < duration) {
          const count = Math.floor(cycle / 24);
          for (const { node, text, start } of nodes) node.data = text.slice(0, Math.max(0, count - start));
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
