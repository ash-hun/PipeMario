#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_DIR = REPO_ROOT / "notebooks"
DOCS_DIR = REPO_ROOT / "docs"
OUT_DIR = DOCS_DIR / "notebooks"
MINT_JSON = REPO_ROOT / "mint.json"

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

def load_mint_json():
    data = json.loads(MINT_JSON.read_text(encoding="utf-8"))
    return data

def save_mint_json(data):
    MINT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def ensure_nav_page(data, page_slug: str):
    """
    mint.json navigation에 'notebooks/<slug>' 페이지가 없으면 추가.
    "Notebooks" 그룹에 페이지를 추가합니다.
    """
    nav = data.get("navigation", [])

    # "Notebooks" 그룹 찾기
    notebooks_group = None
    for group in nav:
        if group.get("group") == "Notebooks":
            notebooks_group = group
            break

    # Notebooks 그룹이 없으면 생성
    if notebooks_group is None:
        notebooks_group = {"group": "Notebooks", "pages": []}
        nav.append(notebooks_group)

    # 페이지 추가
    pages = notebooks_group.setdefault("pages", [])
    if page_slug not in pages:
        pages.append(page_slug)

    data["navigation"] = nav
    return data

def main():
    if not NB_DIR.exists():
        print(f"Skip: {NB_DIR} not found")
        return

    data = load_mint_json()

    for nb in sorted(NB_DIR.glob("*.ipynb")):
        out = OUT_DIR / f"{nb.stem}.mdx"
        nb_to_mdx(nb, out)

        # Mintlify page slug: 프로젝트 루트 기준 상대경로(확장자 없이)
        slug = f"docs/notebooks/{nb.stem}"
        data = ensure_nav_page(data, slug)

    save_mint_json(data)
    print("Synced notebooks → docs")

if __name__ == "__main__":
    main()

