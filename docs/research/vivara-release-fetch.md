# Vivara 1T2026 release discovery

Verified on 2026-10-19 against the official Vivara IR center and its MZ file-manager catalogue:

- IR: https://ri.vivara.com.br/informacoes-financeiras/central-de-resultados/
- The company uses ticker `VIVA3`, MZ company ID `61a4df2d-a461-44d6-9128-da74058019db`, and release category `release-de-resultados`.
- Official 1T26 PDF: https://api.mziq.com/mzfilemanager/v2/d/61a4df2d-a461-44d6-9128-da74058019db/ec873dcd-5db5-e43f-868d-f2c3f512d012?origin=2

The failed production attempt returned 404 after 37 seconds. There were several reproducible lookup gaps: Vivara's name/ticker and IR centre were unmapped, the catalogue parser did not allow hyphenated categories, and the PDF's spaced cover text (`1 T 2 6`) caused the period validator to see the comparative `1T25` footnote first. Python Requests also failed certificate-chain validation for the IR HTML locally, while its catalogue and PDF validated successfully. TLS verification remains enabled.

Vivara now resolves to VIVA3 and queries its verified catalogue directly. Existing issuer, publication, year/quarter, host and download-path checks still apply. Cover typography is normalized before validating the PDF period, and wrong-period covers remain rejected even when comparative figures mention the requested quarter. The existing IR and web-search fallbacks remain available; failed search JSON is reported as a provider failure instead of a missing document.

The real cold automatic lookup, including downloading and validating the 4.4 MB PDF, took 7.84 seconds. A subsequent alias lookup reused the cache in 0.091 seconds. Paid search was blocked for this check and was not called; no paid AI analysis was generated.

The Brazilian path uses issuer IR/catalogues and web search (Tavily, then OpenAI when needed). It is not a direct B3/CVM database integration. New documents are labelled `RI` rather than the ambiguous `B3/RI`. Logs now record the normalized issuer/period and the search provider/candidate count without recording source bodies or credentials.
