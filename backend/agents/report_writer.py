"""Agent 2: independently specified sections in one bounded structured request."""
import json

from company_report_content import company_report_schema


SECTION_BRIEFS = {
    "thesis": "Central investment case; distinguish facts from AI interpretation and give counterarguments.",
    "business": "Business model, customers, named competitors, segment mix and revenue durability.",
    "financials": "Multi-year revenue, profit and cash trends; explain quality and capital intensity.",
    "moat": "Evidence for competitive advantages, their durability and threats.",
    "management": "Execution, capital allocation, ownership/alignment only when evidenced.",
    "sentiment": "Dated independent analyst consensus and market positioning, not management optimism.",
    "outlook": "Management guidance, demand drivers and sourced consensus; distinguish forecasts from facts.",
    "risks": "Material business, balance-sheet, concentration and execution risks and thesis breakers.",
    "verdict": "Balanced company-wide conclusion, principal strength, constraint and watchpoints; no invented data.",
}


def write_report(client, company, as_of, locale, dossier, sources, *, timeout=95):
    schema = company_report_schema()
    del schema["properties"]["valuation"]
    schema["required"].remove("valuation")
    sections = schema["properties"]["sections"]
    sections.update(minItems=9, maxItems=9)
    sections["items"]["properties"]["id"]["enum"] = list(SECTION_BRIEFS)
    briefs = [{"id": key, "brief": brief, "fact_ids": [f["id"] for f in dossier["facts"] if key in f["sections"]]}
              for key, brief in SECTION_BRIEFS.items()]
    prompt = f"""AGENT 2 — write the company-wide research report for {company}, as of {as_of}.
Write in {'English' if locale == 'en' else 'Portuguese'} using only the supplied cited facts and official financials.
Return exactly the nine individually specified sections and supporting structured data. Valuation is handled
by a separate agent: do not produce that section or scenario assumptions here. Use 850–1,200 words total.
Each section: concise summary, 1–2 focused paragraphs and at most 3 nonrepeating bullets. Start paragraphs
with a short **bold key insight**. Cite factual assertions using source_ids, not invented source IDs or URLs.
Use complete sentences, no HTML, no scripts and no filler about missing information. Never invent figures,
ratings, consensus, biographies, comparisons, quotations or forecasts. Label AI judgments explicitly.
All numbers retain period, currency and scale. Numeric monetary JSON values use full currency units;
EPS is per underlying share. Do not mix fiscal/calendar years, ADR/ordinary shares, currencies or periods.
Financial history contains 3–5 full years when available, never quarters/TTM. Highlight metrics must have
numeric_value, unit, date/period and source_id. Segment/geography shares are percentage points (51.5, not .515).
Do not combine overlapping segment/platform classifications. Prefer operational segments and a common period.
Scores are reasoned AI quality assessments from 1–5, with cited support; never equate a score with market upside.
Analyst consensus and market data require dated independent sources; their as_of fields must be exact YYYY-MM-DD
observation dates. Projections require management guidance
or analyst consensus; do not invent model forecasts. Distinguish source facts, calculated values and AI judgments.
SECTION PROMPTS:\n{json.dumps(briefs)}
FACT DOSSIER:\n{json.dumps(dossier, ensure_ascii=False)}
OFFICIAL ANNUAL FINANCIALS:\n{json.dumps([s for s in sources if s.get('annual_financials')], ensure_ascii=False)}"""
    return client.analyze_full_report(prompt, schema, max_output_tokens=8500, timeout=timeout)
