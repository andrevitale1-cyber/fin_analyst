"use client";

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from '../i18n/routing';
import { useTransition } from 'react';

export default function LanguageSwitcher() {
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
    <div className="relative inline-block text-left">
      <select
        className="appearance-none bg-[#161b22] text-gray-400 hover:text-white border border-gray-700 rounded-lg pl-3 pr-8 py-1.5 text-xs font-bold uppercase tracking-wider outline-none cursor-pointer focus:border-blue-500 transition-colors shadow-sm"
        value={locale}
        onChange={onSelectChange}
        disabled={isPending}
      >
        <option value="pt" className="bg-[#161b22] text-gray-200">PT-BR</option>
        <option value="en" className="bg-[#161b22] text-gray-200">EN-US</option>
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
      </div>
    </div>
  );
}
