"""Search formatting must not turn valid candidates into a service outage."""
from unittest.mock import MagicMock, Mock

import pytest
from openai_client import OpenAIClient, OpenAIError


@pytest.mark.parametrize("suffix", ["", "\nNote: Verify the document before analysis.", "\n```\nNote: Official RI links."])
def test_search_accepts_complete_array_with_trailing_commentary(suffix):
    client = OpenAIClient()
    client._client = MagicMock()
    client._request = Mock(return_value={"output": [{"type": "message", "content": [
        {"type": "output_text", "text": '```json\n[{"title":"Itaú 3T26","url":"https://example.com/release.pdf"}]' + suffix}
    ]}]})
    assert client.search_pdf_links("ITUB4 3T26")[0]["url"] == "https://example.com/release.pdf"


@pytest.mark.parametrize("text", ['[{"url":"https://example.com/release.pdf"}', '{}', 'null', 'No release found'])
def test_search_does_not_accept_truncated_or_non_array_output(text):
    client = OpenAIClient()
    client._client = MagicMock()
    client._request = Mock(return_value={"output": [{"type": "message", "content": [
        {"type": "output_text", "text": text}
    ]}]})
    with pytest.raises(OpenAIError):
        client.search_pdf_links("ITUB4 3T26")


def test_truncated_presentation_uses_complete_tool_urls_not_partial_json():
    client = OpenAIClient()
    client._client = MagicMock()
    client._request = Mock(return_value={"status":"incomplete", "output":[
        {"type":"web_search_call", "action":{"sources":[
            {"url":"https://official.example/release.pdf"},
            {"url":"https://official.example/release.pdf"}]}},
        {"type":"message", "content":[{"type":"output_text","text":'[{"url":"https://partial'}]}]})
    assert client.search_pdf_links('MCD Q3 2026') == [
        {"title":"Official report","url":"https://official.example/release.pdf"}]
    payload=client._request.call_args.kwargs['json']
    assert payload['max_output_tokens']==2500
    assert payload['include']==['web_search_call.action.sources']


def test_truncation_without_tool_sources_has_specific_diagnostic():
    client = OpenAIClient()
    client._client = MagicMock()
    client._request = Mock(return_value={"status":"incomplete","output":[]})
    with pytest.raises(OpenAIError) as error:
        client.search_pdf_links('MCD Q3 2026')
    assert error.value.code=='search_output_truncated'
