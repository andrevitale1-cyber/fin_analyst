import csv
import io
import zipfile

from cvm_financials import parse_archive


def archive_fixture():
    output = io.BytesIO()
    fields = ["CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "DT_RECEB", "DT_INI_EXERC", "DT_FIM_EXERC", "MOEDA", "ESCALA_MOEDA", "CD_CONTA", "DS_CONTA", "VL_CONTA"]
    def base(**kwargs):
        return {**dict.fromkeys(fields, ""), "CNPJ_CIA": "issuer", "DT_REFER": "2025-12-31", "VERSAO": "1", "DT_RECEB": "2026-03-18",
                "DT_INI_EXERC": "2025-01-01", "DT_FIM_EXERC": "2025-12-31", "MOEDA": "REAL", "ESCALA_MOEDA": "MIL", **kwargs}
    statements = {"": [base(), base(VERSAO="2", DT_RECEB="2026-11-01")],
                  "DRE_con_": [base(CD_CONTA="3.01", VL_CONTA="1000"), base(CD_CONTA="3.11", VL_CONTA="100"),
                               base(CD_CONTA="3.99.02.01", DS_CONTA="ON", VL_CONTA="2.50"),
                               base(CD_CONTA="3.99.02.02", DS_CONTA="PN", VL_CONTA="3.50"),
                               base(CD_CONTA="3.01", VL_CONTA="9999", VERSAO="2"),
                               base(CNPJ_CIA="other", CD_CONTA="3.01", VL_CONTA="8888")],
                  "DFC_MI_con_": [base(CD_CONTA="6.01", VL_CONTA="80"),
                                  base(CD_CONTA="6.02.01", DS_CONTA="Aquisição de imobilizado", VL_CONTA="-20")],
                  "BPA_con_": [base(CD_CONTA="1.01.01", VL_CONTA="10")],
                  "BPP_con_": [base(CD_CONTA="2.01.04", VL_CONTA="15"), base(CD_CONTA="2.02.01", VL_CONTA="30")]}
    with zipfile.ZipFile(output, "w") as z:
        for statement, records in statements.items():
            text = io.StringIO(); writer = csv.DictWriter(text, fieldnames=fields, delimiter=";")
            writer.writeheader(); writer.writerows(records)
            z.writestr(f"dfp_cia_aberta_{statement}2025.csv", text.getvalue().encode("utf-8"))
    output.seek(0)
    return zipfile.ZipFile(output)


def test_cvm_filters_issuer_filing_date_version_and_preserves_per_share_units():
    with archive_fixture() as z:
        result = parse_archive(z, 2025, "issuer", "2026-10-20")
    values = result["2025-12-31"]
    assert values["Revenue"][1] == 1_000_000
    assert values["Net income"][1] == 100_000
    assert values["Diluted EPS"][1] == 2.5  # Never multiply EPS by statement scale.
    assert values["Capital expenditures"][1] == 20_000


def test_preferred_and_unit_listings_never_reuse_ordinary_share_eps():
    with archive_fixture() as z:
        preferred = parse_archive(z, 2025, "issuer", "2026-10-20", "PN")
    assert preferred["2025-12-31"]["Diluted EPS"][1] == 3.5
    with archive_fixture() as z:
        units = parse_archive(z, 2025, "issuer", "2026-10-20", None)
    assert "Diluted EPS" not in units["2025-12-31"]


def test_petrobras_parent_uses_verified_cnpj_instead_of_ambiguous_names(monkeypatch):
    from unittest.mock import Mock
    import cvm_financials as cvm
    csv_text = "CNPJ_CIA;SIT;DENOM_SOCIAL\n33.000.167/0001-01;ATIVO;PETROLEO BRASILEIRO S A PETROBRAS\n00.000.000/0001-00;ATIVO;PETROBRAS OTHER COMPANY\n"
    response = Mock(status_code=200, content=csv_text.encode())
    monkeypatch.setattr(cvm.requests, "get", Mock(return_value=response))
    cvm.issuer_cnpj.cache_clear()
    try:
        assert cvm.issuer_cnpj("PETR4") == "33.000.167/0001-01"
    finally:
        cvm.issuer_cnpj.cache_clear()
