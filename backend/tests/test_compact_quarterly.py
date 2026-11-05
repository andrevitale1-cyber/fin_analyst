import pytest

from quarterly_results import parse_results, validate_quarterly_result


@pytest.mark.parametrize('en', [False, True])
def test_compact_report_keeps_highlights_and_conclusion_without_internal_labels(en):
    section = 'Section' if en else 'Seção'
    score = 'Section Score' if en else 'Nota Seção'
    overall = 'Overall Score' if en else 'Nota Geral'
    classification = 'Quarter Classification' if en else 'Classificação do Trimestre'
    text = '<!-- compact-quarterly -->\n' + '\n\n'.join(
        f'{section} {i}: Topic\n**Metric {i} increased.** Cause and implication.\n{score} {i}: 4/5'
        for i in range(1, 5)
    ) + f'\n{section} 5: Conclusion\n**AI Conclusion:** Growth supports the business.\n{section} 6: Rating\n{overall}: 4/5\n{classification}: Good'
    parsed = parse_results(text)
    validate_quarterly_result(parsed, 'en' if en else 'pt')
    visible = parsed['tese_investimento']
    assert all(f'**Metric {i} increased.**' in visible for i in range(1, 5))
    assert '**AI Conclusion:** Growth supports the business.' in visible
    assert '4/5' in visible
    assert all(label not in visible for label in ('<!--', section + ' 1:', score, classification))
    assert parsed['nota_geral'] == 4 and parsed['rated_fundamentals'] == 4


def test_legacy_report_still_extracts_only_its_conclusion():
    parsed = parse_results('Seção 1: Receita\nReceita cresceu.\nSeção 5: Conclusão\nTese original.\nSeção 6: Nota Final\nNota Geral: 4/5')
    assert parsed['tese_investimento'] == 'Tese original.'
