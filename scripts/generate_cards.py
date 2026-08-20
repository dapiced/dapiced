#!/usr/bin/env python3
"""Generate space-themed profile stat cards from live GitHub data.

Self-hosted replacement for github-readme-stats / github-profile-trophy:
queries the GitHub REST API and renders SVG cards (dark + light variants)
into an output directory, published to the `output` branch by CI.

Usage: python scripts/generate_cards.py [output_dir]   (default: dist)
Env:   GITHUB_TOKEN - optional, raises API rate limits in CI.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

USER = "dapiced"
API = "https://api.github.com"

LANG_COLORS = {
    "Python": "#3572A5", "R": "#198CE7", "HTML": "#e34c26", "CSS": "#563d7c",
    "Shell": "#89e051", "JavaScript": "#f1e05a", "PowerShell": "#012456",
    "Jinja": "#a52a22", "Dockerfile": "#384d54", "Perl": "#0298c3",
    "Jupyter Notebook": "#DA5B0B", "Makefile": "#427819",
}

THEMES = {
    "dark": {
        "bg1": "#0b1226", "bg2": "#0d1526", "border": "#22304f",
        "title": "#58a6ff", "number": "#79c0ff", "label": "#8b949e",
        "text": "#c9d1d9", "muted": "#6e7f9b", "accent": "#bc8cff",
        "star": "#e3b341", "track": "#1c2740",
    },
    "light": {
        "bg1": "#ffffff", "bg2": "#f6f8fa", "border": "#d0d7de",
        "title": "#0969da", "number": "#0550ae", "label": "#57606a",
        "text": "#24292f", "muted": "#6e7781", "accent": "#8250df",
        "star": "#bf8700", "track": "#eaeef2",
    },
}

FONT = "font-family=\"Segoe UI, Ubuntu, Helvetica, Arial, sans-serif\""
MONO = "font-family=\"Consolas, 'Courier New', monospace\""


def get(url):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": f"{USER}-profile-cards"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def card_shell(w, h, t, deco_stars=True):
    stars = ""
    if deco_stars:
        pts = [(w - 30, 18, 1.2), (w - 55, 30, 0.9), (w - 18, 40, 0.8),
               (w - 30, h - 16, 0.9), (w - 52, h - 26, 0.7)]
        dots = "".join(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{t["accent"]}" opacity="0.55"/>'
            for x, y, r in pts)
        stars = f"<g>{dots}</g>"
    return (
        f'<defs><linearGradient id="cardbg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{t["bg1"]}"/>'
        f'<stop offset="100%" stop-color="{t["bg2"]}"/></linearGradient></defs>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" '
        f'fill="url(#cardbg)" stroke="{t["border"]}"/>' + stars)


def render_stats(user, stars, forks, t):
    w, h = 450, 170
    since = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    items = [
        ("TOTAL STARS EARNED", stars),
        ("FORKS OF MY WORK", forks),
        ("FOLLOWERS", user["followers"]),
        ("PUBLIC REPOSITORIES", user["public_repos"]),
    ]
    cells = ""
    for i, (label, val) in enumerate(items):
        x = 34 + (i % 2) * 215
        y = 66 + (i // 2) * 48
        cells += (
            f'<text x="{x}" y="{y}" {FONT} font-size="24" font-weight="700" '
            f'fill="{t["number"]}">{val}</text>'
            f'<text x="{x}" y="{y + 16}" {FONT} font-size="10" letter-spacing="1" '
            f'fill="{t["label"]}">{label}</text>')
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub stats">'
        + card_shell(w, h, t)
        + f'<text x="34" y="32" {FONT} font-size="14" font-weight="700" '
          f'letter-spacing="2" fill="{t["title"]}">MISSION TELEMETRY - @{USER}</text>'
        + f'<line x1="34" y1="42" x2="{w - 34}" y2="42" stroke="{t["border"]}"/>'
        + cells
        + f'<text x="34" y="{h - 14}" {MONO} font-size="10" fill="{t["muted"]}">'
          f'in orbit since {since.strftime("%b %Y")} · telemetry refreshed daily</text>'
        + "</svg>")


def render_langs(tech_counts, t):
    w, h = 450, 170
    total = sum(tech_counts.values()) or 1
    top = sorted(tech_counts.items(), key=lambda kv: -kv[1])[:6]
    bar_x, bar_w, bar_y = 34, w - 68, 58
    x = bar_x
    segs = ""
    for name, b in top:
        seg = max(4, round(bar_w * b / total))
        seg = min(seg, bar_x + bar_w - x)
        color = LANG_COLORS.get(name, t["accent"])
        segs += f'<rect x="{x}" y="{bar_y}" width="{seg}" height="10" fill="{color}"/>'
        x += seg
    legend = ""
    for i, (name, b) in enumerate(top):
        lx = 34 + (i % 2) * 215
        ly = 96 + (i // 2) * 24
        color = LANG_COLORS.get(name, t["accent"])
        pct = 100 * b / total
        legend += (
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 18}" y="{ly}" {FONT} font-size="12" fill="{t["text"]}">'
            f'{esc(name)}</text>'
            f'<text x="{lx + 175}" y="{ly}" {FONT} font-size="12" text-anchor="end" '
            f'fill="{t["label"]}">{pct:.0f}%</text>')
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tech footprint">'
        + card_shell(w, h, t)
        + f'<text x="34" y="32" {FONT} font-size="14" font-weight="700" '
          f'letter-spacing="2" fill="{t["title"]}">TECH FOOTPRINT - BY REPOSITORY</text>'
        + f'<line x1="34" y1="42" x2="{w - 34}" y2="42" stroke="{t["border"]}"/>'
        + f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" '
          f'fill="{t["track"]}"/>'
        + f'<g clip-path="url(#barclip)">{segs}</g>'
        + f'<clipPath id="barclip"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" '
          f'height="10" rx="5"/></clipPath>'
        + legend + "</svg>")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out, exist_ok=True)

    user = get(f"{API}/users/{USER}")
    repos = get(f"{API}/users/{USER}/repos?per_page=100")
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    forks = sum(r["forks_count"] for r in own)

    # Primary tech per repo. Linguist ignores YAML, which would hide the
    # Ansible roles entirely - infer them from topics/name instead.
    tech_counts = {}
    for r in own:
        if r["name"] == USER:  # profile repo itself
            continue
        tech = r.get("language")
        topics = r.get("topics") or []
        if not tech and ("ansible" in topics or "ansible" in r["name"].lower()):
            tech = "Ansible"
        if tech:
            tech_counts[tech] = tech_counts.get(tech, 0) + 1
    LANG_COLORS.setdefault("Ansible", "#EE0000")

    written = []
    for variant, t in THEMES.items():
        suffix = "dark" if variant == "dark" else "light"
        files = {
            f"stats-{suffix}.svg": render_stats(user, stars, forks, t),
            f"langs-{suffix}.svg": render_langs(tech_counts, t),
        }
        for fname, svg in files.items():
            with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
                f.write(svg)
            written.append(fname)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"generated {len(written)} cards in {out}/ at {stamp}")
    for f in sorted(written):
        print(" -", f)


if __name__ == "__main__":
    main()
