#!/usr/bin/env python3
"""Show GitHub asset download totals and distinct accounts reporting asset use."""
import json
import re
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

API = "https://api.github.com/repos/zuujiscom/free-game-assets"


def github_pages(path):
    url = f"{API}/{path}"
    while url:
        request = Request(url, headers={"Accept": "application/vnd.github+json"})
        with urlopen(request, timeout=20) as response:
            yield from json.load(response)
            link_header = response.headers.get("Link", "")
        match = re.search(r'<([^>]+)>; rel="next"', link_header)
        url = match.group(1) if match else None


def stats():
    counts = {}
    for release in github_pages("releases?per_page=100"):
        if release["draft"]:
            continue
        for asset in github_pages(f"releases/{release['id']}/assets?per_page=100"):
            name = asset["name"]
            if name.endswith((".zip", ".glb")):
                counts[name] = counts.get(name, 0) + asset["download_count"]
    reports = [
        issue
        for issue in github_pages("issues?labels=asset-use&state=all&per_page=100")
        if "pull_request" not in issue
        and issue.get("user")
        and issue["user"].get("type") == "User"
    ]
    reporters = {issue["user"]["id"] for issue in reports}
    return counts, len(reports), len(reporters)


def main():
    try:
        counts, report_count, reporter_count = stats()
    except (URLError, TimeoutError, ValueError, KeyError) as error:
        print(f"Could not read GitHub statistics: {error}", file=sys.stderr)
        return 1
    for extension, title in ((".zip", "ZIP downloads by pack"), (".glb", "Individual GLB downloads by model")):
        group = [(name, count) for name, count in counts.items() if name.endswith(extension)]
        print(f"{title} (all releases)")
        for name, count in sorted(group, key=lambda item: (-item[1], item[0])):
            print(f"  {count:>6,}  {name}")
        print(f"  Total: {sum(count for _, count in group):,}\n")
    print(f"Project-use reports: {report_count:,}")
    print(f"Distinct GitHub accounts reporting use: {reporter_count:,}")
    print("\nDownload totals include repeats. Reports are voluntary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
