from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PUBLIC_PAGES = [
    SITE / "index.html",
    SITE / "methodology" / "index.html",
    SITE / "data-notes" / "index.html",
    SITE / "about" / "index.html",
]
PAGES = [*PUBLIC_PAGES, SITE / "404.html"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pages_have_unique_titles_descriptions_and_one_h1():
    titles = []
    descriptions = []
    for page in PAGES:
        text = read(page)
        title = re.search(r"<title>(.+?)</title>", text, re.I | re.S)
        description = re.search(r'<meta name="description" content="(.+?)">', text, re.I | re.S)
        assert title, page
        assert description, page
        assert len(re.findall(r"<h1(?:\s|>)", text, re.I)) == 1, page
        assert "TODO" not in text
        assert "lorem ipsum" not in text.lower()
        assert "—" not in text
        titles.append(title.group(1).strip())
        descriptions.append(description.group(1).strip())

    assert len(titles) == len(set(titles))
    assert len(descriptions) == len(set(descriptions))


def test_public_pages_have_complete_metadata():
    canonicals = []
    for page in PUBLIC_PAGES:
        text = read(page)
        assert 'rel="canonical"' in text, page
        assert 'rel="icon"' in text, page
        assert 'property="og:title"' in text, page
        assert 'property="og:description"' in text, page
        assert 'property="og:image"' in text, page
        assert 'name="twitter:card"' in text, page
        assert 'application/ld+json' in text, page
        canonical = re.search(r'<link rel="canonical" href="(.+?)">', text, re.I | re.S)
        assert canonical
        canonicals.append(canonical.group(1))

    assert len(canonicals) == len(set(canonicals))


def test_structured_data_uses_truthful_types():
    text = "\n".join(read(page) for page in PUBLIC_PAGES)
    assert '"@type":"WebSite"' in read(SITE / "index.html")
    assert '"@type":"Dataset"' in read(SITE / "index.html")
    assert '"@type":"BreadcrumbList"' in read(SITE / "methodology" / "index.html")
    assert '"@type":"BreadcrumbList"' in read(SITE / "data-notes" / "index.html")
    assert '"@type":"AboutPage"' in read(SITE / "about" / "index.html")
    assert "LocalBusiness" not in text


def test_discovery_and_social_assets_exist():
    for name in ("robots.txt", "sitemap.xml", "llms.txt", "site.webmanifest"):
        assert (SITE / name).exists()
    for name in ("favicon.svg", "social-card.svg"):
        assert (SITE / "assets" / name).exists()
    assert not (SITE / "assets" / "road-safety-hero.svg").exists()


def test_sitemap_lists_all_public_clean_urls():
    sitemap = read(SITE / "sitemap.xml")
    expected = [
        "https://utsav7123.github.io/bc-road-safety-explorer/",
        "https://utsav7123.github.io/bc-road-safety-explorer/methodology/",
        "https://utsav7123.github.io/bc-road-safety-explorer/data-notes/",
        "https://utsav7123.github.io/bc-road-safety-explorer/about/",
    ]
    for url in expected:
        assert f"<loc>{url}</loc>" in sitemap


def test_internal_relative_links_resolve():
    pattern = re.compile(r'href="([^"]+)"')
    for page in PAGES:
        text = read(page)
        for href in pattern.findall(text):
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("#"):
                continue
            target = (page.parent / parsed.path).resolve()
            if parsed.path.endswith("/") or parsed.path in ("./", "../"):
                target = target / "index.html"
            assert target.exists(), f"Broken link {href} in {page}"


def test_images_have_alt_text():
    for page in PUBLIC_PAGES:
        text = read(page)
        images = re.findall(r"<img\b[^>]*>", text, re.I)
        for image in images:
            assert re.search(r'\balt="[^"]*"', image, re.I), f"Missing alt in {page}: {image}"


def test_production_javascript_is_small_and_clean():
    js_path = SITE / "assets" / "app.js"
    js = read(js_path)
    assert js_path.stat().st_size < 16_000
    assert "sourceMappingURL" not in js
    assert "console.error" not in js
    assert "console.log" not in js
    assert "TODO" not in js
    assert "requestAnimationFrame" not in js
    assert "setInterval" not in js
    assert "IntersectionObserver" not in js
    assert "forecast-overlay" not in js


def test_site_avoids_decorative_motion_and_overlay_charts():
    css = read(SITE / "assets" / "styles.css")
    index = read(SITE / "index.html")
    assert "@keyframes" not in css
    assert "road-safety-hero.svg" not in index
    assert "play-years" not in index
    assert "forecast-overlay" not in index
