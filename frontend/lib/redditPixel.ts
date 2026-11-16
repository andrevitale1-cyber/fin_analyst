const PIXEL_ID = "a2_jzugsawslzp2";
type Pixel = ((...args: unknown[]) => void) & {
  sendEvent?: (...args: unknown[]) => void;
  callQueue: unknown[][];
};

declare global {
  interface Window { rdt?: Pixel }
}

let lastPath: string | undefined;

export async function hashRedditEmail(email?: string) {
  if (!email?.trim()) return undefined;
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(email.trim().toLowerCase()));
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
}

export function trackRedditVisit(path: string, email?: string) {
  if (!["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname) || path === lastPath) return;
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
