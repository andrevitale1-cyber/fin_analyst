"""Agent 2: independently specified sections in one bounded structured request."""
import json
import copy
import re

from company_report_content import company_report_schema
from agents.prompt_builder import PromptBuilder
from report_runtime import editorial_preparation
from sector_research import sector_brief, is_petrobras


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
    if is_petrobras(company):
        schema["properties"]["signals"].update(minItems=6, maxItems=6)
        schema["properties"]["metrics"].update(minItems=8)
        sections["items"]["properties"]["paragraphs"].update(minItems=2, maxItems=4)
    briefs = [{"id": key, "brief": brief, "fact_ids": [f["id"] for f in dossier["facts"] if key in f["sections"]]}
              for key, brief in SECTION_BRIEFS.items()]
    prompt = f"""AGENT 2 — write the company-wide research report for {company}, as of {as_of}.
Write in {'English' if locale == 'en' else 'Portuguese'} using only the supplied cited facts and official financials.
{sector_brief(company)}
Return all six summary signals: moat, profitability, management, growth, valuation and sentiment.
The valuation signal must explain the audited model's result rather than omit the category.
Return exactly the nine individually specified sections and supporting structured data. Valuation is handled
by a separate agent: do not produce that section or scenario assumptions here. Use {'2,500–3,500' if editorial_preparation.get() else '1,200–1,600'} words total.
Each section: concise summary, {'2–4' if editorial_preparation.get() else '1–2'} focused paragraphs and at most 3 nonrepeating bullets. Start paragraphs
with a short **bold key insight**. Cite factual assertions using source_ids, not invented source IDs or URLs.
Use complete sentences, no HTML, no scripts and no filler about missing information. Never invent figures,
ratings, consensus, biographies, comparisons, quotations or forecasts. Label AI judgments explicitly.
Never mention JSON, arrays, internal field names, the pipeline or omitted fields in reader-facing prose.
If independent sentiment evidence is unavailable, use at most ONE brief sentence about that gap;
never pad the sentiment section with repeated paragraphs describing missing market information.
All numbers retain period, currency and scale. Numeric monetary JSON values use full currency units;
When secondary notes conflict with original statements, use the primary figure for the same accounting basis;
do not combine reported/adjusted earnings or present a secondary number as primary-verified.
EPS is per underlying share. Do not mix fiscal/calendar years, ADR/ordinary shares, currencies or periods.
Financial history contains 3–5 full years when available, never quarters/TTM. Highlight metrics must have
numeric_value, unit, date/period and source_id. Segment/geography shares are percentage points (51.5, not .515).
Do not combine overlapping segment/platform classifications. Prefer operational segments and a common period.
Scores are reasoned AI quality assessments from 1–5, with cited support; never equate a score with market upside.
Analyst consensus and market data require dated independent sources; their as_of fields must be exact YYYY-MM-DD
observation dates. Projections require management guidance
or analyst consensus; do not invent model forecasts. Distinguish source facts, calculated values and AI judgments.
When the dossier supplies investment_model, its projections are explicitly conditional AI assumptions.
You may explain those in outlook/thesis/verdict with that label and their stated source_id, but do not put
them in the sourced projections array or describe them as guidance or consensus. Follow the model's single
conviction level and selected valuation method throughout. Explain disagreements between cross-check methods.
Cover the priced-in expectations, counterthesis, catalysts and measurable conditions that invalidate the thesis.
If an oil-model bear case has residual_negative=true, explain that enterprise value falls below the debt
bridge and zero is a residual calculation floor. It is not a forecast of a zero trading price or bankruptcy;
equity option value is not modeled. Do not conceal that downside or force positive scenario values.
SHARED ANALYSIS RULES:\n{PromptBuilder().company_field_rules(company, locale)}
SECTION PROMPTS:\n{json.dumps(briefs)}
FACT DOSSIER:\n{json.dumps(dossier, ensure_ascii=False)}
COMPACT SOURCES AND ORIGINAL FINANCIAL EVIDENCE:\n{json.dumps(sources, ensure_ascii=False)}"""
    return client.analyze_full_report(prompt, schema, max_output_tokens=14000 if editorial_preparation.get() else 8500, timeout=timeout)


def repair_report(client, company, as_of, locale, report, issues, dossier, sources, *, timeout=45):
    """Replace only fields named by the independent reviewer, preserving accepted content."""
    from full_report_content import ReportValidationError
    base = company_report_schema()
    targets = " ".join(issue["target"] for issue in issues).lower()
    section_ids = [s["id"] for s in report["sections"] if re.search(r"\b" + re.escape(s["id"]) + r"\b", targets)]
    fields = [key for key in base["properties"] if re.search(r"\b" + key + r"\b", targets)]
    if section_ids and "sections" not in fields:
        fields.append("sections")
    if "sections" in fields and not section_ids:
        section_ids = [s["id"] for s in report["sections"]]
    if not fields:
        raise ReportValidationError("Audit repair did not identify a supported report field")
    properties = {key: base["properties"][key] for key in fields}
    if "sections" in fields:
        properties["sections"].update(minItems=len(section_ids), maxItems=len(section_ids))
        properties["sections"]["items"]["properties"]["id"]["enum"] = section_ids
    schema = {"type": "object", "additionalProperties": False, "required": fields, "properties": properties}
    prompt = f"""AGENT 2 — repair the rejected fields of {company}'s report as of {as_of}.
Write in {'English' if locale == 'en' else 'Portuguese'}. Return ONLY the specified replacement fields.
Correct every reviewer issue against supplied evidence; issues and the old draft are NOT new evidence.
Original source context outranks first-pass extracted statements. Correct percentage denominators and
reported/adjusted/comparable accounting bases explicitly; do not repeat an extraction error from the old draft.
Preserve valid content. Remove unsupported assertions rather than inventing support. Do not change other
fields, add report sections, research again or recalculate valuation prices: Python handles arithmetic.
SHARED ANALYSIS RULES:\n{PromptBuilder().company_field_rules(company, locale)}
ISSUES:\n{json.dumps(issues, ensure_ascii=False)}
DRAFT:\n{json.dumps(report, ensure_ascii=False)}
FACTS:\n{json.dumps(dossier, ensure_ascii=False)}
COMPACT SOURCES AND ORIGINAL FINANCIAL EVIDENCE:\n{json.dumps(sources, ensure_ascii=False)}"""
    replacements = client.analyze_full_report(prompt, schema, max_output_tokens=5000, timeout=timeout)
    if set(replacements) != set(fields):
        raise ReportValidationError("Audit repair returned unexpected fields")
    result = copy.deepcopy(report)
    for key, value in replacements.items():
        if key == "sections":
            ids = [s["id"] for s in value]
            if len(ids) != len(section_ids) or set(ids) != set(section_ids):
                raise ReportValidationError("Audit repair returned unexpected sections")
            by_id = {s["id"]: s for s in value}
            result[key] = [by_id.get(s["id"], s) for s in report[key]]
        else:
            result[key] = value
    return result
