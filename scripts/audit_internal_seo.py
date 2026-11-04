#!/usr/bin/env python3
"""
LeadsFlo built-site technical SEO and internal-link audit.

Run after: npm run build
Usage: python3 scripts/audit_internal_seo.py

Reports:
- Broken internal links
- Canonical mismatches
- Sitemap inconsistencies
- Missing/inaccurate robots directives
- Pages with no internal links pointing to them
- Missing fragment targets
- Multiple or missing H1s
"""

from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET
import json
import sys

ROOT = Path("dist")
DOMAIN = "https://leadsflo.co"
SITEMAP = Path("public/sitemap.xml")

class PageAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.canonicals = []
        self.robots = []
        self.titles = []
        self.description = []
        self.h1_count = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)

        if data.get("id"):
            self.ids.add(data["id"])

        if tag == "a":
            if data.get("href") is not None:
                self.links.append(data["href"])
            if data.get("name"):
                self.ids.add(data["name"])

        if tag == "h1":
            self.h1_count += 1

        if tag == "title":
            self.in_title = True

        if tag == "link" and (
            "canonical" in (data.get("rel") or "").split()
        ):
            self.canonicals.append(data.get("href"))

        if tag == "meta":
            name = (data.get("name") or "").lower()
            if name == "robots":
                self.robots.append(
                    (data.get("content") or "").lower()
                )
            if name == "description":
                self.description.append(data.get("content") or "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.titles.append(data)


def page_route(path):
    relative = path.relative_to(ROOT)
    if relative == Path("index.html"):
        return "/"
    if relative.name != "index.html":
        return "/" + relative.as_posix()
    return "/" + relative.parent.as_posix().strip("/") + "/"


def resolve_path(href, current_route):
    if not href or href.startswith(
        ("mailto:", "tel:", "javascript:", "data:")
    ):
        return None

    parsed = urlsplit(href)

    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None

    if parsed.netloc and parsed.netloc.lower() not in (
        "leadsflo.co", "www.leadsflo.co"
    ):
        return None

    if not parsed.path:
        route = current_route
    elif parsed.path.startswith("/"):
        route = parsed.path
    else:
        # Resolve a relative link against the current page.
        from posixpath import normpath
        base = current_route.rsplit("/", 1)[0]
        route = normpath(base + "/" + parsed.path)

    route = unquote(route)

    if not route.startswith("/"):
        route = "/" + route

    if not route.endswith("/") and "." not in route.rsplit("/",1)[-1]:
        route += "/"

    return route, unquote(parsed.fragment)


def built_target(route):
    path = ROOT / route.lstrip("/")

    if path.is_file():
        return path

    return path / "index.html"


def main():
    if not ROOT.is_dir() or not SITEMAP.is_file():
        print("STOP: Build and sitemap required.")
        return 2

    pages = {}
    for path in ROOT.rglob("index.html"):
        route = page_route(path)
        audit = PageAudit()
        audit.feed(path.read_text(errors="replace"))
        pages[route] = audit

    root = ET.parse(SITEMAP).getroot()

    listed = [
        e.text.strip()
        for e in root.iter()
        if e.tag.split("}")[-1] == "loc" and e.text
    ]

    errors = []
    warnings = []
    inbound = Counter()
    edge_count = 0

    if len(listed) != len(set(listed)):
        errors.append("Duplicate sitemap URLs")

    sitemap_routes = set()

    for url in listed:
        parsed = urlsplit(url)

        if (
            parsed.scheme != "https"
            or parsed.netloc != "leadsflo.co"
        ):
            errors.append("Incorrect sitemap host: " + url)
            continue

        route = parsed.path or "/"

        if not route.endswith("/"):
            errors.append("Noncanonical sitemap URL: " + url)

        sitemap_routes.add(route)

        if route not in pages:
            errors.append("Sitemap route missing build: " + route)

    for route, audit in pages.items():
        url = DOMAIN + route

        # Intentional legacy CRM redirect, not an indexable page.
        if route == "/crm-funnels-automation/":
            if audit.canonicals != [DOMAIN + "/crm-automation/"]:
                errors.append("Legacy CRM redirect canonical mismatch")
            if not any("noindex" in v for v in audit.robots):
                errors.append("Legacy CRM redirect missing noindex")
            if route in sitemap_routes:
                errors.append("Legacy CRM redirect in sitemap")
            if "/crm-automation/" not in pages:
                errors.append("Legacy CRM destination missing")
            continue

        if audit.canonicals != [url]:
            errors.append(
                f"Canonical mismatch: {route}: {audit.canonicals}"
            )

        if not audit.titles or not "".join(audit.titles).strip():
            warnings.append("Missing title: " + route)

        if len(audit.description) != 1:
            warnings.append(
                "Meta description count: " + route
            )

        if audit.h1_count != 1:
            warnings.append(
                f"H1 count {audit.h1_count}: {route}"
            )

        is_noindex = any(
            "noindex" in value for value in audit.robots
        )

        if is_noindex and route in sitemap_routes:
            errors.append(
                "Noindex page appears in sitemap: " + route
            )

        if not is_noindex and route not in sitemap_routes:
            warnings.append(
                "Indexable page missing sitemap: " + route
            )

        if route in sitemap_routes and any(
            "nofollow" in value for value in audit.robots
        ):
            warnings.append(
                "Sitemap page has nofollow: " + route
            )

        seen_links = set()

        for href in audit.links:
            resolved = resolve_path(href, route)

            if resolved is None:
                continue

            target_route, fragment = resolved
            target = built_target(target_route)

            if not target.is_file():
                errors.append(
                    "Broken link: " + route + " -> " + href
                )
                continue

            # Only HTML page links affect inbound page counts.
            if target_route in pages and target_route != route:
                if target_route not in seen_links:
                    inbound[target_route] += 1
                    edge_count += 1
                    seen_links.add(target_route)

            if fragment and target_route in pages:
                if fragment not in pages[target_route].ids:
                    warnings.append(
                        "Missing anchor: "
                        + route + " -> " + href
                    )

    orphaned = sorted(
        route for route in sitemap_routes
        if route != "/" and inbound[route] == 0
    )

    for route in orphaned:
        warnings.append(
            "No internal page links found: " + route
        )

    report = {
        "built_html_pages": len(pages),
        "sitemap_urls": len(listed),
        "unique_internal_page_edges": edge_count,
        "sitemap_pages_without_inbound_links": orphaned,
        "errors": errors,
        "warnings": warnings,
        "most_linked_pages": inbound.most_common(12),
    }

    print("\n=== SITEWIDE INTERNAL SEO AUDIT ===")
    print("Built HTML pages:", len(pages))
    print("Sitemap URLs:", len(listed))
    print("Unique internal page edges:", edge_count)
    print("Errors:", len(errors))
    print("Warnings:", len(warnings))
    print("Pages without inbound links:", len(orphaned))

    print("\n=== MOST LINKED PAGES ===")
    for route, count in inbound.most_common(12):
        print(f"  {count:3}  {route}")

    if errors:
        print("\n=== ERRORS ===")
        for item in errors[:40]:
            print("ERROR:", item)
        if len(errors) > 40:
            print(f"... {len(errors)-40} more")

    if warnings:
        print("\n=== WARNINGS ===")
        for item in warnings[:50]:
            print("WARN:", item)
        if len(warnings) > 50:
            print(f"... {len(warnings)-50} more")

    print("\n=== JSON SUMMARY ===")
    print(json.dumps({
        "built_html_pages": len(pages),
        "sitemap_urls": len(listed),
        "errors": len(errors),
        "warnings": len(warnings),
        "orphaned_pages": len(orphaned)
    }, indent=2))

    # Report SEO findings without silently rewriting
    # previously approved or legacy pages.
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
