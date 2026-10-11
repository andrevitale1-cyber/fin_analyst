"use client";

import { useCallback, useEffect, useRef, type CSSProperties } from "react";
import { motion, useInView, useMotionValueEvent, useReducedMotion, useScroll, useTransform, type MotionValue } from "framer-motion";
import styles from "./AnalysisStory.module.css";

const copy = {
  pt: [
    { title: "Entender os resultados de uma empresa ainda exige navegar por relatórios extensos.", description: "" },
    { title: "Quando são várias empresas, ler, comparar e analisar cada resultado exige ainda mais tempo.", description: "" },
    { title: "Mais agilidade para chegar ao que importa. Mais clareza para entender cada empresa.", description: "" },
  ],
  en: [
    { title: "Understanding company results still means navigating lengthy reports.", description: "" },
    { title: "Across multiple companies, reading, comparing and analyzing every result takes even more time.", description: "" },
    { title: "Get to what matters sooner. Understand each company more clearly.", description: "" },
  ],
};

function Scene({ index, progress, title, description, reduced }: { index: number; progress: MotionValue<number>; title: string; description: string; reduced: boolean }) {
  const video = useRef<HTMLVideoElement>(null);
  const start = index / 3;
  const end = (index + 1) / 3;
  const opacity = useTransform(progress, [start, start + .001, end - .001, end], index === 0 ? [1, 1, 1, 0] : index === 2 ? [0, 1, 1, 1] : [0, 1, 1, 0]);
  const textOpacity = useTransform(progress, [start, start + .06, end - .06, end], [0, 1, 1, 0]);
  const y = useTransform(progress, [start, end], ["50svh", "-50svh"]);
  const shade = useTransform(progress, value => 1 - Math.sin(Math.max(0, Math.min(1, (value - start) * 3)) * Math.PI));
  const shadeColor = useTransform(progress, [0, 1 / 6, 1 / 6 + .001, 1], ["#2e21de", "#2e21de", "#040313", "#040313"]);
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
    <video ref={video} className={styles.video} muted loop playsInline preload="metadata" aria-hidden="true" onLoadedData={() => syncVideo(progress.get())}>
      <source media="(min-width: 744px)" src={`/reference/clearstreet/story-${index + 1}-desktop.mp4#t=0.01`} type="video/mp4" />
      <source src={`/reference/clearstreet/story-${index + 1}.mp4#t=0.01`} type="video/mp4" />
    </video>
    <motion.div className={styles.shade} style={reduced ? undefined : { opacity: shade, backgroundColor: index === 0 ? shadeColor : "#040313" }} />
    <motion.div className={styles.text} style={reduced ? undefined : { y, opacity: textOpacity }}>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </motion.div>
  </motion.div>;
}

export default function AnalysisStory({ locale }: { locale: string }) {
  const section = useRef<HTMLElement>(null);
  const solution = useRef<HTMLElement>(null);
  const solutionVisible = useInView(solution, { amount: .15 });
  const reduced = useReducedMotion() ?? false;
  const english = locale === "en";
  const { scrollYProgress } = useScroll({ target: section, offset: ["start start", "end end"] });
  return <>
    <section ref={section} className={styles.story} aria-label={english ? "From reports to understanding" : "Dos relatórios à compreensão"}>
      <div className={styles.sticky}>
        {copy[english ? "en" : "pt"].map((scene, index) => <Scene key={index} index={index} progress={scrollYProgress} {...scene} reduced={reduced} />)}
      </div>
    </section>
    <motion.section ref={solution} data-active={solutionVisible && !reduced} className={styles.solution} initial="idle" animate={reduced || solutionVisible ? "active" : "idle"}>
      <motion.div className={styles.rectangles} aria-hidden="true" variants={{ idle: { opacity: 0, scale: .85 }, active: { opacity: 1, scale: 1 } }} transition={{ duration: reduced ? 0 : 2.8, ease: "easeOut" }}>
        <div className={styles.ring}>
          {Array.from({ length: 24 }, (_, index) => <span key={index} className={styles.block} style={{ "--angle": `${index * 15}deg`, "--phase": `${index * -.14}s` } as CSSProperties} />)}
        </div>
      </motion.div>
      <motion.div className={styles.solutionText} variants={{ idle: { opacity: 0, y: 20 }, active: { opacity: 1, y: 0 } }} transition={{ duration: reduced ? 0 : 1, delay: reduced ? 0 : .4 }}>
        <h2>{english ? "This is where" : "É aqui que o"}<br /><span>FinAnalyzer {english ? "comes in." : "entra."}</span></h2>
      </motion.div>
      <div className={styles.foreground} aria-hidden="true">
        {Array.from({ length: 6 }, (_, index) => <span key={index} className={styles.frontBlock} style={{ "--index": index, "--phase": `${index * -.56}s` } as CSSProperties} />)}
      </div>
    </motion.section>
  </>;
}
