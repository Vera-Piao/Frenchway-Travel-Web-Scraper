from targets import TARGETS
from utils import fetch_html, save_html


def scrape_site(category, site_name, url):
    print(f"\nRequesting: {site_name}")
    print(f"URL: {url}")

    response = fetch_html(url)

    if response is None:
        return "failed"

    status_code = response.status_code

    if status_code == 200:
        output_file = save_html(
            response.text,
            category,
            site_name,
        )
        print(f"[200 OK] Saved to: {output_file}")
        return "success"

    elif status_code == 403:
        print(f"[403 FORBIDDEN] Access denied: {url}")
        return "forbidden"

    elif status_code == 404:
        print(f"[404 NOT FOUND] Page not found: {url}")
        return "not_found"

    else:
        print(f"[{status_code}] Request returned status code {status_code}: {url}")
        return "other"


def main():
    stats = {
        "success": 0,
        "forbidden": 0,
        "not_found": 0,
        "failed": 0,
        "other": 0,
    }

    total = 0

    for category, sites in TARGETS.items():

        print("\n" + "=" * 60)
        print(f"Category: {category}")
        print("=" * 60)

        for site_name, url in sites.items():
            total += 1

            result = scrape_site(
                category,
                site_name,
                url,
            )

            stats[result] += 1

    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)

    print(f"Total sites: {total}")
    print(f"Successful: {stats['success']}")
    print(f"Forbidden: {stats['forbidden']}")
    print(f"Not found: {stats['not_found']}")
    print(f"Failed requests: {stats['failed']}")
    print(f"Other status codes: {stats['other']}")


if __name__ == "__main__":
    main()