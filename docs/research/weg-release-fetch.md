# WEG quarterly release discovery

The WEG attempt for 1T2026 failed before AI analysis. The official results center HTML contains no PDF links; its MZ CMS loads metadata after JavaScript runs.

Verified public sources:

- Center: https://ri.weg.net/informacoes-financeiras/central-de-resultados/
- The center declares its `fmId` and release category in inline configuration, and uses `mziq.cmsint.js` to POST a read-only year/category filter to `api.mziq.com/mzfilemanager/company/{fmId}/filter/categories/year/meta`.
- The API metadata identifies the exact company, category, year, quarter, publication status and file URL. The 1T2026 PDF was validated by the existing PDF/content-period checks.

`AutoFetcher` now reads this configuration without executing JavaScript. It supports mapped IR centers and centers discovered by search. Only published release-category rows for the requested year/quarter and issuer are accepted; download hosts and issuer path are checked. Existing search remains the fallback if a catalog is unavailable. The PDF content must still pass period validation before it can be cached or analyzed.

A real cold lookup on 2026-10-19 took 3.8 seconds; the second lookup took 0.026 seconds from cache. Paid search was blocked during this check and was not called. This measures document discovery, not AI analysis latency.

Regression checks cover a JavaScript-only WEG center, cache reuse, wrong issuer/year/quarter, unpublished documents, untrusted links, provider outage, and metadata that disagrees with PDF content.
