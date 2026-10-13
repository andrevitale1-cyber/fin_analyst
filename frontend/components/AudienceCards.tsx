"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useReducedMotion, useInView } from "framer-motion";
import type { Rive, LoopEvent } from "@rive-app/canvas";
import { Link } from "@/i18n/routing";
import useVideoPlayback from "./useVideoPlayback";
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
  const visible = useInView(section, { amount: .05 });
  const blocked = useVideoPlayback(video, visible);
  const { scrollYProgress } = useScroll({ target: section, offset: ["start end", "end end"] });
  const { scrollYProgress: exitProgress } = useScroll({ target: section, offset: ["end center", "end start"] });
  const exitOpacity = useTransform(exitProgress, [0, 1], [1, 0]);
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
          autoplay: true,
          onLoop: event => { if (!disposed && (event.data as LoopEvent)?.type === "oneshot") { instance.reset(); instance.play(); } },
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

  const plus = <span className={styles.plus} aria-hidden="true"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M20.75 11.25H12.75V3.25H11.25V11.25H3.25V12.75H11.25V20.75H12.75V12.75H20.75V11.25Z" fill="currentColor" /></svg></span>;

  return <motion.section ref={section} className={styles.section} style={reduce ? undefined : { opacity: exitOpacity }} aria-label={english ? "Who FinAnalyzer is for" : "Para quem é o FinAnalyzer"}>
    <div className={styles.grid}>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><Link href="/dashboard" className={styles.card}>
        <h2>Clients</h2>
        <div className={styles.visual}>
          <video ref={video} className={styles.video} style={{ opacity: blocked ? 0 : 1 }} src={media + "clients-mobile-v2.mp4"} muted loop autoPlay playsInline preload="auto" aria-hidden="true" />
          {blocked && <img className={styles.video} style={{ position: "absolute", inset: 0 }} src={media + "clients-mobile-fallback.webp"} alt="" aria-hidden="true" />}
          <span className={styles.shade} />
          {plus}
        </div>
        <p>{english ? <><strong>For individual investors, businesses, analysts, and professional investors who want to understand companies and analyze results faster.</strong> Clear explanations for those getting started, and organized research for professionals and teams who need greater speed.</> : <><strong>Para investidores pessoa física, empresas, analistas e investidores profissionais que querem entender as empresas e analisar resultados com mais agilidade.</strong> Explicações claras para quem está começando e pesquisa organizada para profissionais e equipes que precisam ganhar tempo.</>}</p>
      </Link></motion.div>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><Link href="/dashboard" className={styles.card}>
        <h2>Services</h2>
        <div className={styles.visual} style={{ backgroundImage: `url(${media}services.jpg)`, backgroundSize: "cover", backgroundPosition: "center" }}>
          <canvas ref={canvas} className={styles.canvas} aria-hidden="true" />
          {plus}
        </div>
        <p>{english ? <><strong>Find reports, analyze results, and compare companies in one place.</strong> Automatic document search, AI analysis, fundamental scores, an aggregated table, and saved history help you spend less time reading and quickly revisit previous results.</> : <><strong>Encontre relatórios, analise resultados e compare empresas em um só lugar.</strong> Busca automática de documentos, análise por IA, notas dos fundamentos, tabela agregada e histórico salvo para gastar menos tempo lendo e consultar resultados anteriores com agilidade.</>}</p>
      </Link></motion.div>
    </div>
  </motion.section>;
}
