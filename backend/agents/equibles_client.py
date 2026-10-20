"""Bounded official-release discovery; Equibles never supplies the analysis prompt."""
import json
import logging
import os
import re
from urllib.parse import quote

import requests

logger = logging.getLogger("uvicorn.error")


class EquiblesClient:
    def __init__(self):
        self.api_key = os.getenv("EQUIBLES_API_KEY", "").strip()
        self.last_status = "disabled"

    def release_candidates(self, ticker):
        if not self.api_key or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", ticker):
            return []
        try:
            # Fixed host, no redirects: never forward the credential to a source document.
            with requests.get(f"https://api.equibles.com/v1/stocks/{quote(ticker, safe='')}/ir-news",
                              params={"limit": 50, "offset": 0},
                              headers={"Authorization": f"Bearer {self.api_key}"},
                              timeout=(2, 6), allow_redirects=False, stream=True) as response:
                self.last_status = f"http_{response.status_code}"
                if response.status_code != 200:
                    logger.info("equibles_release_lookup issuer=%s outcome=%s", ticker, self.last_status)
                    return []
                data = bytearray()
                for chunk in response.iter_content(65536):
                    data.extend(chunk)
                    if len(data) > 1_000_000:
                        self.last_status = "oversized_response"
                        return []
            payload = json.loads(data)
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                self.last_status = "invalid_response"
                return []
            if payload.get("ticker", ticker).upper() != ticker:
                self.last_status = "issuer_mismatch"
                return []
            rows = [{"title": row["title"], "url": row["url"]}
                    for row in payload["data"][:50] if isinstance(row, dict)
                    and isinstance(row.get("title"), str) and isinstance(row.get("url"), str)]
            self.last_status = "ok"
            logger.info("equibles_release_lookup issuer=%s outcome=ok candidates=%d", ticker, len(rows))
            return rows
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            self.last_status = "unavailable"
            logger.info("equibles_release_lookup issuer=%s outcome=unavailable", ticker)
            return []
