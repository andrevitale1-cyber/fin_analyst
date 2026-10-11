"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import type { Rive } from "@rive-app/canvas";
import { Link } from "@/i18n/routing";
import styles from "./AudienceCards.module.css";

const media = "/reference/clearstreet/";

export default function AudienceCards({ locale }: { locale: string }) {
  const video = useRef<HTMLVideoElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const animation = useRef<Rive | null>(null);
  const section = useRef<HTMLElement>(null);
  const english = locale === "en";
  const [desktop, setDesktop] = useState(false);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: section, offset: ["start end", "end end"] });
  const revealY = useTransform(scrollYProgress, (p) => desktop && !reduce ? 140 * Math.pow(1 - p, 3) : 0);
  const revealOpacity = useTransform(scrollYProgress, (p) => desktop && !reduce ? 1 - Math.pow(1 - p, 3) : 1);
  useEffect(() => {
    const query = window.matchMedia("(min-width: 1024px)");
    const sync = () => setDesktop(query.matches);
    sync(); query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    let disposed = false;
    let resize: ResizeObserver | undefined;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      void import("@rive-app/canvas").then(({ Rive, Layout, Fit, Alignment, RuntimeLoader }) => {
        if (disposed || !canvas.current) return;
        RuntimeLoader.setWasmUrl(media + "rive.wasm");
        const instance = new Rive({
          src: media + "services.riv",
          canvas: canvas.current,
          autoplay: false,
          layout: new Layout({ fit: Fit.Cover, alignment: Alignment.Center }),
          onLoad: () => {
            if (disposed) return;
            instance.resizeDrawingSurfaceToCanvas();
            canvas.current?.setAttribute("data-ready", "true");
            resize = new ResizeObserver(() => instance.resizeDrawingSurfaceToCanvas());
            if (canvas.current) resize.observe(canvas.current);
          },
        });
        animation.current = instance;
      });
    }, { rootMargin: "300px" });
    if (section.current) observer.observe(section.current);
    return () => { disposed = true; observer.disconnect(); resize?.disconnect(); animation.current?.cleanup(); animation.current = null; };
  }, []);

  const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const playVideo = () => {
    if (!reducedMotion() && video.current) void video.current.play().catch(() => {});
  };
  const playServices = () => {
    if (!reducedMotion() && animation.current && canvas.current?.dataset.ready === "true") {
      animation.current.stop();
      animation.current.reset();
      animation.current.play();
    }
  };
  const plus = <span className={styles.plus} aria-hidden="true"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M20.75 11.25H12.75V3.25H11.25V11.25H3.25V12.75H11.25V20.75H12.75V12.75H20.75V11.25Z" fill="currentColor" /></svg></span>;

  return <section ref={section} className={styles.section} aria-label={english ? "Who FinAnalyzer is for" : "Para quem é o FinAnalyzer"}>
    <div className={styles.grid}>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><Link href="/dashboard" className={styles.card} onMouseEnter={playVideo} onFocus={playVideo}>
        <h2>Clients</h2>
        <div className={styles.visual}>
          <video ref={video} className={styles.video} src={media + "clients.mp4#t=0.01"} muted playsInline preload="metadata" aria-hidden="true" onEnded={() => { if (video.current) video.current.currentTime = 0; }} />
          <span className={styles.shade} />
          {plus}
        </div>
        <p>{english ? <><strong>For individual investors who want to understand companies and analyze results faster.</strong> Clear explanations and organized information, even if you are just getting started with investing.</> : <><strong>Para o investidor pessoa física que quer entender as empresas e analisar resultados com mais agilidade.</strong> Explicações claras e informações organizadas, mesmo para quem está começando a investir.</>}</p>
      </Link></motion.div>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><Link href="/dashboard" className={styles.card} onMouseEnter={playServices} onFocus={playServices}>
        <h2>Services</h2>
        <div className={styles.visual} style={{ backgroundImage: `url(${media}services.jpg)`, backgroundSize: "cover", backgroundPosition: "center" }}>
          <canvas ref={canvas} className={styles.canvas} aria-hidden="true" />
          {plus}
        </div>
        <p>{english ? <><strong>For businesses, analysts, and professional investors who need greater speed in their research.</strong> Bring fundamentals, reports, and sources together to streamline financial analysis and support your team&apos;s work.</> : <><strong>Para investidores pessoa jurídica, analistas e profissionais que precisam de mais agilidade nas análises.</strong> Reúna fundamentos, relatórios e fontes para acelerar a leitura de resultados e apoiar o trabalho da sua equipe.</>}</p>
      </Link></motion.div>
    </div>
  </section>;
}
