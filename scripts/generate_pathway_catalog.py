#!/usr/bin/env python3
"""Generate pathway catalog artifacts from README.md."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
CATALOG_DIR = REPO_ROOT / "catalog"
CATALOG_INDEX = CATALOG_DIR / "README.md"
OUTPUT_JSON = REPO_ROOT / "pathways.json"

SECTION_PATTERN = re.compile(
    r"\*\*(Introduction[^*]+?)\*\*\n(?P<body>(?:\s+\+.*\n)+)",
    re.MULTILINE,
)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https://github.com/[^)]+)\)")


def slugify(value: str) -> str:
    """Create filesystem-friendly slug."""
    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return cleaned or "pathway"


def extract_pathways(readme_text: str) -> list[dict[str, object]]:
    pathways: list[dict[str, object]] = []
    for heading, body in SECTION_PATTERN.findall(readme_text):
        modules = []
        for line in body.splitlines():
            match = LINK_PATTERN.search(line)
            if not match:
                continue
            title, url = match.groups()
            modules.append({"title": title.strip(), "url": url.strip()})
        if modules:
            pathways.append({"name": heading.strip(), "modules": modules})
    return pathways


def build_catalog(pathways: list[dict[str, object]]) -> None:
    CATALOG_DIR.mkdir(exist_ok=True)
    catalog_lines = ["# Learning Pathway Catalog", ""]
    for pathway in pathways:
        name = str(pathway["name"])
        modules = list(pathway["modules"])
        slug = slugify(name)
        pathway_dir = CATALOG_DIR / slug
        pathway_dir.mkdir(parents=True, exist_ok=True)
        pathway_md = pathway_dir / "README.md"
        pathway_lines = [f"# {name}", ""]
        for module in modules:
            title = module["title"]
            url = module["url"]
            pathway_lines.append(f"- [{title}]({url})")
        pathway_lines.append("")
        pathway_md.write_text("\n".join(pathway_lines) + "\n", encoding="utf-8")
        catalog_lines.append(f"## [{name}](./{slug}/README.md)")
        catalog_lines.append("")
        for module in modules:
            catalog_lines.append(f"- [{module['title']}]({module['url']})")
        catalog_lines.append("")
    CATALOG_INDEX.write_text("\n".join(catalog_lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    pathways = extract_pathways(text)
    if not pathways:
        raise SystemExit("No pathways found in README.md")
    OUTPUT_JSON.write_text(json.dumps(pathways, indent=2) + "\n", encoding="utf-8")
    build_catalog(pathways)


if __name__ == "__main__":
    main()
