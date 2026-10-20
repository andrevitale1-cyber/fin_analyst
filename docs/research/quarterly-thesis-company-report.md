# Quarterly thesis and company report entry points

The saved WEG 2Q2026 analysis contained the complete strategic conclusion, but its `## Section 5` heading did not match the thesis parser. The dashboard displayed a generic placeholder. The shared extractor now accepts Portuguese/English headings with Markdown hashes and bold markers, preserves the thesis's bold prose, and stops before scores or chart JSON. History responses recover affected theses from the original saved analysis without changing scores, writing database records or calling AI.

The full-report action now opens the company-wide report regardless of whether the quarterly analysis came from automatic lookup, upload or history. The legacy `analysisId` entry point checks ownership, loads only the issuer, closes that read transaction, then uses the same company-report service and shared cache as the Full Reports tab. It does not load the selected quarter's original file or AI text into public research. Existing saved period reports remain accessible; new expansions through this entry point are company reports.

The WEG company report also contained `BVMF` in its model-generated `symbol` field. Company reports now use their canonical `company` identifier for logo identity on both fresh generation and reads of existing saved reports. The gallery and reader therefore use WEGE3's local logo without regenerating the report.

Validation: 227 backend tests, frontend production build, and desktop/mobile browser checks using the actual saved WEG quarterly analysis and public company report. Research/generation APIs were mocked during browser checks; no paid report regeneration was performed.
