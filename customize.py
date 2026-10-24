#!/usr/bin/env python3
"""Fill in the placeholders in README.md and the SVGs in one go.

Example:
    python customize.py --name "Your Name" --linkedin your-id --email you@mail.com \
        --portfolio https://your.site --cf your_cf_handle --lc your_lc_name

Any option you skip is left as it is, so you can run it more than once.
Delete this file before or after pushing, it is not needed on GitHub.
"""
import argparse
import html
import pathlib

ROOT = pathlib.Path(__file__).parent
FILES = [ROOT / "README.md"] + sorted((ROOT / "assets").glob("*.svg"))

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--name", help="display name shown on the banner")
ap.add_argument("--linkedin", help="LinkedIn id (the part after linkedin.com/in/)")
ap.add_argument("--email")
ap.add_argument("--portfolio", help="full URL")
ap.add_argument("--cf", help="Codeforces handle")
ap.add_argument("--lc", help="LeetCode username")
a = ap.parse_args()

pairs = {
    "YOUR_NAME": a.name,
    "YOUR_LINKEDIN": a.linkedin,
    "YOUR_EMAIL": a.email,
    "YOUR_PORTFOLIO": a.portfolio,
    "CF_HANDLE": a.cf,
    "LC_USERNAME": a.lc,
}

for f in FILES:
    text = f.read_text(encoding="utf-8")
    new = text
    for token, value in pairs.items():
        if value is None:
            continue
        new = new.replace(token, html.escape(value) if f.suffix == ".svg" else value)
    if new != text:
        f.write_text(new, encoding="utf-8")
        print("updated", f.relative_to(ROOT))

left = [t for t, v in pairs.items() if v is None]
if left:
    print("still placeholders:", ", ".join(left))
