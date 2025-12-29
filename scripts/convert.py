#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_DIR = REPO_ROOT / "notebooks"
DOCS_DIR = REPO_ROOT / "docs"
OUT_DIR = DOCS_DIR / "notebooks"
DOCS_JSON = DOCS_DIR / "docs.json"

def nb_to_mdx(nb_path: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_md = out_path.with_suffix(".md")

    subprocess.check_call([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "markdown",
        "--output", tmp_md.name,
        str(nb_path),
        "--output-dir", str(tmp_md.parent),
    ])

    md = tmp_md.read_text(encoding="utf-8").replace("\r\n", "\n")

    title = nb_path.stem.replace("_", " ").strip()
    frontmatter = (
        f"---\n"
        f"title: \"{title}\"\n"
        f"description: \"Notebook: {title}\"\n"
        f"---\n\n"
    )

    out_path.write_text(frontmatter + md, encoding="utf-8")
    tmp_md.unlink(missing_ok=True)

def load_docs_json():
    data = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    return data

def save_docs_json(data):
    DOCS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def ensure_nav_page(data, page_slug: str):
    """
    docs.json navigation에 'notebooks/<slug>' 페이지가 없으면 추가.
    "Notebooks" 탭 아래 "Notebooks" 그룹에 페이지를 추가합니다.
    """
    nav = data.get("navigation", {})
    tabs = nav.get("tabs", [])

    # "Notebooks" 탭을 찾거나 생성
    notebooks_tab = None
    for t in tabs:
        if t.get("tab") == "Notebooks":
            notebooks_tab = t
            break
    if notebooks_tab is None:
        notebooks_tab = {"tab": "Notebooks", "groups": []}
        tabs.append(notebooks_tab)

    groups = notebooks_tab.setdefault("groups", [])

    # "Notebooks" 그룹 찾거나 생성
    nb_group = None
    for g in groups:
        if g.get("group") == "Notebooks":
            nb_group = g
            break
    if nb_group is None:
        nb_group = {"group": "Notebooks", "pages": []}
        groups.append(nb_group)

    pages = nb_group.setdefault("pages", [])
    if page_slug not in pages:
        pages.append(page_slug)

    nav["tabs"] = tabs
    data["navigation"] = nav
    return data

def main():
    if not NB_DIR.exists():
        print(f"Skip: {NB_DIR} not found")
        return

    data = load_docs_json()

    for nb in sorted(NB_DIR.glob("*.ipynb")):
        out = OUT_DIR / f"{nb.stem}.mdx"
        nb_to_mdx(nb, out)

        # Mintlify page slug: docs 폴더 기준 상대경로(확장자 없이)
        slug = f"notebooks/{nb.stem}"
        data = ensure_nav_page(data, slug)

    save_docs_json(data)
    print("Synced notebooks → docs")

if __name__ == "__main__":
    main()

