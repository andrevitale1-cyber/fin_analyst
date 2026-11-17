import { hasTrackingConsent } from "./consent";

const PIXEL_ID = "a2_jzugsawslzp2";
type Pixel = ((...args: unknown[]) => void) & {
  sendEvent?: (...args: unknown[]) => void;
  callQueue: unknown[][];
};

declare global {
  interface Window { rdt?: Pixel }
}

let lastPath: string | undefined;
const conversions = new Set<string>();
// Do not report historical accounts as new registrations when tracking is introduced.
const CONVERSIONS_STARTED_AT = Date.parse("2026-11-16T00:10:00Z");

async function hashValue(value: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
}

export async function hashRedditEmail(email?: string) {
  return email?.trim() ? hashValue(email.trim().toLowerCase()) : undefined;
}

export async function signupConversionId(userId: string, createdAt: number) {
  return Number.isFinite(createdAt) && createdAt >= CONVERSIONS_STARTED_AT && createdAt <= Date.now()
    ? hashValue("reddit-signup:" + userId) : undefined;
}

export function trackRedditVisit(path: string, email?: string) {
  if (!hasTrackingConsent() || !["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname) || path === lastPath) return;
  if (!window.rdt) {
    const pixel = function (...args: unknown[]) {
      if (pixel.sendEvent) pixel.sendEvent(...args);
      else pixel.callQueue.push(args);
    } as Pixel;
    pixel.callQueue = [];
    window.rdt = pixel;
    const script = document.createElement("script");
    script.src = `https://www.redditstatic.com/ads/pixel.js?pixel_id=${PIXEL_ID}`;
    script.async = true;
    document.head.appendChild(script);
    pixel("init", PIXEL_ID);
  }
  lastPath = path;
  // Only accept a pre-hashed match key; never send an account email in plaintext.
  const matching = email && /^[a-f0-9]{64}$/.test(email) ? { email } : {};
  window.rdt("track", "PageVisit", matching);
}

export function trackRedditConversion(event: "SignUp" | "Purchase" | "AddToCart", data: { conversionId: string; value?: number; currency?: string }, email?: string) {
  if (!["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname)
      || !/^[a-f0-9]{64}$/.test(data.conversionId)
      || (event === "Purchase" && (!Number.isFinite(data.value) || Number(data.value) <= 0 || data.currency !== "BRL"))) return;
  const key = `reddit:${event}:${data.conversionId}`;
  if (conversions.has(key)) return;
  try { if (localStorage.getItem(key)) return; } catch { /* Storage can be blocked; keep in-memory deduplication. */ }
  trackRedditVisit(window.location.pathname);
  const matching = email && /^[a-f0-9]{64}$/.test(email) ? { email } : {};
  window.rdt?.("track", event, { ...data, ...matching });
  conversions.add(key);
  try { localStorage.setItem(key, "1"); } catch { /* See storage fallback above. */ }
}

export function requestRedditGetStarted() {
  if (!hasTrackingConsent() || !["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname)) return;
  const event_id = crypto.randomUUID();
  void (async () => {
    const conversionId = await hashValue("reddit-click:" + event_id);
    trackRedditConversion("AddToCart", {conversionId});
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
    await fetch(`${base}/api/conversions/reddit`, {method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({event:"AddToCart",event_id}),keepalive:true});
  })().catch(() => { /* Tracking must not interrupt navigation. */ });
}
