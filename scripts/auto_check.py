# AI-assisted (Claude Code, claude.ai) — https://claude.ai
"""Auto-mark REQUIREMENTS_CHECKLIST.md items verifiable from committed artifacts.

Run by CI on every push to main. Commits a change back if any items were
newly satisfied. No item is ever un-marked.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHECKLIST = ROOT / "REQUIREMENTS_CHECKLIST.md"
README = ROOT / "README.md"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
NB_PICK = ROOT / "notebooks" / "challenge3-pickandplace.ipynb"
NB_REACH = ROOT / "notebooks" / "challenge3-reach-experimentation.ipynb"


def notebook_source(path: Path) -> str:
    """Return all code cell source from a notebook as a single string."""
    if not path.exists():
        return ""
    nb = json.loads(path.read_text())
    return "\n".join(
        "".join(cell["source"])
        for cell in nb["cells"]
        if cell["cell_type"] == "code"
    )


def notebook_markdown(path: Path) -> str:
    """Return all markdown cell source from a notebook as a single string."""
    if not path.exists():
        return ""
    nb = json.loads(path.read_text())
    return "\n".join(
        "".join(cell["source"])
        for cell in nb["cells"]
        if cell["cell_type"] == "markdown"
    )


def repo_is_public() -> bool:
    try:
        url = "https://api.github.com/repos/aipi590-ggn/aipi590-challenge-3"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        return not data.get("private", True)
    except Exception:
        return False


def evaluate() -> dict[str, bool]:
    """Return {item_id: should_be_checked} for all auto-markable items."""
    readme = README.read_text() if README.exists() else ""
    nb_pick_code = notebook_source(NB_PICK)
    nb_reach_code = notebook_source(NB_REACH)
    nb_pick_md = notebook_markdown(NB_PICK)
    nb_reach_md = notebook_markdown(NB_REACH)
    all_nb_code = nb_pick_code + nb_reach_code
    all_nb_md = nb_pick_md + nb_reach_md

    has_videos = list((RESULTS / "videos").glob("*.mp4")) if (RESULTS / "videos").exists() else []
    has_gifs = list((RESULTS / "videos").glob("*.gif")) if (RESULTS / "videos").exists() else []

    return {
        # EMB — Physical or Simulated Embodiment
        "EMB1": "mujoco" in all_nb_code.lower() or "gymnasium_robotics" in all_nb_code,

        # TASK — Embodied Task
        "TASK1": "FetchPickAndPlace" in all_nb_code or "FetchReach" in all_nb_code,
        "TASK2": bool(has_videos) or bool(has_gifs),

        # SIM — Sim-to-Real Transfer Discussion
        "SIM1": "sim" in readme.lower() and "real" in readme.lower(),
        "SIM2": sum(1 for g in ["action", "reward", "state", "observation"]
                    if g in readme.lower()) >= 3,
        "SIM3": "domain randomization" in readme.lower() or "randomization" in all_nb_md.lower(),

        # GEN — General
        "GEN1": True,  # any technique is allowed
        "GEN3": repo_is_public(),
    }


def mark_item(text: str, item_id: str) -> tuple[str, bool]:
    """Change '- [ ] **ITEM_ID**' to '- [x] **ITEM_ID**'. Returns (text, changed)."""
    pattern = rf"(- )\[ \]( \*\*{re.escape(item_id)}\*\*)"
    new_text = re.sub(pattern, r"\1[x]\2", text)
    return new_text, new_text != text


def strikethrough_checked(text: str) -> str:
    """Add ~~strikethrough~~ to the description of checked items."""
    def strike_line(m: re.Match) -> str:
        prefix, item_id, desc = m.group(1), m.group(2), m.group(3)
        if desc.startswith("~~"):
            return m.group(0)  # already struck
        return f"{prefix}{item_id} ~~{desc.strip()}~~"

    return re.sub(
        r"(- \[x\] )(\*\*\w+\*\*) — (.+)$",
        strike_line,
        text,
        flags=re.MULTILINE,
    )


def main() -> None:
    text = CHECKLIST.read_text()
    conditions = evaluate()
    newly_marked = []

    for item_id, satisfied in conditions.items():
        if satisfied:
            text, changed = mark_item(text, item_id)
            if changed:
                newly_marked.append(item_id)

    text = strikethrough_checked(text)

    if text != CHECKLIST.read_text():
        CHECKLIST.write_text(text)
        if newly_marked:
            print(f"Auto-marked: {', '.join(newly_marked)}")
        else:
            print("Strikethrough updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
