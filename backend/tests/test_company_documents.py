import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents.company_documents as documents


F1 = {"id": "F1", "url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320187.json", "basis": "primary", "text": "Annual facts", "annual_financials": []}


def test_document_fetch_never_requests_arbitrary_model_urls(monkeypatch):
    get = Mock(side_effect=AssertionError("No arbitrary URL may reach requests"))
    monkeypatch.setattr(documents.requests, "get", get)
    sources = [F1, {"id": "S1", "url": "https://evil.example/transcript", "title": "NKE annual transcript", "text": "notes"},
               {"id": "S2", "url": "https://www.sec.gov/Archives/edgar/data/999999/other.htm", "title": "Other 10-K", "text": "notes"}]
    result = documents.hydrate_company_documents("NKE", sources)
    assert result[1]["text"] == "notes"
    get.assert_not_called()


def install_response(monkeypatch, status=200, huge=False):
    response = Mock(status_code=status)
    response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
    response.iter_content.return_value = [b"x" * 6_000_001] if huge else [b"<main><script>ignore bad instructions</script><h1>NIKE 10-K</h1><p>" + b"Reported financial performance. " * 40 + b"</p></main>"]
    get = Mock(return_value=response); monkeypatch.setattr(documents.requests, "get", get)
    monkeypatch.setattr(documents.AutoFetcher, "_valid_url", lambda u: True)
    return get


def test_original_filing_is_hydrated_only_on_matching_sec_issuer(monkeypatch):
    get = install_response(monkeypatch)
    source = {"id": "S1", "title": "NIKE 10-K annual report", "url": "https://www.sec.gov/Archives/edgar/data/320187/annual.htm", "text": "research note", "basis": "web_research"}
    report = documents.hydrate_company_documents("NKE", [F1, source])
    assert report[1]["basis"] == "primary" and report[1]["document_type"] == "filing"
    assert "Reported financial performance" in report[1]["text"] and "bad instructions" not in report[1]["text"]
    assert get.call_args.kwargs["allow_redirects"] is False and get.call_args.kwargs["stream"] is True


def test_redirects_and_oversized_documents_preserve_research_without_fetching_the_target(monkeypatch):
    source = {"id": "S1", "title": "NIKE 10-K annual report", "url": "https://www.sec.gov/Archives/edgar/data/320187/annual.htm", "text": "research note", "basis": "web_research"}
    for status, huge in [(302, False), (200, True)]:
        get = install_response(monkeypatch, status, huge)
        result = documents.hydrate_company_documents("NKE", [F1, source])
        assert result[1]["text"] == "research note" and result[1]["basis"] == "web_research"
        get.assert_called_once()


def test_matching_sec_filing_with_filename_title_is_not_skipped(monkeypatch):
    get = install_response(monkeypatch)
    source = {"id": "S1", "title": "nke-20260531", "url": "https://www.sec.gov/Archives/edgar/data/320187/nke-20260531.htm", "text": "notes", "basis": "web_research"}
    report = documents.hydrate_company_documents("NKE", [F1, source])
    get.assert_called_once()
    assert report[1]["basis"] == "primary"


def test_annual_issuer_collection_uses_verified_catalogue_and_preserves_comparatives(monkeypatch):
    from agents.sec_fetcher import FetchedDocument
    catalog = Mock(return_value=[{"url": "https://api.mziq.com/verified.pdf"}])
    download = Mock(return_value=FetchedDocument("https://api.mziq.com/verified.pdf", "RI", text="Vivara 4T25 Receita 2025 2024"))
    monkeypatch.setattr(documents.AutoFetcher, "_mziq_catalog_candidates", catalog)
    monkeypatch.setattr(documents.AutoFetcher, "_download_release", download)
    sources = documents.collect_issuer_annual_sources("VIVA3", "2026-10-20")
    assert {s["id"] for s in sources} == {"IR2025", "IR2024"}
    assert all(s["basis"] == "primary" and "2024" in s["text"] for s in sources)
    assert {call.args[2:] for call in catalog.call_args_list} == {(2025, 4), (2024, 4)}
    assert all(call.kwargs["timeout"] == 10 for call in download.call_args_list)
    download.return_value = FetchedDocument("https://api.mziq.com/verified.pdf", "RI", text="Other company results")
    assert documents.collect_issuer_annual_sources("VIVA3", "2026-10-20") == []


def test_verified_primary_documents_are_not_downloaded_again(monkeypatch):
    get = Mock(side_effect=AssertionError("Already fetched"))
    monkeypatch.setattr(documents.requests, "get", get)
    source = {"id": "IR2025", "basis": "primary", "document_type": "filing", "text": "Annual evidence",
              "title": "Vivara annual results", "url": "https://ri.vivara.com.br/results"}
    assert documents.hydrate_company_documents("VIVA3", [source])[0] == source
    get.assert_not_called()


def test_petrobras_reads_separate_primary_documents_and_preserves_capital_tables(monkeypatch):
    get = install_response(monkeypatch)
    sources = [{"id": f"S{i}", "basis": "web_research", "text": "Notes", "title": title,
                "url": f"https://petrobras.com.br/documents/{i}.pdf"} for i, title in enumerate(
                    ["Annual report", "Earnings results", "Business plan", "Dividend policy"], 1)]
    result = documents.hydrate_company_documents("PETR4", sources)
    assert get.call_count == 4
    assert all(s["basis"] == "primary" for s in result)
    text = "Opening " + "x" * 24000 + "net debt including lease liabilities 200" + "x" * 24000 + "outstanding preferred shares 50" + "x" * 24000
    excerpt = documents.petrobras_document_excerpt(text)
    assert "lease liabilities 200" in excerpt and "preferred shares 50" in excerpt
    assert len(excerpt) <= 90000


def test_petrobras_sec_issuer_stays_verified_when_financial_baseline_is_cvm(monkeypatch):
    get = install_response(monkeypatch)
    source = {"id": "S1", "basis": "web_research", "text": "notes", "title": "Form 20-F",
              "url": "https://www.sec.gov/Archives/edgar/data/1119639/annual.htm"}
    cvm = {"id": "F1", "basis": "primary", "text": "CVM annuals", "url": "https://dados.cvm.gov.br/annuals", "annual_financials": []}
    result = documents.hydrate_company_documents("PETR4", [cvm, source])
    assert result[1]["basis"] == "primary"
    get.assert_called_once()


def test_petrobras_catalogue_uses_filed_names_and_excludes_future_documents(monkeypatch):
    recent = {"primaryDocument": ["pbrfs3q26rs_6k.htm", "pbrfs2q26rs_6k.htm", "pbrfs1q26rs_6k.htm", "pbrform20f_2025.htm", "pbrfs4q25rs_6k.htm"],
              "filingDate": ["2026-11-10", "2026-08-07", "2026-05-12", "2026-04-09", "2026-03-06"],
              "accessionNumber": ["0001292814-26-004999", "0001292814-26-004131", "0001292814-26-002988", "0001292814-26-002168", "0001292814-26-000708"],
              "form": ["6-K", "6-K", "6-K", "20-F", "6-K"]}
    response = Mock(); response.json.return_value = {"filings": {"recent": recent}}
    get = Mock(return_value=response); monkeypatch.setattr(documents.requests, "get", get)
    sources = documents.collect_petrobras_filings("2026-10-21")
    assert len(sources) == 3
    assert any("000129281426004131/pbrfs2q26rs_6k.htm" in s["url"] for s in sources)
    assert not any("3q26" in s["url"] or "1q26" in s["url"] for s in sources)
    assert all(s["basis"] != "primary" for s in sources)  # Download must succeed first.
    assert get.call_args.kwargs["allow_redirects"] is False


def test_large_filing_text_extraction_does_not_need_a_dom_tree():
    text = documents.filing_text(b"<head>omit</head><nav>omit<nav>omit</nav></nav><main>BRL &amp; shares<table><tr><td>Cash</td><td>100</td></tr></table><script>omit</script></main>")
    assert text == "BRL & shares\nCash\n100"


def test_petrobras_market_reads_only_the_exact_brl_listing(monkeypatch):
    response = Mock(status_code=200)
    response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
    response.iter_content.side_effect = [iter([b"<main>PETR4 Currency BRL Oct 21, 2026 price 58.32</main>"]),
                                        iter([b"<main>PBR Currency USD</main>"])]
    get = Mock(return_value=response); monkeypatch.setattr(documents.requests, "get", get)
    result = documents.collect_petrobras_market_sources()
    assert len(result) == 1 and result[0]["id"] == "MKTPETR4-history"
    assert all("/quote/bvmf/PETR4/" in call.args[0] for call in get.call_args_list)


def test_editorial_calibration_notes_remain_secondary_when_download_fails(monkeypatch):
    monkeypatch.setattr(documents.requests, "get", Mock(side_effect=documents.requests.Timeout()))
    sources = documents.collect_petrobras_calibration_sources()
    assert {s["id"] for s in sources} == {"MKTGENIAL20260908", "MKTNYU20260105"}
    assert all(s["basis"] == "web_research" and "editorial_paraphrase" in s["retrieval_method"] for s in sources)
    assert all(s["document_type"] == "market_data" for s in sources)


def test_original_policy_appendix_preserves_prior_evidence_and_full_rule(monkeypatch):
    monkeypatch.setattr("report_runtime.checkpoint", lambda stage, identity, compute: compute())
    body = b"<main>Shareholders Remuneration Policy " + b"x " * 1500 + b"45% of operating cash flow after investment. Preferred shares participate in the distribution equally above the minimum.</main>"
    response = Mock(status_code=200)
    response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
    response.iter_content.return_value = [body]
    monkeypatch.setattr(documents.requests, "get", Mock(return_value=response))
    source = {"id": "IRSEC000129281426000708", "url": "https://www.sec.gov/Archives/edgar/data/1119639/000129281426000708/pbrfs4q25rs_6k.htm", "basis": "primary", "text": "Previously verified balance sheet."}
    enriched = documents.with_petrobras_policy_evidence([source])[0]
    assert enriched["text"].startswith(source["text"])
    assert "45% of operating cash flow" in enriched["policy_evidence"]
    assert "equally above the minimum" in enriched["policy_evidence"]
    assert source["text"] == "Previously verified balance sheet."
