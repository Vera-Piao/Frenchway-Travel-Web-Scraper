from pathlib import Path
import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def fetch_html(url, timeout=15):
    """
    Send an HTTP GET request and return the response.
    """

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
        )

        return response

    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {url}")
        return None

    except requests.exceptions.ConnectionError:
        print(f"[CONNECTION ERROR] {url}")
        return None

    except requests.exceptions.RequestException as error:
        print(f"[REQUEST ERROR] {url}: {error}")
        return None


def save_html(html, category, site_name):
    """
    Save HTML content under data/raw/<category>/.
    """

    output_dir = Path("data/raw") / category
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{site_name}.html"

    output_file.write_text(
        html,
        encoding="utf-8",
    )

    return output_file