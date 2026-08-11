#!/usr/bin/env python3
"""Dependency-free WCL HTTP and deterministic artifact helpers."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
import random
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
API_URL = "https://www.warcraftlogs.com/api/v2/client"
USER_AGENT = "wow-rotation-research/1.0"


class WCLRequestError(RuntimeError):
    """A sanitized WCL transport or GraphQL failure."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def query_sha256(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json(path: Path, value: Any) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    _atomic_bytes(path, payload)


def write_gzip_json(path: Path, value: Any) -> None:
    _atomic_bytes(
        path,
        gzip.compress(canonical_json_bytes(value), compresslevel=9, mtime=0),
    )


def write_gzip_jsonl(path: Path, values: Iterable[Any]) -> None:
    payload = b"".join(canonical_json_bytes(value) + b"\n" for value in values)
    _atomic_bytes(path, gzip.compress(payload, compresslevel=9, mtime=0))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rate_limit_remaining(rate_limit: dict[str, Any] | None) -> float | None:
    if not rate_limit:
        return None
    limit = rate_limit.get("limitPerHour")
    spent = rate_limit.get("pointsSpentThisHour")
    if not isinstance(limit, (int, float)) or not isinstance(spent, (int, float)):
        return None
    return float(limit) - float(spent)


class WCLClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        timeout: int = 90,
        max_retries: int = 4,
    ) -> None:
        if not client_id or not client_secret:
            raise ValueError("WCL_CLIENT_ID and WCL_CLIENT_SECRET are required")
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout = timeout
        self._max_retries = max_retries
        self._token: str | None = None

    def _request_json(self, request: urllib.request.Request) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:2000]
                last_error = WCLRequestError(f"WCL HTTP {exc.code}: {body}")
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt >= self._max_retries:
                    raise last_error from None
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = WCLRequestError(f"WCL transport failure: {exc}")
                if attempt >= self._max_retries:
                    raise last_error from None
                delay = 2**attempt
            time.sleep(delay + random.random() * 0.25)
        raise WCLRequestError(str(last_error or "WCL request failed"))

    def token(self) -> str:
        if self._token:
            return self._token
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode("utf-8")
        ).decode("ascii")
        request = urllib.request.Request(
            TOKEN_URL,
            data=urllib.parse.urlencode(
                {"grant_type": "client_credentials"}
            ).encode("ascii"),
            method="POST",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
        )
        response = self._request_json(request)
        token = response.get("access_token")
        if not isinstance(token, str) or not token:
            raise WCLRequestError("OAuth succeeded without an access token")
        self._token = token
        return token

    def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            API_URL,
            data=canonical_json_bytes(
                {"query": query, "variables": variables or {}}
            ),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        response = self._request_json(request)
        errors = response.get("errors")
        if errors:
            raise WCLRequestError(
                "WCL GraphQL error: "
                + json.dumps(errors, ensure_ascii=False)[:4000]
            )
        data = response.get("data")
        if not isinstance(data, dict):
            raise WCLRequestError("WCL GraphQL response did not contain data")
        return data
