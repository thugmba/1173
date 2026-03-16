"""
Convert VIZ.qmd sections into individual Jupyter notebooks.
Output: Notebooks/Viz_S1.ipynb ... Viz_S16.ipynb  (16 sections total)
"""

import json
import re
import uuid
import os

QMD_PATH = "Lectures/VIZ.qmd"
OUT_DIR = "Notebooks"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- helpers --------------------------------------------------------

def make_id():
    return uuid.uuid4().hex[:8]

def notebook_skeleton(title: str, module: str) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0"
            },
            "title": title,
            "module": module
        },
        "cells": []
    }

def md_cell(text: str) -> dict:
    lines = text.splitlines(keepends=True)
    if not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return {
        "cell_type": "markdown",
        "id": make_id(),
        "metadata": {},
        "source": lines
    }

def code_cell(text: str) -> dict:
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return {
        "cell_type": "code",
        "id": make_id(),
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": lines
    }

# ---------- parse QMD into cells -------------------------------------------

def parse_section_to_cells(content: str) -> list:
    """
    Convert section text (markdown + python code blocks) into notebook cells.
    Adjacent markdown lines are batched into one markdown cell.
    Each ```python ... ``` block becomes a code cell.
    Other fenced blocks (```, no lang or non-python) stay as markdown.
    """
    cells = []
    lines = content.split("\n")
    i = 0
    md_buf = []

    def flush_md():
        text = "\n".join(md_buf).strip()
        if text:
            cells.append(md_cell(text))
        md_buf.clear()

    while i < len(lines):
        line = lines[i]

        # Detect fenced code block — handles both ```python and ```{python}
        m = re.match(r'^(`{3,}|~{3,})\{?(\w*)\}?', line)
        if m:
            fence = m.group(1)
            lang = m.group(2).lower()
            # collect until closing fence
            i += 1
            code_lines = []
            while i < len(lines):
                if lines[i].startswith(fence[0] * len(fence)):
                    i += 1  # skip closing fence
                    break
                # strip Quarto chunk options (#| echo: false, etc.)
                if not lines[i].startswith("#|"):
                    code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)

            if lang in ("python", "py"):
                flush_md()
                if code_text.strip():
                    cells.append(code_cell(code_text))
            else:
                # Keep non-python fenced blocks as markdown (with fences)
                if lang:
                    block = f"```{lang}\n{code_text}\n```"
                else:
                    block = f"```\n{code_text}\n```"
                md_buf.append(block)
        else:
            md_buf.append(line)
            i += 1

    flush_md()
    return cells

# ---------- split QMD into sections ----------------------------------------

def read_qmd(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()

def strip_yaml_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            return text[end + 5:]
    return text

# Module/section title patterns
MODULE_RE = re.compile(r'^# (Module \d+: .+)$', re.MULTILINE)
SECTION_RE = re.compile(r'^## (Section \d+: .+)$', re.MULTILINE)

def split_sections(text: str):
    """
    Returns list of dicts:
        { 'section_num': int, 'module': str, 'title': str, 'content': str }
    section_num is 1-based, sequential across all modules (1..16)
    """
    # Find all module and section markers with positions
    all_markers = []
    for m in MODULE_RE.finditer(text):
        all_markers.append(('module', m.start(), m.group(1)))
    for m in SECTION_RE.finditer(text):
        all_markers.append(('section', m.start(), m.group(1)))
    all_markers.sort(key=lambda x: x[1])

    sections = []
    current_module = ""
    seq = 1

    for idx, (kind, pos, title) in enumerate(all_markers):
        if kind == 'module':
            current_module = title
        else:  # section
            # content goes from this section header to next marker (or end)
            next_pos = all_markers[idx + 1][1] if idx + 1 < len(all_markers) else len(text)
            content = text[pos:next_pos].strip()
            sections.append({
                'section_num': seq,
                'module': current_module,
                'title': title,
                'content': content
            })
            seq += 1

    return sections

# ---------- main -----------------------------------------------------------

def main():
    raw = read_qmd(QMD_PATH)
    body = strip_yaml_front_matter(raw)
    sections = split_sections(body)

    print(f"Found {len(sections)} sections")

    for sec in sections:
        n = sec['section_num']
        nb_title = f"{sec['module']} — {sec['title']}"
        nb = notebook_skeleton(nb_title, sec['module'])

        # First cell: module title only (section title is in the second cell)
        header_md = f"# {sec['module']}"
        nb["cells"].append(md_cell(header_md))

        # Parse rest of section content
        cells = parse_section_to_cells(sec['content'])
        # Skip the first cell if it just repeats the section header
        nb["cells"].extend(cells)

        out_path = os.path.join(OUT_DIR, f"Viz_S{n}.ipynb")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

        code_count = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
        md_count = sum(1 for c in nb["cells"] if c["cell_type"] == "markdown")
        print(f"  Viz_S{n:02d}.ipynb  [{sec['module']} | {sec['title']}]  "
              f"md={md_count} code={code_count}")

    print("\nDone.")

if __name__ == "__main__":
    main()
