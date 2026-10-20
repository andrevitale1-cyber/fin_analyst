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
