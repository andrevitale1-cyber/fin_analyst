"use client";

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from '../i18n/routing';
import { useTransition } from 'react';

export default function LanguageSwitcher({ compact = false, dark = false }: { compact?: boolean; dark?: boolean }) {
  const [isPending, startTransition] = useTransition();
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const onSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextLocale = e.target.value;
    startTransition(() => {
      router.replace(pathname, { locale: nextLocale });
    });
  };

  return (
    <div className={`relative inline-block text-left ${compact ? "w-full" : ""}`}>
      <select
        aria-label={locale === "en" ? "Language" : "Idioma"}
        className={`appearance-none rounded-lg bg-transparent py-2 pl-2 pr-6 text-xs font-semibold outline-none cursor-pointer focus-visible:ring-2 focus-visible:ring-sky-500 transition-colors ${dark ? "text-slate-300 hover:bg-white/10" : "text-slate-600 hover:bg-slate-100"} ${compact ? "w-full" : ""}`}
        value={locale}
        onChange={onSelectChange}
        disabled={isPending}
      >
        <option value="pt" className="bg-white text-slate-900">PT</option>
        <option value="en" className="bg-white text-slate-900">EN</option>
      </select>
      <div className={`pointer-events-none absolute inset-y-0 right-0 flex items-center text-gray-500 ${compact ? "px-0" : "px-2"}`}>
        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
      </div>
    </div>
  );
}
