import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis_pdf import generate_analysis_pdf
from report_auth import SessionUser, require_report_user
from report_generator import router


def sample(call=False):
    return {'metadata': {'empresa': 'Exemplo de exportação', 'periodo': '1T/2026', 'tipo': 'Earnings Call' if call else 'Quarterly results'},
            'data': {'nota_geral': 5, 'receita_nota': 5, 'lucro_nota': 4, 'divida_nota': 5, 'rentabilidade_nota': 5},
            'analise_completa': '\n\n'.join(f'## {i+1}. Análise de demonstração\n**Geração de caixa:** dados de exemplo, não constituem uma análise real. Receita de R$ 1.000 milhões e margem de 25%.\n\n'+
                                          'Texto para verificar a paginação, os acentos e a legibilidade. '*15 for i in range(12)) +
                                 '\n\n| Período | Receita |\n| --- | --- |\n| 1T/2026 | R$ 1.000 milhões |\n```json\n[{"hidden": true}]\n```',
            'source': {'name': 'Exemplo', 'url': 'https://finanalyser.com.br'}}


@pytest.mark.parametrize('call', [False, True])
def test_multipage_pdf_has_all_text_watermark_and_no_raw_json(call):
    pdf = generate_analysis_pdf(sample(call))
    assert pdf.startswith(b'%PDF-')
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) > 1
    for page in reader.pages:
        assert page.extract_text().count('FinAnalyser') >= 3  # Watermark, header and footer on every page.
        assert 'Página' in page.extract_text()
        assert b'FinAnalyser' in page.get_contents().get_data()  # Painted watermark, not metadata only.
    text = '\n'.join(page.extract_text() for page in reader.pages)
    assert '12. Análise de demonstração' in text
    assert 'R$ 1.000 milhões' in text
    assert 'hidden' not in text
    assert ('Geral' in text) is not call


def test_untrusted_markup_is_literal_and_cannot_load_files():
    result = sample()
    result['analise_completa'] = '<img src="file:///etc/passwd"/>\n[invalid](javascript:alert)\n**Safe & sound**\n10 − 3 = 7; growth ≥ 5%'
    reader = PdfReader(io.BytesIO(generate_analysis_pdf(result, 'en')))
    assert '<img src="file:///etc/passwd"/>' in reader.pages[0].extract_text()
    assert 'Safe & sound' in reader.pages[0].extract_text()
    assert '10 - 3 = 7; growth >= 5%' in reader.pages[0].extract_text()
    assert not reader.pages[0].get('/Annots')


def test_missing_category_is_not_exported_as_zero_or_none():
    result=sample();result['data']['divida_nota']=None
    reader=PdfReader(io.BytesIO(generate_analysis_pdf(result,'en')))
    text='\n'.join(page.extract_text() for page in reader.pages)
    assert 'N/A/5' in text and 'None/5' not in text and '0/5' not in text


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    cursor = Mock()
    cursor.fetchone.return_value = (json.dumps(sample()),)
    connection = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setitem(sys.modules, 'main', SimpleNamespace(get_db_connection=lambda: connection))
    with TestClient(app) as test_client:
        yield app, test_client, cursor, connection


@pytest.mark.parametrize('path', ['/api/report/42/pdf', '/api/report/42'])
def test_export_requires_session_premium_and_ownership(client, path):
    app, http, cursor, connection = client
    assert http.get(path).status_code == 401
    app.dependency_overrides[require_report_user] = lambda: SessionUser('user_free', plan='free')
    assert http.get(path).status_code == 403
    cursor.execute.assert_not_called()
    app.dependency_overrides[require_report_user] = lambda: SessionUser('user_owner', plan='premium')
    response = http.get(path)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    sql, parameters = cursor.execute.call_args.args
    assert 'CAST(user_id AS TEXT) = %s' in sql and parameters == (42, 'user_owner')
    if path.endswith('/pdf'):
        assert response.content.startswith(b'%PDF-')
        assert 'attachment' in response.headers['content-disposition']
    connection.close.assert_called()
    cursor.fetchone.return_value = None
    assert http.get(path).status_code == 404


def test_export_locale_is_validated(client):
    app, http, _, _ = client
    app.dependency_overrides[require_report_user] = lambda: SessionUser('user_owner', plan='premium')
    assert http.get('/api/report/42/pdf?locale=invalid').status_code == 422
