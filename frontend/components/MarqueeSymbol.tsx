"use client";

import { useEffect, useRef, useState } from "react";
import type { Rive } from "@rive-app/canvas";
import styles from "./MarqueeSymbol.module.css";

// Native versions of the six Clear Street geometric motifs stay visible without WASM/canvas.
function VectorSymbol({ index }: { index: number }) {
  return <svg className={styles.vector} viewBox="0 0 84 84" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
    {index === 1 && <><circle cx="42" cy="34" r="27" /><circle cx="42" cy="50" r="27" /></>}
    {index === 2 && Array.from({ length: 12 }, (_, i) => <circle key={i} cx="42" cy="10" r="6" transform={`rotate(${i * 30} 42 42)`} />)}
    {index === 3 && [34, 27, 20, 13, 6].map(r => <circle key={r} cx="42" cy="42" r={r} />)}
    {index === 4 && [[22,34,11],[34,27,10],[45,20,8],[56,13,6],[65,7,4]].map(([cy,rx,ry]) => <ellipse key={cy} cx="42" cy={cy} rx={rx} ry={ry} />)}
    {index === 5 && [34,38,42,46,50].map(cx => <circle key={cx} cx={cx} cy="42" r="28" />)}
    {index === 6 && <><circle cx="35" cy="30" r="22" /><circle cx="53" cy="43" r="22" /><circle cx="33" cy="54" r="22" /></>}
  </svg>;
}

export default function MarqueeSymbol({ index, visible }: { index: number; visible: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [desktop, setDesktop] = useState(false);
  const [readyToDraw, setReadyToDraw] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(min-width: 744px) and (hover: hover) and (pointer: fine)");
    const sync = () => setDesktop(query.matches);
    sync(); query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);
  useEffect(() => {
    setReadyToDraw(false);
    if (!desktop || !visible || !canvas.current) return;
    let disposed = false;
    let ready = false;
    let instance: Rive | undefined;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      if (!ready || !instance) return;
      if (reduce.matches) { instance.pause(); instance.scrub(instance.animationNames, 1); }
      else instance.play(instance.stateMachineNames);
    };
    const resize = new ResizeObserver(() => instance?.resizeDrawingSurfaceToCanvas(Math.min(devicePixelRatio, 2)));
    resize.observe(canvas.current);
    void import("@rive-app/canvas").then(({ Rive, RuntimeLoader, Layout, Fit }) => {
      if (disposed || !canvas.current) return;
      RuntimeLoader.setWasmUrl("/reference/clearstreet/rive.wasm");
      instance = new Rive({ canvas: canvas.current, src: `/reference/clearstreet/marquee-${index}.riv`,
        autoplay: false, stateMachines: "State Machine 1", layout: new Layout({ fit: Fit.Contain }),
        onLoad: () => { if (disposed) return; ready = true; setReadyToDraw(true); instance?.resizeDrawingSurfaceToCanvas(Math.min(devicePixelRatio, 2)); sync(); },
        onLoadError: () => { if (!disposed) setReadyToDraw(false); },
      });
    }).catch(() => { if (!disposed) setReadyToDraw(false); });
    reduce.addEventListener("change", sync);
    return () => { disposed = true; resize.disconnect(); reduce.removeEventListener("change", sync); instance?.cleanup(); };
  }, [index, visible, desktop]);
  return <span className={styles.symbol} data-ready={readyToDraw} aria-hidden="true"><VectorSymbol index={index} />{desktop && <canvas className={styles.canvas} ref={canvas} width={84} height={84} />}</span>;
}
