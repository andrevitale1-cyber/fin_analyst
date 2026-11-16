export const TIKTOK_PIXEL_ID = "DBT8JPJC77UEEP3E4PS0";

// Vendor bootstrap only; page events are sent separately for Next.js navigation.
export const TIKTOK_BOOTSTRAP = `!function(w,d,t){
w.TiktokAnalyticsObject=t;
var ttq=w[t]=w[t]||[];
ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie","holdConsent","revokeConsent","grantConsent"];
ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};
for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);
ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};
ttq.load=function(e,n){var r="https://analytics.tiktok.com/i18n/pixel/events.js",o=n&&n.partner;
ttq._i=ttq._i||{};ttq._i[e]=[];ttq._i[e]._u=r;ttq._t=ttq._t||{};ttq._t[e]=+new Date;ttq._o=ttq._o||{};ttq._o[e]=n||{};
n=d.createElement("script");n.type="text/javascript";n.async=!0;n.src=r+"?sdkid="+e+"&lib="+t;
e=d.getElementsByTagName("script")[0];e.parentNode.insertBefore(n,e)};
ttq.load("${TIKTOK_PIXEL_ID}");
}(window,document,"ttq");`;

declare global {
  interface Window { ttq?: { page: () => void } }
}

let lastPath: string | undefined;

export function trackTikTokVisit(path: string) {
  if (!["finanalyser.com.br", "www.finanalyser.com.br"].includes(window.location.hostname)
      || path === lastPath || !window.ttq) return;
  window.ttq.page();
  lastPath = path;
}
