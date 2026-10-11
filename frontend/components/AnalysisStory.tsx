"use client";

import { useCallback, useEffect, useRef } from "react";
import { motion, useMotionValueEvent, useReducedMotion, useScroll, useTransform, type MotionValue } from "framer-motion";
import styles from "./AnalysisStory.module.css";

const copy = {
  pt: [
    { title: "Entender os resultados de uma empresa ainda exige navegar por relatórios extensos.", description: "" },
    { title: "Entre PDFs, planilhas e indicadores, o que importa pode se perder.", description: "Receita, lucro, dívida e rentabilidade precisam ser vistos em conjunto." },
    { title: "Mais tempo reunindo informações. Menos tempo compreendendo o negócio.", description: "" },
  ],
  en: [
    { title: "Understanding company results still means navigating lengthy reports.", description: "" },
    { title: "Between PDFs, spreadsheets and metrics, what matters can get lost.", description: "Revenue, income, debt and profitability need to be seen together." },
    { title: "More time gathering information. Less time understanding the business.", description: "" },
  ],
};

function Scene({ index, progress, title, description, reduced }: { index: number; progress: MotionValue<number>; title: string; description: string; reduced: boolean }) {
  const video = useRef<HTMLVideoElement>(null);
  const start = index / 3;
  const end = (index + 1) / 3;
  const opacity = useTransform(progress, [start, start + .045, end - .045, end], index === 0 ? [1, 1, 1, 0] : index === 2 ? [0, 1, 1, 1] : [0, 1, 1, 0]);
  const y = useTransform(progress, [start, end], [20, -20]);
  const shade = useTransform(progress, [start, start + .08, end - .08, end], [.75, .28, .28, .75]);
  const syncVideo = useCallback((value: number) => {
    const element = video.current;
    if (!element) return;
    if (!reduced && !window.matchMedia("(prefers-reduced-motion: reduce)").matches && value >= start && value < end) void element.play().catch(() => {});
    else element.pause();
  }, [reduced, start, end]);
  useMotionValueEvent(progress, "change", syncVideo);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => syncVideo(progress.get());
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, [progress, syncVideo]);

  return <motion.div className={styles.scene} style={reduced ? undefined : { opacity }}>
    <video ref={video} className={styles.video} src={`/reference/clearstreet/story-${index + 1}.mp4#t=0.01`} muted loop playsInline preload="metadata" aria-hidden="true" onLoadedData={() => syncVideo(progress.get())} />
    <motion.div className={styles.shade} style={reduced ? undefined : { opacity: shade }} />
    <motion.div className={styles.text} style={reduced ? undefined : { y }}>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </motion.div>
  </motion.div>;
}

export default function AnalysisStory({ locale }: { locale: string }) {
  const section = useRef<HTMLElement>(null);
  const reduced = useReducedMotion() ?? false;
  const english = locale === "en";
  const { scrollYProgress } = useScroll({ target: section, offset: ["start start", "end end"] });
  return <>
    <section ref={section} className={styles.story} aria-label={english ? "From reports to understanding" : "Dos relatórios à compreensão"}>
      <div className={styles.sticky}>
        {copy[english ? "en" : "pt"].map((scene, index) => <Scene key={index} index={index} progress={scrollYProgress} {...scene} reduced={reduced} />)}
      </div>
    </section>
    <section className={styles.solution}>
      <motion.div initial={reduced ? false : { opacity: 0, y: 35 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .35 }} transition={{ duration: .8 }}>
        <h2>{english ? "This is where" : "É aqui que o"}<br /><span>FinAnalyzer</span><br />{english ? "comes in." : "entra."}</h2>
        <p>{english ? "Official reports. Organized fundamentals. A clearer view of company results." : "Relatórios oficiais. Fundamentos organizados. Mais clareza sobre os resultados das empresas."}</p>
      </motion.div>
    </section>
  </>;
}
