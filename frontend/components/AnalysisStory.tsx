"use client";

import { useLayoutEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CustomEase } from "gsap/CustomEase";
import { Link } from "@/i18n/routing";
import { ChevronRight } from "lucide-react";
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

export default function AnalysisStory({ locale }: { locale: string }) {
  const section = useRef<HTMLElement>(null);
  const reduced = useReducedMotion() ?? false;
  const english = locale === "en";

  useLayoutEffect(() => {
    const root = section.current;
    if (!root) return;
    gsap.registerPlugin(ScrollTrigger, CustomEase);
    const scenes = Array.from(root.querySelectorAll<HTMLDivElement>("[data-story-scene]"));
    const videos = scenes.map(scene => scene.querySelector("video")!);
    const panels = Array.from(root.querySelectorAll<HTMLDivElement>("[data-story-panel]"));
    const query = window.matchMedia("(min-width: 744px) and (hover: hover)");
    let disposed = false;
    const play = (video: HTMLVideoElement) => {
      video.muted = true;
      video.defaultMuted = true;
      video.playsInline = true;
      void video.play().catch(() => {});
    };
    const activate = (index: number) => {
      scenes.forEach((scene, i) => {
        scene.dataset.active = String(i === index);
        if (i === index && !document.hidden) play(videos[i]);
        else videos[i].pause();
      });
    };
    const resume = () => {
      const bounds = root.getBoundingClientRect();
      if (document.hidden || bounds.bottom <= 0 || bounds.top >= window.innerHeight) return;
      const index = scenes.findIndex(scene => scene.dataset.active === "true");
      if (index >= 0) play(videos[index]);
    };
    const sources = () => {
      videos.forEach((video, i) => {
        const src = `/reference/clearstreet/story-${i + 1}${query.matches ? "-desktop" : ""}.mp4#t=0.01`;
        if (video.getAttribute("src") !== src) {
          video.src = src;
          video.load();
        }
      });
      ScrollTrigger.refresh();
    };
    sources();
    const context = gsap.context(() => {
      const ease = CustomEase.create("finanalyzer-story-title", "M0,0 C0.202,0 0.253,1 0.5,1 0.672,1 0.819,0 1,0");
      panels.forEach((panel, index) => {
        ScrollTrigger.create({
          trigger: panel, start: "top bottom", end: "top top",
          onEnter: () => activate(index),
          onEnterBack: () => activate(index),
          onLeave: () => { if (index < videos.length - 1) videos[index].pause(); },
          onLeaveBack: () => { if (index < videos.length - 1) videos[index].pause(); },
          onRefresh: self => { if (self.isActive) activate(index); },
          onUpdate: self => {
            const opacity = index === videos.length - 1 && self.progress > .5 ? 0 : 1 - Math.sin(self.progress * Math.PI);
            scenes[index].style.setProperty("--overlay-opacity", reduced ? ".28" : opacity.toFixed(2));
            if (index === 0) scenes[0].style.setProperty("--overlay-color", self.progress > .5 ? "#040313" : "#2e21de");
          },
        });
        if (!reduced) gsap.fromTo(panel.querySelector("h2"), { y: 20, opacity: 0 }, {
          y: -20, opacity: 1, ease,
          scrollTrigger: { trigger: panel.querySelector("h2"), start: "top+=100px bottom", end: "top top", scrub: true, invalidateOnRefresh: true },
        });
      });
      ScrollTrigger.create({
        trigger: root, start: "top bottom", end: "bottom top",
        onEnterBack: resume,
        onLeave: () => videos.forEach(video => video.pause()),
        onLeaveBack: () => videos.forEach(video => video.pause()),
      });
    }, root);
    const visibility = () => { if (document.hidden) videos.forEach(video => video.pause()); else resume(); };
    videos.forEach(video => video.addEventListener("canplay", resume));
    document.addEventListener("touchstart", resume, { passive: true, capture: true });
    document.addEventListener("touchend", resume, { passive: true, capture: true });
    document.addEventListener("click", resume, true);
    document.addEventListener("visibilitychange", visibility);
    query.addEventListener("change", sources);
    const refresh = () => { if (!disposed) ScrollTrigger.refresh(); };
    window.addEventListener("pageshow", refresh);
    void document.fonts.ready.then(refresh);
    ScrollTrigger.refresh();
    return () => {
      disposed = true;
      context.revert();
      videos.forEach(video => { video.pause(); video.removeEventListener("canplay", resume); });
      document.removeEventListener("touchstart", resume, true);
      document.removeEventListener("touchend", resume, true);
      document.removeEventListener("click", resume, true);
      document.removeEventListener("visibilitychange", visibility);
      query.removeEventListener("change", sources);
      window.removeEventListener("pageshow", refresh);
    };
  }, [reduced, locale]);

  return <>
    <section ref={section} className={styles.story} aria-label={english ? "From reports to understanding" : "Dos relatórios à compreensão"}>
      <div className={styles.sticky}>
        {copy[english ? "en" : "pt"].map((_, index) => <div key={index} data-story-scene data-active={index === 0} className={styles.scene}>
          <video className={styles.video} src={`/reference/clearstreet/story-${index + 1}.mp4#t=0.01`} width="1920" height="1080" muted loop playsInline preload="auto" aria-hidden="true" />
        </div>)}
      </div>
      <div className={styles.titles}>
        {copy[english ? "en" : "pt"].map((scene, index) => <div key={index} data-story-panel className={styles.titlePanel}>
          <h2>{scene.title}</h2>
          {scene.description && <p>{scene.description}</p>}
        </div>)}
      </div>
    </section>
    <section className={styles.solution} aria-labelledby="first-analysis-heading">
      <div className={styles.solutionContent}>
        <h2 id="first-analysis-heading"><span>{english ? "Your next analysis" : "Sua próxima análise"}</span><br />{english ? "starts here." : "começa aqui."}</h2>
        <p>{english ? "Choose a company and a quarter. Let AI highlight what matters, and revisit your analysis whenever you need it." : "Escolha a empresa e o trimestre. A IA destaca o que importa, e você pode consultar sua análise quando precisar."}</p>
        <Link href="/dashboard" className={styles.solutionButton}>{english ? "Analyze my first company" : "Analisar minha primeira empresa"}<ChevronRight size={16} aria-hidden="true" /></Link>
        <img className={styles.solutionGlow} src="/reference/finup/first-analysis-glow.avif" width="1280" height="314" alt="" loading="lazy" />
      </div>
    </section>
  </>;
}
