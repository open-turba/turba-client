"""HTTP session helpers."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from turba_client.constants import DEFAULT_USER_AGENT


def build_session(max_retries: int = 3, user_agent: str | None = None) -> requests.Session:
    """Create a retry-aware HTTP session."""
    retry = Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent or DEFAULT_USER_AGENT})
    return session
