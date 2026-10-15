"use client";

import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import useVideoPlayback from "./useVideoPlayback";
import styles from "./SearchBenefit.module.css";

export default function SearchBenefit({ locale }: { locale: string }) {
  const card = useRef<HTMLElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const visible = useInView(card, { amount: .3 });
  const reduced = useReducedMotion();
  const english = locale === "en";
  useVideoPlayback(video, visible);

  return <motion.article ref={card} className={styles.card} initial={reduced ? false : { opacity: 0, y: 32 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .15 }} transition={{ duration: .6 }}>
    <div className={styles.media}>
      <video ref={video} src="/benefits/company-search-loop-6800ms.mp4#t=0.01" width="1280" height="720" muted loop playsInline autoPlay preload="auto" aria-label={english ? "Company details and official report search demonstration" : "Demonstração do preenchimento da empresa e busca do documento oficial"} />
    </div>
    <div className={styles.copy}>
      <h3>{english ? "Find the report without the manual search" : "Encontre o balanço sem procurar manualmente"}</h3>
      <p>{english ? "Enter the company, year and quarter. FinAnalyzer finds the official document for that period so you can start your analysis, without having to locate and download the file yourself." : "Informe a empresa, o ano e o trimestre. O FinAnalyzer busca o documento oficial do período para você começar a análise, sem precisar localizar e baixar o arquivo por conta própria."}</p>
    </div>
  </motion.article>;
}
