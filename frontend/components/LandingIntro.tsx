"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "framer-motion";
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowDown, BarChart3, BookOpen, Clock3, Files, History, Link2, MessageSquareText, Search, X } from "lucide-react";
import { Link } from "@/i18n/routing";
import "lenis/dist/lenis.css";
import styles from "./LandingIntro.module.css";

export default function LandingIntro({ locale }: { locale: string }) {
  const english = locale === "en";
  const [menu, setMenu] = useState<"mobile" | null>(null);
  const header = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const marquee = useRef<HTMLDivElement>(null);
  const marqueeVisible = useInView(marquee);
  const close = () => setMenu(null);
  const highlights = english ? [
    { title: "Less reading", description: "AI highlights what matters", icon: Clock3 },
    { title: "More clarity", description: "Company reports, explained", icon: BookOpen },
    { title: "Faster comparisons", description: "Key fundamentals side by side", icon: Files },
    { title: "Research, saved", description: "History ready to revisit", icon: History },
    { title: "Beyond the numbers", description: "Call insights and management tone", icon: MessageSquareText },
    { title: "Check the source", description: "Links to official documents", icon: Link2 },
  ] : [
    { title: "Menos leitura", description: "A IA destaca o que importa", icon: Clock3 },
    { title: "Mais clareza", description: "Resultados explicados em contexto", icon: BookOpen },
    { title: "Compare mais rápido", description: "Fundamentos lado a lado", icon: Files },
    { title: "Pesquisa sempre à mão", description: "Histórico pronto para consultar", icon: History },
    { title: "Além dos números", description: "Análise do call e do tom da gestão", icon: MessageSquareText },
    { title: "Confira a fonte", description: "Links para documentos oficiais", icon: Link2 },
  ];
  const links = [
    { href: "#clients", text: english ? "Clients" : "Clientes" },
    { href: "#funcionalidades", text: english ? "Benefits" : "Benefícios" },
    { href: "#aggregated-table-heading", text: english ? "Aggregated table" : "Tabela agregada" },
    { href: "#meta-analysis-heading", text: english ? "AI analysis" : "Análise IA" },
    { href: "#call-analysis-heading", text: "Calls" },
    { href: "#planos", text: english ? "Pricing" : "Planos" },
  ];

  useEffect(() => {
    // Match Clear Street's wheel damping; keep touch scrolling native on mobile.
    const query = window.matchMedia("(min-width: 1024px) and (hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    let cleanup = () => {};
    const sync = () => {
      cleanup();
      if (!query.matches) { cleanup = () => {}; return; }
      gsap.registerPlugin(ScrollTrigger);
      const scroll = new Lenis({ lerp: .1, wheelMultiplier: 1, smoothWheel: true, syncTouch: false });
      const tick = (time: number) => scroll.raf(time * 1000);
      scroll.on("scroll", ScrollTrigger.update);
      gsap.ticker.add(tick);
      cleanup = () => { gsap.ticker.remove(tick); scroll.destroy(); };
    };
    sync();
    query.addEventListener("change", sync);
    return () => { query.removeEventListener("change", sync); cleanup(); };
  }, []);

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1024px)");
    desktop.addEventListener("change", close);
    return () => desktop.removeEventListener("change", close);
  }, []);

  useEffect(() => {
    if (!menu) return;
    const outside = (event: PointerEvent) => { if (!header.current?.contains(event.target as Node)) close(); };
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") { close(); menuButton.current?.focus(); }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", keyboard);
    return () => { document.removeEventListener("pointerdown", outside); document.removeEventListener("keydown", keyboard); };
  }, [menu]);

  return <>
    <header ref={header} className={styles.navigation}>
      <nav className={styles.pill} aria-label={english ? "Main navigation" : "Navegação principal"}>
        <Link href="/" className={styles.brand} aria-label="FinAnalyzer home" onClick={close}>
          <BarChart3 aria-hidden="true" size={24} /><span>FinAnalyzer</span>
        </Link>
        <div className={styles.desktopLinks}>
          {links.map(link => <a key={link.href} href={link.href} onClick={close}>{link.text}</a>)}
        </div>
        <div className={styles.actions}>
          <Link href="/dashboard" className={styles.search} aria-label={english ? "Search a company" : "Buscar uma empresa"}><Search size={21} /></Link>
          <Link href="/dashboard" className={styles.login}>{english ? "Sign in" : "Entrar"}</Link>
          <Link href="/dashboard" className={styles.primary}>{english ? "Get started" : "Começar"}</Link>
        </div>
        <button ref={menuButton} className={styles.menuButton} aria-expanded={menu === "mobile"} aria-controls="landing-mobile-menu" onClick={() => setMenu(menu === "mobile" ? null : "mobile")}>
          {menu === "mobile" ? <><X size={15} /><span className={styles.srOnly}>{english ? "Close menu" : "Fechar menu"}</span></> : "Menu"}
        </button>
      </nav>
      {menu === "mobile" && <div id="landing-mobile-menu" className={styles.mobileMenu} data-lenis-prevent>
        {links.map(link => <a key={link.href} href={link.href} onClick={close}>{link.text}</a>)}
        <Link href="/dashboard" onClick={close}>{english ? "Sign in" : "Entrar"}</Link>
        <Link href="/dashboard" className={styles.primary} onClick={close}>{english ? "Analyze a company" : "Analisar uma empresa"}</Link>
      </div>}
    </header>
    <section className={styles.hero} aria-labelledby="landing-title">
      <div className={styles.inner}>
        <div className={styles.copy}>
          <h1 id="landing-title">{english ? "Speed, transparency and clarity" : "Agilidade, transparência e clareza"}<br className={styles.headlineBreak} /> {english ? "for every investor." : "para cada investidor."}</h1>
          <p>{english
            ? "Official reports, AI analysis, company comparisons and saved research in one platform. Understand results faster and revisit every analysis with ease."
            : "Relatórios oficiais, análise por IA, comparação de empresas e histórico em uma plataforma. Entenda os resultados mais rápido e consulte cada análise com facilidade."}</p>
          <a href="#clients" className={styles.scrollDown} aria-label={english ? "Explore FinAnalyzer" : "Conhecer o FinAnalyzer"}><ArrowDown size={26} /></a>
        </div>
      </div>
      <div ref={marquee} className={styles.marquee} data-visible={marqueeVisible} role="region" aria-label={english ? "What FinAnalyzer helps you do" : "Como o FinAnalyzer ajuda você"}>
        <div className={styles.track}>
          {[false, true].map(duplicate => <ul key={String(duplicate)} aria-hidden={duplicate || undefined}>
            {highlights.map(({ title, description, icon: Icon }) => <li key={title}>
              <span className={styles.marqueeIcon} aria-hidden="true"><Icon strokeWidth={1} /></span>
              <div><p>{title}</p><span>{description}</span></div>
            </li>)}
          </ul>)}
        </div>
      </div>
    </section>
  </>;
}
