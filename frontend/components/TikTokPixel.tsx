"use client";

import Script from "next/script";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { TIKTOK_BOOTSTRAP, trackTikTokVisit, requestTikTokEvent, trackTikTokConversion } from "../lib/tiktokPixel";

export default function TikTokPixel() {
  const pathname = usePathname();
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);
  const {getToken, userId, isLoaded} = useAuth();

  useEffect(() => {
    setEnabled(["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname));
  }, []);

  useEffect(() => {
    if (ready) trackTikTokVisit(pathname);
  }, [pathname, ready]);

  useEffect(() => {
    if (!enabled || !ready || !isLoaded) return;
    const send = async (event: Event) => {
      const body = (event as CustomEvent).detail;
      try {
        const token = body.event === "ViewContent" ? null : await getToken();
        if (!token && body.event !== "ViewContent") return;
        const base = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
        // Retry the same occurrence ID, never turn an analytics failure into a product error.
        for (let attempt = 0; attempt < 2; attempt++) {
          const response = await fetch(`${base}/api/conversions/tiktok${body.event === "ViewContent" ? "/content" : ""}`, {
            method: "POST", headers: {"Content-Type": "application/json", ...(token ? {Authorization: `Bearer ${token}`} : {})},
            body: JSON.stringify(body), keepalive: true,
          });
          if (response.ok) {
            const data = await response.json();
            if (data.event) trackTikTokConversion(data.event, data.event_id, data.properties);
            return;
          }
          if (response.status < 500) return;
        }
      } catch { /* Advertising must not interrupt analysis or checkout. */ }
    };
    window.addEventListener("finanalyser:tiktok", send);
    if (userId) {
      requestTikTokEvent("CompleteRegistration");
      requestTikTokEvent("FirstAnalysisCompleted");
    }
    return () => { window.removeEventListener("finanalyser:tiktok", send); };
  }, [enabled, ready, isLoaded, userId, getToken]);

  useEffect(() => {
    if (!ready) return;
    const pricing = document.getElementById("planos");
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        requestTikTokEvent("ViewContent", "premium_pricing");
        observer.disconnect();
      }
    }, {threshold: 0.15});
    if (pricing) observer.observe(pricing);
    return () => observer.disconnect();
  }, [ready, pathname]);

  return enabled ? <Script id="tiktok-pixel-bootstrap" strategy="afterInteractive" onReady={() => setReady(true)}>{TIKTOK_BOOTSTRAP}</Script> : null;
}
