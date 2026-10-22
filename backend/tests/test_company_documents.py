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
    assert len(excerpt) <= 48000
