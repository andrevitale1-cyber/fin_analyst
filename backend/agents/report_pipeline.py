"""Four specialized agents; no agent can publish or bypass quota/access checks."""
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
import logging

from agents.report_facts import writing_sources
from agents.report_writer import write_report
from agents.report_valuation import value_company, calculate_valuation
from agents.report_verifier import verify_report
from company_report_content import apply_official_financials, validate_company_report


PIPELINE_VERSION = "company-agents-v1"
logger = logging.getLogger("uvicorn.error")


def remaining(deadline, cap):
    budget = int(deadline - perf_counter())
    if budget < 5:
        raise TimeoutError("Company report pipeline deadline exceeded")
    return min(cap, budget)


def generate_report(client, company, as_of, locale, sources, dossier, *, deadline):
    started = perf_counter()
    compact_sources = writing_sources(dossier, sources)
    with ThreadPoolExecutor(max_workers=2) as pool:
        writer = pool.submit(write_report, client, company, as_of, locale, dossier, compact_sources,
                             timeout=remaining(deadline, 95))
        valuation = pool.submit(value_company, client, company, as_of, locale, dossier, compact_sources,
                                timeout=remaining(deadline, 50))
        raw, calculated = writer.result(), valuation.result()
    if calculated["section"]["id"] != "valuation" or any(s["id"] == "valuation" for s in raw["sections"]):
        raise ValueError("Agent returned a section outside its assigned role")
    raw["sections"].append(calculated["section"])
    raw["valuation"] = calculated["valuation"]
    content = calculate_valuation(validate_company_report(apply_official_financials(raw, sources), sources))
    writing_ms = round((perf_counter() - started) * 1000)
    logger.info("report_agents company=%s stage=sections_and_valuation elapsed_ms=%d", company, writing_ms)
    reviewed = perf_counter()
    review = verify_report(client, content, dossier, sources, as_of, timeout=remaining(deadline, 40))
    verification_ms = round((perf_counter() - reviewed) * 1000)
    logger.info("report_agents company=%s stage=verification passed=true elapsed_ms=%d", company, verification_ms)
    content["pipeline"] = {"version": PIPELINE_VERSION, "agents": ["facts", "sections", "valuation", "verification"],
                           "verification": review, "writing_ms": writing_ms,
                           "verification_ms": verification_ms,
                           "document_types": sorted({s.get("document_type", "research") for s in sources})}
    return content
