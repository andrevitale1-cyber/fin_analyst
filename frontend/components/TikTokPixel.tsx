"use client";

import Script from "next/script";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { TIKTOK_BOOTSTRAP, trackTikTokVisit } from "../lib/tiktokPixel";

export default function TikTokPixel() {
  const pathname = usePathname();
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setEnabled(["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname));
  }, []);

  useEffect(() => {
    if (ready) trackTikTokVisit(pathname);
  }, [pathname, ready]);

  return enabled ? <Script id="tiktok-pixel-bootstrap" strategy="afterInteractive" onReady={() => setReady(true)}>{TIKTOK_BOOTSTRAP}</Script> : null;
}
