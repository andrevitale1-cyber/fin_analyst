"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useMotionValueEvent, useReducedMotion, useScroll, useTransform, type MotionValue } from "framer-motion";
import useVideoPlayback from "./useVideoPlayback";
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

function Scene({ index, progress, reduced, mobile }: { index: number; progress: MotionValue<number>; reduced: boolean; mobile: boolean }) {
  const video = useRef<HTMLVideoElement>(null);
  const start = index / 3;
  const end = (index + 1) / 3;
  const shade = useTransform(progress, value => {
    const local = Math.max(0, Math.min(1, (value - start) * 3));
    return index === 2 && local > .5 ? 0 : 1 - Math.sin(local * Math.PI);
  });
  const shadeColor = useTransform(progress, [0, 1 / 6, 1 / 6 + .001, 1], ["#2e21de", "#2e21de", "#040313", "#040313"]);
  const [active, setActive] = useState(index === 0);
  useMotionValueEvent(progress, "change", value => setActive(value >= start && (index === 2 || value < end)));
  const blocked = useVideoPlayback(video, active);

  return <div className={styles.scene} style={{ display: active ? "block" : "none" }}>
    <video ref={video} className={styles.video} style={{ opacity: blocked ? 0 : 1 }} src={`/reference/clearstreet/story-${index + 1}${mobile ? "-mobile-v2" : "-desktop"}.mp4`} muted loop autoPlay playsInline preload="metadata" aria-hidden="true" />
    {blocked && <img className={styles.video} style={{ position: "absolute", inset: 0 }} src={`/reference/clearstreet/story-${index + 1}-mobile-fallback.webp`} alt="" aria-hidden="true" />}
    <motion.div className={styles.shade} style={reduced ? { opacity: .28 } : { opacity: shade, backgroundColor: index === 0 ? shadeColor : "#040313" }} />
  </div>;
}

function StoryTitle({ title, description, reduced }: { title: string; description: string; reduced: boolean }) {
  const panel = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: panel, offset: ["start end", "start start"] });
  const opacity = useTransform(scrollYProgress, [0, .12, .35, .68, .95, 1], [0, .65, 1, 1, .1, 0]);
  const y = useTransform(scrollYProgress, [0, 1], [20, -20]);
  return <div ref={panel} className={styles.titlePanel}>
    <motion.h2 style={reduced ? undefined : { opacity, y }}>{title}</motion.h2>
    {description && <p>{description}</p>}
  </div>;
}

export default function AnalysisStory({ locale }: { locale: string }) {
  const section = useRef<HTMLElement>(null);
  const solution = useRef<HTMLElement>(null);
  const solutionVideo = useRef<HTMLVideoElement>(null);
  const loopVideo = useRef<HTMLVideoElement>(null);
  const [introEnded, setIntroEnded] = useState(false);
  const [mobile, setMobile] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(max-width: 743px)");
    const sync = () => setMobile(query.matches);
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);
  const solutionVisible = useInView(solution, { amount: .15 });
  const reduced = useReducedMotion() ?? false;
  const english = locale === "en";
  useVideoPlayback(solutionVideo, solutionVisible && !introEnded);
  useVideoPlayback(loopVideo, solutionVisible && introEnded);
  const { scrollYProgress } = useScroll({ target: section, offset: ["start start", "end end"] });
  return <>
    <section ref={section} className={styles.story} aria-label={english ? "From reports to understanding" : "Dos relatórios à compreensão"}>
      <div className={styles.sticky}>
        {copy[english ? "en" : "pt"].map((_, index) => <Scene key={index} index={index} progress={scrollYProgress} reduced={reduced} mobile={mobile} />)}
      </div>
      <div className={styles.titles}>
        {copy[english ? "en" : "pt"].map((scene, index) => <StoryTitle key={index} {...scene} reduced={reduced} />)}
      </div>
    </section>
    <motion.section ref={solution} data-active={solutionVisible} className={styles.solution} initial="idle" animate={reduced || solutionVisible ? "active" : "idle"}>
      <video ref={solutionVideo} className={styles.solutionVideo} src="/benefits/finanalyzer-orbit-intro.mp4" muted playsInline preload="metadata" aria-hidden="true" onEnded={() => setIntroEnded(true)} />
      <video ref={loopVideo} className={styles.solutionVideo} style={{ opacity: introEnded ? 1 : 0 }} src="/benefits/finanalyzer-orbit-loop.mp4" muted loop playsInline preload="auto" aria-hidden="true" />
      <motion.div className={styles.solutionText} variants={{ idle: { opacity: 0, y: 20 }, active: { opacity: 1, y: 0 } }} transition={{ duration: reduced ? 0 : 1, delay: reduced ? 0 : .4 }}>
        <h2 aria-label={english ? "This is where FinAnalyzer comes in." : "É aqui que o FinAnalyzer entra."}>{english ? "This is where" : "É aqui que o"}<br /><span>FinAnalyzer</span><br />{english ? "comes in." : "entra."}</h2>
      </motion.div>
    </motion.section>
  </>;
}
