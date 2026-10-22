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
from sector_research import is_petrobras


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
    if is_petrobras(company):
        from agents.company_documents import with_petrobras_policy_evidence
        sources = with_petrobras_policy_evidence(sources)
        compact_sources = writing_sources(dossier, sources)
    content = calculate_valuation(validate_company_report(apply_official_financials(raw, sources), sources), locale)
    if investment_model is not None:
        verify_model(investment_model, sources)
        content["investment_model"] = investment_model
    writing_ms = round((perf_counter() - started) * 1000)
    logger.info("report_agents company=%s stage=sections_and_valuation elapsed_ms=%d", company, writing_ms)
    reviewed = perf_counter()
    audit_timeout = (240 if editorial_preparation.get() else 90) if is_petrobras(company) else 40
    progress("verification")
    attempts = 3 if is_petrobras(company) else 2
    for attempt in range(attempts):
        progress("verification")
        try:
            review = verify_report(client, content, dossier, sources, as_of, timeout=remaining(deadline, audit_timeout), company=company, locale=locale)
            break
        except EvidenceAuditError as error:
            if attempt == attempts - 1 or deadline - perf_counter() < 165:
                raise
            logger.info("report_agents company=%s stage=evidence_repair issues=%d", company, len(error.issues))
            progress("repair")
            fact_issues = [i for i in error.issues if not i["reason"].startswith("Reader copy:")]
            if is_petrobras(company):
                fact_issues = [i for i in fact_issues if "facts" in i["target"].lower() or "dossier" in i["target"].lower()]
                if investment_model and any("investment_model" in i["target"] for i in error.issues):
                    from agents.petrobras_model import repair_narratives
                    investment_model = repair_narratives(client, investment_model, error.issues, sources, locale,
                        timeout=remaining(deadline, 180))
            if fact_issues:
                dossier = checkpoint("audited-facts-repair-v1", [company, as_of, client.model, dossier, fact_issues, compact_sources],
                    lambda: repair_fact_dossier(client, dossier, fact_issues, sources, timeout=remaining(deadline, 90 if editorial_preparation.get() else 45)))
            compact_sources = writing_sources(dossier, sources)
            flagged_sources = {sid for issue in error.issues for sid in issue["source_ids"]}
            originals = {s["id"]: s for s in sources}
            repair_sources = [originals[s["id"]] if s["id"] in flagged_sources else s for s in compact_sources]
            repair_context = {**dossier, "investment_model": model_context(investment_model)} if investment_model is not None else dossier
            repair = lambda: repair_report(client, company, as_of, locale, content, error.issues, repair_context,
                                           repair_sources, timeout=remaining(deadline, 240 if editorial_preparation.get() else 75))
            corrected = checkpoint("editorial-sections-repair-v1", [company, as_of, locale, client.model, content, error.issues, repair_context, repair_sources], repair) if editorial_preparation.get() else repair()
            # Revalidate model inputs, then recompute every derived valuation output.
            corrected["valuation"].pop("fair_value", None)
            for case in corrected["valuation"]["scenarios"]:
                for key in ("future_value", "present_value", "upside_percent"):
                    case.pop(key, None)
            corrected.pop("investment_model", None)
            if investment_model is not None:
                model_section = model_valuation_section(investment_model, locale)
                corrected["valuation"] = model_section["valuation"]
                corrected["sections"] = [model_section["section"] if s["id"] == "valuation" else s for s in corrected["sections"]]
            content = calculate_valuation(validate_company_report(apply_official_financials(corrected, sources), sources), locale)
            if investment_model is not None:
                content["investment_model"] = investment_model
    verification_ms = round((perf_counter() - reviewed) * 1000)
    logger.info("report_agents company=%s stage=verification passed=true elapsed_ms=%d", company, verification_ms)
    content["pipeline"] = {"version": PIPELINE_VERSION, "agents": ["facts", "sections", "valuation", "verification"],
                           "verification": review, "writing_ms": writing_ms,
                           "verification_ms": verification_ms,
                           "document_types": sorted({s.get("document_type", "research") for s in sources})}
    return content
