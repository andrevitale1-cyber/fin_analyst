"use client";

import { useEffect, useRef } from "react";
import type { Rive } from "@rive-app/canvas";

export default function MarqueeSymbol({ index, visible }: { index: number; visible: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (!visible || !canvas.current) return;
    let disposed = false;
    let ready = false;
    let instance: Rive | undefined;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      if (!ready || !instance) return;
      if (reduce.matches) { instance.pause(); instance.scrub(instance.animationNames, 1); }
      else instance.play();
    };
    const resize = new ResizeObserver(() => instance?.resizeDrawingSurfaceToCanvas(Math.min(devicePixelRatio, 2)));
    resize.observe(canvas.current);
    void import("@rive-app/canvas").then(({ Rive, RuntimeLoader, Layout, Fit }) => {
      if (disposed || !canvas.current) return;
      RuntimeLoader.setWasmUrl("/reference/clearstreet/rive.wasm");
      instance = new Rive({ canvas: canvas.current, src: `/reference/clearstreet/marquee-${index}.riv`,
        autoplay: false, layout: new Layout({ fit: Fit.Contain }),
        onLoad: () => { ready = true; instance?.resizeDrawingSurfaceToCanvas(Math.min(devicePixelRatio, 2)); sync(); },
      });
    });
    reduce.addEventListener("change", sync);
    return () => { disposed = true; resize.disconnect(); reduce.removeEventListener("change", sync); instance?.cleanup(); };
  }, [index, visible]);
  return <canvas ref={canvas} width={84} height={84} aria-hidden="true" style={{ width: "100%", height: "100%" }} />;
}
