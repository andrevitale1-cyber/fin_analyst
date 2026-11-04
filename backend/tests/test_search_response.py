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
