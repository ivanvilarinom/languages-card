"""Write an SVG card with the primary language of every repo the token can see.

    GH_TOKEN=... python3 languages.py [output.svg]
    python3 languages.py --demo    # self-check, no token needed
"""
import json
import os
import sys
import urllib.request
from collections import Counter

# Same colors GitHub uses (github-linguist). Unknown languages fall back to grey.
COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Shell": "#89e051", "HTML": "#e34c26", "CSS": "#563d7c", "Vue": "#41b883",
    "C++": "#f34b7d", "C": "#555555", "C#": "#178600", "Dockerfile": "#384d54",
    "Go": "#00ADD8", "Java": "#b07219", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95", "Dart": "#00B4AB",
    "Jupyter Notebook": "#DA5B0B", "Svelte": "#ff3e00", "Lua": "#000080",
}
MAX_ITEMS = 8  # 4 columns x 2 rows; the rest goes into "Other"


def fetch_counts(token):
    counts, page, seen_private = Counter(), 1, False
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/user/repos?affiliation=owner&per_page=100&page={page}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        repos = json.load(urllib.request.urlopen(req))
        if not repos:
            break
        seen_private |= any(r["private"] for r in repos)
        counts.update(r["language"] for r in repos if r["language"] and not r["fork"])
        page += 1
    if not seen_private:
        print("::warning::The token only sees public repositories. See the README to include private ones.")
    return counts


def render(counts):
    total = sum(counts.values())
    items = counts.most_common()
    if len(items) > MAX_ITEMS:
        items = items[: MAX_ITEMS - 1] + [("Other", sum(n for _, n in items[MAX_ITEMS - 1 :]))]

    bar, x = [], 24.0
    for i, (lang, n) in enumerate(items):
        w = 576 - x if i == len(items) - 1 else round(552 * n / total, 1)
        bar.append(f'<rect x="{x:.1f}" y="46" width="{w:.1f}" height="8" fill="{COLORS.get(lang, "#8b949e")}"/>')
        x += w

    legend = []
    for i, (lang, n) in enumerate(items):
        cx, cy = 28 + 140 * (i % 4), 82 + 24 * (i // 4)
        legend.append(
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="{COLORS.get(lang, "#8b949e")}"/>'
            f'<text x="{cx + 10}" y="{cy + 4}">{lang} {100 * n / total:.1f}%</text>'
        )

    font = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
    nl = "\n    "
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="130" viewBox="0 0 600 130">
  <style>
    .bg {{ fill: #f6f8fa; stroke: #d0d7de; }}
    .h {{ font: 600 14px {font}; fill: #1f2328; }}
    .s, .l {{ font: 400 12px {font}; fill: #59636e; }}
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #0d1117; stroke: #30363d; }}
      .h {{ fill: #e6edf3; }}
      .s, .l {{ fill: #8b949e; }}
    }}
  </style>
  <defs><clipPath id="bar"><rect x="24" y="46" width="552" height="8" rx="4"/></clipPath></defs>
  <rect class="bg" x=".5" y=".5" width="599" height="129" rx="8"/>
  <text class="h" x="24" y="30">Languages</text>
  <text class="s" x="576" y="30" text-anchor="end">Primary language across {total} repositories</text>
  <g clip-path="url(#bar)">
    {nl.join(bar)}
  </g>
  <g class="l">
    {nl.join(legend)}
  </g>
</svg>
"""


if __name__ == "__main__":
    if "--demo" in sys.argv:
        svg = render(Counter({"Python": 21, "TypeScript": 5, "Shell": 4, "HTML": 2, "Vue": 1, "C++": 1, "Dockerfile": 1}))
        assert "Python 60.0%" in svg and "across 35 repositories" in svg
        many = render(Counter({f"L{i}": 1 for i in range(10)}))
        assert "Other 30.0%" in many and many.count("<circle") == MAX_ITEMS
        print("ok")
    else:
        out = sys.argv[1] if len(sys.argv) > 1 else "languages.svg"
        with open(out, "w") as f:
            f.write(render(fetch_counts(os.environ["GH_TOKEN"])))
