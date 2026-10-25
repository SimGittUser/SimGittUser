#!/usr/bin/env python3
"""Build a black-and-white Codeforces stats card (SVG) from the public Codeforces API.

Run by the GitHub Action twice a day. Standard library only.

    python scripts/cf_card.py --handle codeof_akshit --out dist
    python scripts/cf_card.py --handle demo --out dist --sample   # offline preview
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
BLACK, WHITE, MUTED, LINE = "#0a0a0a", "#ffffff", "#737373", "#e5e5e5"
FB = "'IDBlack', 'Inter Display', 'Segoe UI', Arial, sans-serif"
FT = "'IBold', 'Inter', 'Segoe UI', Arial, sans-serif"
FS = "'ISemi', 'Inter', 'Segoe UI', Arial, sans-serif"


def api(method, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://codeforces.com/api/{method}?{q}"
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-card"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            if data.get("status") == "OK":
                return data["result"]
            last = RuntimeError(data.get("comment", "API error"))
        except Exception as e:  # network hiccup or Codeforces rate limit
            last = e
        time.sleep(2 + attempt * 3)
    raise last


def collect(handle):
    info = api("user.info", handles=handle)[0]
    subs = api("user.status", handle=handle)
    contests = api("user.rating", handle=handle)
    solved = {}
    for s in subs:
        if s.get("verdict") != "OK":
            continue
        p = s["problem"]
        key = (p.get("contestId"), p.get("index")) if p.get("contestId") else p.get("name")
        solved[key] = p.get("rating")
    return {
        "handle": info["handle"],
        "rating": info.get("rating"),
        "maxRating": info.get("maxRating"),
        "rank": info.get("rank", "unrated"),
        "contests": len(contests),
        "solved": len(solved),
        "ratings": [r for r in solved.values() if r],
    }


def sample():
    return {"handle": "demo_user", "rating": 1063, "maxRating": 1082, "rank": "newbie", "contests": 12,
            "solved": 187, "ratings": [800] * 70 + [900] * 38 + [1000] * 27 + [1100] * 16 + [1200] * 10 + [1300] * 5 + [1400] * 3 + [1600]}


def buckets(ratings, max_bars=9):
    if not ratings:
        return []
    counts = {}
    for r in ratings:
        counts[r] = counts.get(r, 0) + 1
    keys = sorted(counts)
    lo = keys[0]
    out = []
    r = lo
    while r <= keys[-1]:
        out.append([str(r), counts.get(r, 0)])
        r += 100
    if len(out) > max_bars:  # fold the hardest ones into "X+"
        head, tail = out[: max_bars - 1], out[max_bars - 1:]
        out = head + [[tail[0][0] + "+", sum(c for _, c in tail)]]
    return out


def card(d, fonts):
    W, H = 900, 230
    style = "".join(
        f"@font-face{{font-family:'{n}';src:url(data:font/woff;base64,{b}) format('woff');}}" for n, b in fonts.items())
    rank = " ".join(w.capitalize() for w in str(d["rank"]).split())
    rating = d["rating"] if d["rating"] is not None else "–"
    peak = d["maxRating"] if d["maxRating"] is not None else "–"
    today = dt.date.today().strftime("%d %b %Y")

    def stat(x, y, label, value, size=30):
        return (f'<text x="{x}" y="{y}" font-family="{FS}" font-size="12.5" fill="{MUTED}">{label}</text>'
                f'<text x="{x}" y="{y+32}" font-family="{FB}" font-size="{size}" fill="{BLACK}">{value}</text>')

    # long ranks ("International Grandmaster") shrink to fit the column
    rank_size = min(30, round(225 / (0.56 * max(len(rank), 1)), 1))
    contests = f"{d['contests']} contest" + ("" if d["contests"] == 1 else "s")

    bars = buckets(d["ratings"])
    BX0, BX1, BY0, BY1 = 600, 866, 70, 186
    chart = ""
    if bars:
        n = len(bars)
        slot = (BX1 - BX0) / n
        bw = min(26, slot * 0.62)
        top = max(c for _, c in bars) or 1
        for i, (lab, c) in enumerate(bars):
            h = (BY1 - BY0 - 18) * c / top
            x = BX0 + i * slot + (slot - bw) / 2
            cx = x + bw / 2
            chart += (f'<rect x="{x:.1f}" y="{BY1:.1f}" width="{bw:.1f}" height="0" rx="3" fill="{BLACK}">'
                      f'<animate attributeName="height" from="0" to="{h:.1f}" dur="1s" begin="{i*0.08:.2f}s" fill="freeze"/>'
                      f'<animate attributeName="y" from="{BY1}" to="{BY1-h:.1f}" dur="1s" begin="{i*0.08:.2f}s" fill="freeze"/></rect>'
                      f'<text x="{cx:.1f}" y="{BY1-h-6:.1f}" text-anchor="middle" font-family="{FT}" font-size="11" fill="{BLACK}">{c}</text>'
                      f'<text x="{cx:.1f}" y="{BY1+16}" text-anchor="middle" font-family="{FS}" font-size="10.5" fill="{MUTED}">{lab}</text>')
        chart += f'<line x1="{BX0}" x2="{BX1}" y1="{BY1}" y2="{BY1}" stroke="{BLACK}" stroke-width="1.5"/>'
    else:
        chart = f'<text x="{BX0}" y="130" font-family="{FS}" font-size="13" fill="{MUTED}">No rated problems yet</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Codeforces: {d['solved']} problems solved, rating {rating}, peak {peak}, {rank}">
<style>{style}</style>
<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="18" fill="{WHITE}" stroke="{BLACK}" stroke-width="2.5"/>
<text x="36" y="48" font-family="{FT}" font-size="14" fill="{MUTED}">Codeforces</text>
<text x="36" y="76" font-family="{FB}" font-size="24" fill="{BLACK}">@{d['handle']}</text>
<text x="34" y="162" font-family="{FB}" font-size="76" fill="{BLACK}" letter-spacing="-2">{d['solved']}</text>
<text x="36" y="192" font-family="{FT}" font-size="15" fill="{BLACK}">Problems solved<tspan font-family="{FS}" fill="{MUTED}">  ·  {contests}</tspan></text>
<line x1="300" y1="36" x2="300" y2="194" stroke="{LINE}" stroke-width="2"/>
{stat(330, 60, "Rating", rating)}{stat(450, 60, "Peak", peak)}
{stat(330, 140, "Rank", rank, rank_size)}
<line x1="570" y1="36" x2="570" y2="194" stroke="{LINE}" stroke-width="2"/>
<text x="{BX0}" y="48" font-family="{FT}" font-size="14" fill="{BLACK}">Solved by difficulty</text>
<text x="{BX1}" y="48" text-anchor="end" font-family="{FS}" font-size="11" fill="{MUTED}">Updated {today}</text>
{chart}
</svg>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--out", default="dist")
    ap.add_argument("--sample", action="store_true", help="use made-up numbers (offline preview)")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "cf-card.svg"
    fonts = json.loads((HERE / "fonts.json").read_text())
    try:
        d = sample() if a.sample else collect(a.handle)
        target.write_text(card(d, fonts), encoding="utf-8")
        print(f"cf-card.svg: {d['solved']} solved, rating {d['rating']}")
    except Exception as e:
        # Codeforces down: keep yesterday's card instead of publishing a broken image
        repo = os.environ.get("GITHUB_REPOSITORY")
        print("Codeforces API failed:", e)
        if not repo:
            raise
        url = f"https://raw.githubusercontent.com/{repo}/output/cf-card.svg"
        with urllib.request.urlopen(url, timeout=30) as r:
            target.write_bytes(r.read())
        print("kept the previous card from the output branch")


if __name__ == "__main__":
    main()
