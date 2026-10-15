"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useReducedMotion, useInView } from "framer-motion";
import useVideoPlayback from "./useVideoPlayback";
import styles from "./AudienceCards.module.css";

const media = "/reference/clearstreet/";

export default function AudienceCards({ locale }: { locale: string }) {
  const video = useRef<HTMLVideoElement>(null);
  const section = useRef<HTMLElement>(null);
  const english = locale === "en";
  const [desktop, setDesktop] = useState(false);
  const reduce = useReducedMotion();
  const visible = useInView(section, { amount: .05 });
  useVideoPlayback(video, visible);
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

  return <motion.section id="clients" ref={section} className={styles.section} style={reduce ? undefined : { opacity: exitOpacity }} aria-label={english ? "Who FinAnalyzer is for" : "Para quem é o FinAnalyzer"}>
    <div className={styles.grid}>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><article className={styles.card}>
        <h2>Clients</h2>
        <div className={styles.visual}>
          <video ref={video} className={styles.video} src={media + "clients.mp4#t=0.01"} width="580" height="500" muted loop autoPlay playsInline preload="auto" aria-hidden="true" />
        </div>
        <p>{english ? <><strong>For individual investors, businesses, analysts, and professional investors who want to understand companies and analyze results faster.</strong> Clear explanations for those getting started, and organized research for professionals and teams who need greater speed.</> : <><strong>Para investidores pessoa física, empresas, analistas e investidores profissionais que querem entender as empresas e analisar resultados com mais agilidade.</strong> Explicações claras para quem está começando e pesquisa organizada para profissionais e equipes que precisam ganhar tempo.</>}</p>
      </article></motion.div>
      <motion.div style={{ y: revealY, opacity: revealOpacity, minWidth: 0 }}><article className={styles.card}>
        <h2>Services</h2>
        <div className={styles.visual}>
          <img className={styles.video} src="/benefits/services-card.png" alt="" width="1600" height="1232" loading="lazy" />
        </div>
        <p>{english ? <><strong>Find reports, analyze results, and compare companies in one place.</strong> Automatic document search, AI analysis, fundamental scores, an aggregated table, and saved history help you spend less time reading and quickly revisit previous results.</> : <><strong>Encontre relatórios, analise resultados e compare empresas em um só lugar.</strong> Busca automática de documentos, análise por IA, notas dos fundamentos, tabela agregada e histórico salvo para gastar menos tempo lendo e consultar resultados anteriores com agilidade.</>}</p>
      </article></motion.div>
    </div>
  </motion.section>;
}
