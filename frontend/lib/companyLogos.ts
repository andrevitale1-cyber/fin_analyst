const COMPANY_TICKERS: Record<string, string> = {
  APPLE: "AAPL", "APPLE INC": "AAPL", MICROSOFT: "MSFT", "MICROSOFT CORPORATION": "MSFT",
  GOOGLE: "GOOGL", ALPHABET: "GOOGL", "ALPHABET INC": "GOOGL", META: "META", "META PLATFORMS INC": "META",
  AMAZON: "AMZN", "AMAZON COM INC": "AMZN", NVIDIA: "NVDA", "NVIDIA CORPORATION": "NVDA",
  TESLA: "TSLA", "TESLA INC": "TSLA", WEG: "WEGE3", "WEG S A": "WEGE3",
  "CAVA GROUP INC": "CAVA", "BERKSHIRE HATHAWAY": "BRK-B",
};
const LOCAL_LOGOS = new Set("AAPL ABBV ABEV AMAT AMD AMZN AVGO BAC BBD BRK-B BSBR CAT COST CSCO CVX GOOG INTC ITUB JBS JNJ JPM KO LLY LRCX MA META MSFT MU NU NVDA ORCL PBR PLTR TSLA V VALE WEGE3.SA WMT XOM BPAC3.SA".split(" "));
const LOCAL_ALIASES: Record<string, string> = {
  GOOGL: "GOOG", "BRK.B": "BRK-B", WEGE3: "WEGE3.SA", BPAC11: "BPAC3.SA",
  PETR4: "PBR", PETR3: "PBR", VALE3: "VALE", ITUB4: "ITUB", BBDC4: "BBD", ABEV3: "ABEV", SANB11: "BSBR",
};

export function companyLogoSources(symbol?: string | null, company = ""): string[] {
  const raw = (symbol?.trim() || company.trim()).toUpperCase();
  const name = raw.replace(/[^A-Z0-9]+/g, " ").trim();
  const ticker = COMPANY_TICKERS[name] || raw.match(/\(([A-Z0-9.-]{1,15})\)$/)?.[1] || raw.replace(/^(?:NASDAQ|NYSE|B3):\s*/, "");
  if (!/^[A-Z0-9][A-Z0-9.-]{0,14}$/.test(ticker)) return [];
  const local = LOCAL_ALIASES[ticker] || ticker;
  const sources = ["AMD", "MU", "NOW"].includes(local) ? [`/report-logos/${local}.png`]
    : LOCAL_LOGOS.has(local) ? [`/benefits/company-logos/${local}.webp`] : [];
  const remote = /^[A-Z]{4}\d{1,2}$/.test(ticker) ? `${ticker}.SA` : ticker.replace(/^BRK\.([AB])$/, "BRK-$1");
  sources.push(`https://financialmodelingprep.com/image-stock/${encodeURIComponent(remote)}.png`);
  return sources;
}
