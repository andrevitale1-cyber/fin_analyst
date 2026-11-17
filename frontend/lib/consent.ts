export const CONSENT_KEY = "finanalyser:cookie-consent";

// Analytics and advertising load only after an explicit "granted"; blocked storage counts as no consent.
export function hasTrackingConsent() {
  try { return localStorage.getItem(CONSENT_KEY) === "granted"; } catch { return false; }
}
