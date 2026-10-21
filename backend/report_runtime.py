"""Public-evidence checkpoints, job progress and provider-reported usage; no prompt logging."""
from contextvars import ContextVar
from hashlib import sha256
import json
import logging
import math
import os
from time import perf_counter
import uuid

progress_callback = ContextVar("report_progress", default=None)
editorial_preparation = ContextVar("editorial_preparation", default=None)
logger = logging.getLogger("uvicorn.error")


def progress(stage):
    callback = progress_callback.get()
    if callback:
        callback(stage)


def checkpoint(stage, identity, compute):
    from full_reports import connection, read_report
    key = sha256(json.dumps(["research-pipeline-v1", stage, identity], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '180s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
            cur.execute("SELECT content FROM company_research_cache WHERE cache_key=%s", (key,))
            row = cur.fetchone()
            if row:
                return read_report(row[0])
            result = compute()
            if result is not None and result != []:
                cur.execute("INSERT INTO company_research_cache(cache_key,content) VALUES (%s,%s::jsonb)", (key, json.dumps(result)))
        conn.commit()
        return result
    finally:
        conn.close()


def usage_record(result, model, elapsed_ms, stage):
    usage = result.get("usage") or {}
    safe_int = lambda value: value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
    calls = sum(item.get("type") == "web_search_call" for item in result.get("output", []))
    entry = {"model": result.get("model") or model, "stage": stage, "elapsed_ms": elapsed_ms,
             "input_tokens": safe_int(usage.get("input_tokens")), "output_tokens": safe_int(usage.get("output_tokens")),
             "cached_input_tokens": safe_int((usage.get("input_tokens_details") or {}).get("cached_tokens")),
             "reasoning_tokens": safe_int((usage.get("output_tokens_details") or {}).get("reasoning_tokens")),
             "web_search_calls": calls, "estimated_cost_usd": None}
    # Estimates use operator-supplied rates, never an invented price or a claim about the invoice.
    try:
        rates = json.loads(os.getenv("REPORT_MODEL_PRICING_JSON", "{}"))[entry["model"]]
        names = ("input_per_million", "cached_input_per_million", "output_per_million", "search_per_call")
        if all(isinstance(rates[n], (int, float)) and not isinstance(rates[n], bool) and math.isfinite(rates[n]) and rates[n] >= 0 for n in names):
            cached = min(entry["cached_input_tokens"], entry["input_tokens"])
            entry["estimated_cost_usd"] = round(((entry["input_tokens"] - cached) * rates[names[0]] + cached * rates[names[1]]
                + entry["output_tokens"] * rates[names[2]]) / 1_000_000 + calls * rates[names[3]], 8)
    except (ValueError, KeyError, TypeError):
        pass
    return entry


def record_run(company, model, stage, elapsed_ms, timings, clients, error_type=None):
    from full_reports import connection
    calls = [call for client in clients if client is not None and isinstance(getattr(client, "usage_calls", None), list) for call in client.usage_calls]
    payload = {"timings": timings, "calls": calls, "input_tokens": sum(c["input_tokens"] for c in calls),
               "output_tokens": sum(c["output_tokens"] for c in calls),
               "estimated_cost_usd": (sum(c["estimated_cost_usd"] for c in calls) if all(c["estimated_cost_usd"] is not None for c in calls) else None) if calls else (0 if error_type is None else None)}
    conn = None
    try:
        conn = connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO report_runs(id,company,model,stage,elapsed_ms,error_type,diagnostics) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)",
                        (str(uuid.uuid4()), company, model, stage, elapsed_ms, error_type, json.dumps(payload)))
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        logger.warning("report_run_metrics_unavailable company=%s", company)
    finally:
        if conn:
            conn.close()
