"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, BarChart3, Search, X } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./LandingIntro.module.css";

export default function LandingIntro({ locale }: { locale: string }) {
  const english = locale === "en";
  const [menu, setMenu] = useState<"mobile" | null>(null);
  const header = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const close = () => setMenu(null);
  const links = [
    { href: "#clients", text: english ? "Clients" : "Clientes" },
    { href: "#funcionalidades", text: english ? "Benefits" : "Benefícios" },
    { href: "#aggregated-table-heading", text: english ? "Aggregated table" : "Tabela agregada" },
    { href: "#meta-analysis-heading", text: english ? "AI analysis" : "Análise IA" },
    { href: "#call-analysis-heading", text: "Calls" },
    { href: "#planos", text: english ? "Pricing" : "Planos" },
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
      {menu === "mobile" && <div id="landing-mobile-menu" className={styles.mobileMenu}>
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
    </section>
  </>;
}
