"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, BarChart3, ChevronDown, Search, X } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./LandingIntro.module.css";

export default function LandingIntro({ locale }: { locale: string }) {
  const english = locale === "en";
  const [menu, setMenu] = useState<"clients" | "services" | "mobile" | null>(null);
  const header = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const close = () => setMenu(null);
  const links = [
    { href: "#funcionalidades", text: english ? "Features" : "Recursos" },
    { href: "#meta-analysis-heading", text: english ? "AI analysis" : "Análise IA" },
    { href: "#aggregated-table-heading", text: english ? "Company comparison" : "Comparação de empresas" },
  ];

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
          <BarChart3 aria-hidden="true" size={24} /><span>FinAnalyzer<span className={styles.ai}>.AI</span></span>
        </Link>
        <div className={styles.desktopLinks}>
          <button aria-expanded={menu === "clients"} aria-controls="landing-clients" onClick={() => setMenu(menu === "clients" ? null : "clients")}>{english ? "Clients" : "Clientes"}<ChevronDown size={12} /></button>
          <button aria-expanded={menu === "services"} aria-controls="landing-services" onClick={() => setMenu(menu === "services" ? null : "services")}>{english ? "Services" : "Serviços"}<ChevronDown size={12} /></button>
          <a href="#meta-analysis-heading" onClick={close}>{english ? "AI analysis" : "Análise IA"}</a>
          <a href="#planos" onClick={close}>{english ? "Pricing" : "Planos"}</a>
          <Link href="/dashboard">FinAnalyzer AI</Link>
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
      {menu === "clients" && <div id="landing-clients" className={styles.dropdown}>
        <a href="#clients" onClick={close}>{english ? "Individual investors" : "Investidores pessoa física"}</a>
        <a href="#clients" onClick={close}>{english ? "Professional investors and businesses" : "Investidores profissionais e empresas"}</a>
      </div>}
      {menu === "services" && <div id="landing-services" className={styles.dropdown}>
        {links.map(link => <a key={link.href} href={link.href} onClick={close}>{link.text}</a>)}
        <Link href="/dashboard" onClick={close}>{english ? "Search reports and call transcripts" : "Buscar resultados e transcrições"}</Link>
      </div>}
      {menu === "mobile" && <div id="landing-mobile-menu" className={styles.mobileMenu}>
        <a href="#clients" onClick={close}>{english ? "Clients" : "Clientes"}</a>
        {links.map(link => <a key={link.href} href={link.href} onClick={close}>{link.text}</a>)}
        <a href="#planos" onClick={close}>{english ? "Pricing" : "Planos"}</a>
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
    </section>
  </>;
}
