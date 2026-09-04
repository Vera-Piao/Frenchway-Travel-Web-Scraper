"""HTTP and file helpers used by the Frenchway collection pipeline."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


@dataclass
class FetchResult:
    response: requests.Response | None
    error_type: str = ""
    error_message: str = ""
    elapsed_seconds: float = 0.0


def create_http_session(retries=2, backoff_factor=0.8):
    """Create a retrying HTTP session for transient failures only."""
    retry_policy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_url(url, timeout=15, retries=2, session=None):
    """Fetch a URL and return response, timing, and normalized error data."""
    owned_session = session is None
    client = session or create_http_session(retries=retries)
    started = perf_counter()

    try:
        response = client.get(
            url,
            timeout=timeout,
            allow_redirects=True,
        )
        return FetchResult(response=response, elapsed_seconds=round(perf_counter() - started, 3))
    except requests.exceptions.Timeout as error:
        return FetchResult(None, "timeout", str(error), round(perf_counter() - started, 3))
    except requests.exceptions.ConnectionError as error:
        return FetchResult(None, "connection_error", str(error), round(perf_counter() - started, 3))
    except requests.exceptions.RequestException as error:
        return FetchResult(None, "request_error", str(error), round(perf_counter() - started, 3))
    finally:
        if owned_session:
            client.close()


def fetch_html(url, timeout=15):
    """Backward-compatible helper returning only the HTTP response."""
    return fetch_url(url, timeout=timeout).response


def save_html(html, category, site_name, raw_data_dir="data/raw"):
    """
    Save HTML content under data/raw/<category>/.
    """

    output_dir = Path(raw_data_dir) / category
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{site_name}.html"

    payload = html if isinstance(html, bytes) else html.encode("utf-8")
    temporary_file = output_file.with_suffix(".html.tmp")
    temporary_file.write_bytes(payload)
    temporary_file.replace(output_file)

    return output_file


def content_sha256(content):
    """Return a stable SHA-256 digest for response or file bytes."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return sha256(content).hexdigest()
