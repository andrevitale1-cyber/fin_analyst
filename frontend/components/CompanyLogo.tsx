"use client";

import { useState } from "react";
import { Building2 } from "lucide-react";
import { companyLogoSources } from "../lib/companyLogos";

type Props = { symbol?: string | null; company: string; small?: boolean; className?: string };

export default function CompanyLogo(props: Props) {
  const sources = companyLogoSources(props.symbol, props.company);
  return <LogoImage key={sources.join("|")} {...props} sources={sources} />;
}

function LogoImage({ company, small = false, className = "", sources }: Props & { sources: string[] }) {
  const [index, setIndex] = useState(0);
  const size = small ? 18 : 48;
  const style = `shrink-0 ${className || (small ? "h-[18px] w-[18px]" : "h-12 w-12 rounded-xl")}`;
  return sources[index]
    ? <img src={sources[index]} alt="" width={size} height={size} referrerPolicy="no-referrer" onError={() => setIndex(value => value + 1)} className={`object-contain ${style}`} />
    : <span aria-label={company} className={`flex items-center justify-center bg-sky-50 text-sky-800 ${style}`}><Building2 size={small ? 16 : 22} /></span>;
}
