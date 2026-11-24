"""Count public repos whose workflows use this action and write a shields.io badge to stats.json.

    GH_TOKEN=... GITHUB_REPOSITORY=owner/repo python3 stats.py

Uses GitHub code search, so it only sees public repos that GitHub has indexed (default branch).
New repos can take a while to show up.
"""
import json
import os
import urllib.parse
import urllib.request

repo = os.environ["GITHUB_REPOSITORY"]
query = urllib.parse.quote(f'"{repo}@" path:.github/workflows')
users = set()

for page in range(1, 11):  # code search caps at 1000 results
    req = urllib.request.Request(
        f"https://api.github.com/search/code?q={query}&per_page=100&page={page}",
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json"},
    )
    items = json.load(urllib.request.urlopen(req))["items"]
    users |= {i["repository"]["full_name"] for i in items if i["repository"]["full_name"].lower() != repo.lower()}
    if len(items) < 100:
        break

with open("stats.json", "w") as f:
    json.dump({"schemaVersion": 1, "label": "used by", "message": f"{len(users)} repos", "color": "0969da"}, f)
print(f"used by {len(users)} repos")
