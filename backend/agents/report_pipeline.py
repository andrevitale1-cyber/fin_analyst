"""Four specialized agents; no agent can publish or bypass quota/access checks."""
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
import logging

from agents.report_facts import writing_sources, repair_fact_dossier
from agents.report_writer import write_report, repair_report
from agents.report_valuation import value_company, calculate_valuation
from agents.report_verifier import verify_report, EvidenceAuditError
from company_report_content import apply_official_financials, validate_company_report
from report_runtime import checkpoint, progress, editorial_preparation
from agents.report_model import model_context, model_valuation_section, verify_model


PIPELINE_VERSION = "company-agents-v4"
logger = logging.getLogger("uvicorn.error")


def remaining(deadline, cap):
    budget = int(deadline - perf_counter())
    if budget < 5:
        raise TimeoutError("Company report pipeline deadline exceeded")
    return min(cap, budget)


def generate_report(client, company, as_of, locale, sources, dossier, *, deadline, investment_model=None):
    started = perf_counter()
    compact_sources = writing_sources(dossier, sources)
    progress("writing")
    if investment_model is not None:
        context = {**dossier, "investment_model": model_context(investment_model)}
        raw = checkpoint("writer", [PIPELINE_VERSION, bool(editorial_preparation.get()), company, as_of, locale, client.model, context, compact_sources],
                         lambda: write_report(client, company, as_of, locale, context, compact_sources, timeout=remaining(deadline, 360 if editorial_preparation.get() else 130)))
        calculated = model_valuation_section(investment_model, locale)
    else:
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
    content = calculate_valuation(validate_company_report(apply_official_financials(raw, sources), sources), locale)
    if investment_model is not None:
        verify_model(investment_model, sources)
        content["investment_model"] = investment_model
    writing_ms = round((perf_counter() - started) * 1000)
    logger.info("report_agents company=%s stage=sections_and_valuation elapsed_ms=%d", company, writing_ms)
    reviewed = perf_counter()
    progress("verification")
    try:
        review = verify_report(client, content, dossier, sources, as_of, timeout=remaining(deadline, 40), company=company, locale=locale)
    except EvidenceAuditError as error:
        if deadline - perf_counter() < 165:
            raise
        logger.info("report_agents company=%s stage=evidence_repair issues=%d", company, len(error.issues))
        progress("repair")
        dossier = checkpoint("audited-facts-repair-v1", [company, as_of, client.model, dossier, error.issues, compact_sources],
            lambda: repair_fact_dossier(client, dossier, error.issues, sources, timeout=remaining(deadline, 45)))
        compact_sources = writing_sources(dossier, sources)
        repair_context = {**dossier, "investment_model": model_context(investment_model)} if investment_model is not None else dossier
        corrected = repair_report(client, company, as_of, locale, content, error.issues, repair_context,
                                  compact_sources, timeout=remaining(deadline, 75))
        # Revalidate model inputs, then recompute every derived valuation output.
        corrected["valuation"].pop("fair_value", None)
        for case in corrected["valuation"]["scenarios"]:
            for key in ("future_value", "present_value", "upside_percent"):
                case.pop(key, None)
        corrected.pop("investment_model", None)
        if investment_model is not None:
            corrected["valuation"] = model_valuation_section(investment_model, locale)["valuation"]
        content = calculate_valuation(validate_company_report(apply_official_financials(corrected, sources), sources), locale)
        if investment_model is not None:
            content["investment_model"] = investment_model
        review = verify_report(client, content, dossier, sources, as_of, timeout=remaining(deadline, 40), company=company, locale=locale)
    verification_ms = round((perf_counter() - reviewed) * 1000)
    logger.info("report_agents company=%s stage=verification passed=true elapsed_ms=%d", company, verification_ms)
    content["pipeline"] = {"version": PIPELINE_VERSION, "agents": ["facts", "sections", "valuation", "verification"],
                           "verification": review, "writing_ms": writing_ms,
                           "verification_ms": verification_ms,
                           "document_types": sorted({s.get("document_type", "research") for s in sources})}
    return content
