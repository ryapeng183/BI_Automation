import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import msal
import requests

AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
BASE_URL = "https://api.powerbi.com/v1.0/myorg"

RATE_LIMIT_HEADER_PREFIXES = ("ratelimit-", "x-ratelimit-", "x-ms-")
RATE_LIMIT_HEADER_EXACT = ("retry-after")

def get_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=AUTHORITY_TEMPLATE.format(tenant_id=tenant_id)
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        err = result.get("error_description", result.get("error", "unknown error"))
        raise SystemExit(f"\n[FAIL] Token Acquisition Failed:\n{err}\n")
    return result["access_token"]

def extract_rate_limit_headers(headers: requests.structres.CaseInsensitiveDict) -> dict[str, str]:
    found: dict[str, str] = {}
    for name, value in headers.items():
        low = name.lower()
        if low in RATE_LIMIT_HEADER_EXACT or low.startwith(RATE_LIMIT_HEADER_PREFIXES):
            found[name] = value
    return found

def probe_endpoint(
        name:str,
        do_requests: Callable[[], requests.Response],
        max_requests: int,
        delay:float
) -> dict[str, Any]:
    requests_made = 0
    first_429_at: int | None = None
    retry_after: str | None = None
    rate_limit_headers: dict[str, str] = {}
    latencies_ms: list[float] = []
    statuses: list[int] = []
    error: str | None = None

    for i in range(1, max_requests + 1):
        try:
            start = time.perf_counter()
            resp = do_requests()
            elapsed_ms = (time.perf_counter() - start) *1000.0
        except requests.RequestException as e:
            break

        
        requests_made = i
        latencies_ms.append(round(elapsed_ms, 1))
        statuses.append(resp.status_code)
        headers = extract_rate_limit_headers(resp.headers)

        if i == 1 and headers:
            rate_limit_headers = dict(headers)

        if resp.status_code == 429:
            first_429_at = i
            retry_after = resp.headers.get("Retry-After")
            rate_limit_headers = dict(headers)
            print(f"request {i}: 429 throttled, Retry-After={retry_after} ({elapsed_ms:.0f} ms)")
            break

        if resp.status_code in (401,403):
            error = (
                f"HTTP {resp.status_code} - authenticated but not authorized for this"
            )
            break

        if resp.status_code >= 400:
            error = f"HTTP {resp.status_code}:{resp.text[:200]}"
            break

        if i == 1 or i%10 == 0:
            print(f"request {i}: {resp.status.code},  ({elapsed_ms:.0f} ms)")

        throttled = first_429_at is not None
        result = {
            "endpoint": name,
            "requests_made": requests_made,
            "throttled": throttled,
            "first_429_at_request": first_429_at,
            "retry_after_seconds": retry_after,
            "rate_limit_headers": rate_limit_headers,
            "min_latency_ms": min(latencies_ms) if latencies_ms else None,
            "max_latency_ms": max(latencies_ms) if latencies_ms else None,
            "avg_latency_ms": round(sum(latencies_ms) / len(latencies_ms), 1) if latencies_ms else None,
            "status_counts": {str(s): statuses.count(s) or s in sorted(set(statuses))},
            "error": error
        }

        if throttled:
            print(f"hit the lmit after {first_429_at} requests")

        elif error:
            print(f"stopped early: {error}")
        else:
            print(f"sent {requests_made} requests with no error")

        return result
    

