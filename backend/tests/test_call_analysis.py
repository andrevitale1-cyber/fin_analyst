from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from call_analysis import without_key_moments
from report_generator import _clean_md, generate_report_html


@pytest.mark.parametrize("heading", [
    "**5. Key moments**", "5. Key moments", "## 5. Key moments",
    "**5. Momentos principais**", "### **5. Momentos principais**",
])
def test_retired_section_removed_without_losing_conclusion_or_inline_timestamps(heading):
    analysis = "**1. Results**\nRevenue grew. [12:34]\n\n**4. AI Conclusion**\nConfident. [01:12:35]"
    assert without_key_moments(analysis + "\n\n" + heading + "\nLegacy list") == analysis


def test_unrelated_section_five_and_regular_body_text_are_preserved():
    analysis = "**4. AI Conclusion**\nThere were 5. Key moments in the discussion.\n**5. Strategic outlook**\nMore detail."
    assert without_key_moments(analysis) == analysis


def test_saved_call_export_omits_legacy_section_and_retains_timestamps():
    text = "**4. AI Conclusion**\n**Confident.** Revenue grew. [12:34]\n\n**5. Key moments**\nOld marker list"
    report = generate_report_html({"metadata": {"empresa": "Example", "tipo": "Earnings Call"}, "analise_completa": text}, locale="en")
    assert "Key moments" not in report and "Old marker list" not in report
    assert "Confident." in report and "[12:34]" in report


def test_hour_timestamp_is_a_single_badge():
    html = _clean_md("- **Guidance:** Demand remains strong. [01:12:35]")
    assert "[01:12:35]</span>" in html
