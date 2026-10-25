"use client";

import { UserButton } from "@clerk/nextjs";
import { useLocale, useTranslations } from "next-intl";
import { BarChart3, BookOpen, ChevronLeft, History, LayoutDashboard, Menu, Table2, X } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";

export default function DashboardSidebar({ active, open, collapsed, onClose, onCollapse, onNavigate, children }: {
  active: string; open: boolean; collapsed: boolean; onClose: () => void; onCollapse: (value: boolean) => void;
  onNavigate: (view: "dashboard" | "table" | "history" | "reports") => void; children?: React.ReactNode;
}) {
  const locale = useLocale();
  const t = useTranslations("Dashboard");
  const items = [["dashboard", LayoutDashboard, "newAnalysis"], ["table", Table2, "aggregatedTable"], ["history", History, "history"], ["reports", BookOpen, "fullReports"]] as const;
  return <>
    {open && <div className="fixed inset-0 z-40 bg-black/60 md:hidden" onClick={onClose} />}
    <aside aria-label={locale === "en" ? "Main navigation" : "Navegação principal"} className={`fixed inset-y-0 left-0 z-50 flex w-72 shrink-0 flex-col border-r border-white/10 bg-[#0b1526] p-6 text-white transition-transform md:sticky md:top-0 md:h-screen md:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"} ${collapsed ? "md:w-20 md:px-3" : ""}`}>
      <div className="mb-10 flex items-center justify-between gap-2">
        <a href={`/${locale}`} aria-label={locale === "en" ? "FinAnalyzer home" : "Início FinAnalyzer"} className="flex min-w-0 items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-sky-400">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-700"><BarChart3 size={21} /></span>
          {!collapsed && <span className="text-xl font-bold tracking-tight">FinAnalyzer<span className="text-blue-500">.AI</span></span>}
        </a>
        <button onClick={onClose} aria-label={locale === "en" ? "Close menu" : "Fechar menu"} className="p-1 text-slate-400 md:hidden"><X size={21}/></button>
        {!collapsed && <button onClick={() => onCollapse(true)} aria-label={locale === "en" ? "Collapse menu" : "Recolher menu"} className="hidden p-1 text-slate-400 hover:text-white md:block"><ChevronLeft size={20}/></button>}
      </div>
      {collapsed && <button onClick={() => onCollapse(false)} aria-label={t("sidebar.menu")} className="mb-4 hidden h-10 items-center justify-center rounded-xl hover:bg-white/10 md:flex"><Menu size={20}/></button>}
      <nav className="space-y-2">{items.map(([view, Icon, label]) => <button key={view} onClick={() => { onClose(); onNavigate(view); }} aria-current={active === view ? "page" : undefined} title={t(`nav.${label}`)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${collapsed ? "justify-center" : "text-left"} ${active === view ? "bg-sky-500/15 text-sky-300" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}><Icon size={20}/>{!collapsed && t(`nav.${label}`)}</button>)}</nav>
      <div className="mt-auto">{!collapsed && children}</div>
      <div className="mt-4 space-y-3 border-t border-white/10 pt-4">
        <LanguageSwitcher compact={collapsed} dark />
        <UserButton showName={!collapsed} appearance={{elements:{userButtonOuterIdentifier:"!text-white", avatarBox:"h-9 w-9"}}}/>
      </div>
    </aside>
  </>;
}
