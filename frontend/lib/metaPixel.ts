export const META_PIXEL_ID = "2311081823088345";
const HOSTS = ["finanalyser.com.br", "www.finanalyser.com.br"];

type Fbq = ((...args: unknown[]) => void) & { queue?: unknown[][]; loaded?: boolean; callMethod?: (...args: unknown[]) => void };
declare global { interface Window { fbq?: Fbq; _fbq?: Fbq } }

// Loads only inside <CookieConsent> after "granted"; ignores non-production hosts.
export function loadMetaPixel() {
  if (typeof window === "undefined" || !HOSTS.includes(window.location.hostname) || window.fbq) return;
  const fbq: Fbq = function (...args: unknown[]) { fbq.callMethod ? fbq.callMethod(...args) : fbq.queue!.push(args); };
  fbq.queue = []; fbq.loaded = true;
  window.fbq = window._fbq = fbq;
  const script = document.createElement("script");
  script.async = true; script.src = "https://connect.facebook.net/en_US/fbevents.js";
  document.head.appendChild(script);
  fbq("init", META_PIXEL_ID);
}

export function trackMetaPageView() { window.fbq?.("track", "PageView"); }

// One CompleteRegistration per account; accounts older than 10 min are not new sign-ups.
export function trackMetaSignup(userId: string, createdAt: number) {
  if (!window.fbq || !(Date.now() - createdAt < 10 * 60 * 1000)) return;
  const key = `meta:signup:${userId}`;
  try { if (localStorage.getItem(key)) return; localStorage.setItem(key, "1"); } catch { /* Blocked storage: skip rather than double-count. */ return; }
  window.fbq("track", "CompleteRegistration", {}, { eventID: `signup-${userId}` });
}
