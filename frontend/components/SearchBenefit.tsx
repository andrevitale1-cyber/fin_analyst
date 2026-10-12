"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { Pause, Play } from "lucide-react";
import styles from "./SearchBenefit.module.css";

export default function SearchBenefit({ locale }: { locale: string }) {
  const card = useRef<HTMLElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const visible = useInView(card, { amount: .3 });
  const reduced = useReducedMotion();
  const [playing, setPlaying] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const english = locale === "en";

  useEffect(() => {
    const element = video.current;
    if (!element) return;
    if (visible && !reduced && !userPaused) void element.play().catch(() => {});
    else element.pause();
  }, [visible, reduced, userPaused]);

  return <motion.article ref={card} className={styles.card} initial={reduced ? false : { opacity: 0, y: 32 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .15 }} transition={{ duration: .6 }}>
    <div className={styles.media}>
      <video ref={video} src="/benefits/company-search-six-seconds.mp4#t=0.01" muted loop playsInline preload="metadata" aria-label={english ? "Company details and official report search demonstration" : "Demonstração do preenchimento da empresa e busca do documento oficial"}
        onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} />
      <button type="button" className={styles.control} aria-label={playing ? (english ? "Pause demonstration" : "Pausar demonstração") : (english ? "Play demonstration" : "Reproduzir demonstração")} onClick={() => {
        const element = video.current;
        if (!element) return;
        setUserPaused(playing);
        if (playing) element.pause(); else void element.play().catch(() => {});
      }}>{playing ? <Pause size={18} /> : <Play size={18} />}</button>
    </div>
    <div className={styles.copy}>
      <p className={styles.label}>{english ? "AUTOMATIC SEARCH" : "BUSCA AUTOMÁTICA"}</p>
      <h3>{english ? "Find the report without the manual search" : "Encontre o balanço sem procurar manualmente"}</h3>
      <p>{english ? "Enter the company, year and quarter. FinAnalyzer finds the official document for that period so you can start your analysis, without having to locate and download the file yourself." : "Informe a empresa, o ano e o trimestre. O FinAnalyzer busca o documento oficial do período para você começar a análise, sem precisar localizar e baixar o arquivo por conta própria."}</p>
    </div>
  </motion.article>;
}
