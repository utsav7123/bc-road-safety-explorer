from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGES = [SITE / "index.html", SITE / "methodology" / "index.html", SITE / "404.html"]


def test_pages_have_one_h1_and_no_em_dash():
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        assert len(re.findall(r"<h1(?:\s|>)", text, re.I)) == 1
        assert "—" not in text
        assert "TODO" not in text


def test_public_pages_have_metadata():
    for page in PAGES[:2]:
        text = page.read_text(encoding="utf-8")
        assert "<title>" in text
        assert 'name="description"' in text
        assert 'rel="canonical"' in text
        assert 'application/ld+json' in text


def test_discovery_files_exist():
    for name in ("robots.txt", "sitemap.xml", "llms.txt"):
        assert (SITE / name).exists()


def test_internal_relative_links_resolve():
    pattern = re.compile(r'href="([^"]+)"')
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        for href in pattern.findall(text):
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("#"):
                continue
            target = (page.parent / parsed.path).resolve()
            if parsed.path.endswith("/") or parsed.path in ("./", "../"):
                target = target / "index.html"
            assert target.exists(), f"Broken link {href} in {page}"


def test_javascript_has_motion_and_no_source_map():
    js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
    css = (SITE / "assets" / "styles.css").read_text(encoding="utf-8")
    assert "requestAnimationFrame" in js
    assert "setInterval" in js
    assert "IntersectionObserver" in js
    assert "@keyframes" in css
    assert "prefers-reduced-motion" in css
    assert "sourceMappingURL" not in js
    assert "console.error" not in js
