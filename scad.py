# scad.py ───────────────────────────────────────────────────────────────
"""
Static hygiene + optional compile check for OpenSCAD code.

• Uses xvfb-run automatically in head-less Linux containers
• Emits rich DEBUG-level logs so you can see exactly what happens
"""

from __future__ import annotations

import logging
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from config import OPENSCAD_PATH

# ── Logging setup (inherits root level from ui.py) ─────────────────────
log = logging.getLogger(__name__)

# ── Head-less helper ───────────────────────────────────────────────────
XVFB_RUN = shutil.which("xvfb-run") if platform.system() != "Windows" else None


def _wrap(cmd: list[str]) -> list[str]:
    """Prefix *cmd* with xvfb-run if available (Linux head-less)."""
    if XVFB_RUN:
        return [
            XVFB_RUN,
            "--auto-servernum",
            "--server-args=-screen 0 1280x1024x24",
            *cmd,
        ]
    return cmd


# ── Regexes & built-ins (unchanged) ────────────────────────────────────
FENCE_RE = re.compile(r"```")
LINE_RE = re.compile(r"//.*?$", re.M)
BLOCK_RE = re.compile(r"/\*.*?\*/", re.S)
MOD_RE = re.compile(r"\bmodule\s+(\w+)\s*\(")
FUNC_RE = re.compile(r"\bfunction\s+(\w+)\s*\(")

_STD = {
    "if", "for", "difference", "union", "intersection",
    "translate", "rotate", "scale", "mirror",
    "linear_extrude", "rotate_extrude", "cylinder", "sphere", "cube",
    "circle", "square", "polygon", "polyhedron",
    "hull", "offset", "projection", "minkowski", "color", "text",
    "import", "render", "surface", "children",
    "sin", "cos", "tan", "asin", "acos", "atan", "sqrt", "pow", "abs",
    "floor", "ceil", "min", "max", "round", "exp", "log",
}


@dataclass
class SCADGuard:
    """Sanity-check and (optionally) compile OpenSCAD snippets."""

    openscad_path: str = field(default_factory=lambda: OPENSCAD_PATH)
    max_lines: int = 15

    # ── Static hygiene check ───────────────────────────────────────────
    def clean(self, code: str) -> Tuple[bool, str]:
        if FENCE_RE.search(code):
            return False, "markdown fence present"
        if BLOCK_RE.search(code) or LINE_RE.search(code):
            return False, "comments present"
        defined = set(MOD_RE.findall(code)) | set(FUNC_RE.findall(code))
        called = set(re.findall(r"\b(\w+)\s*\(", code))
        undef = called - defined - _STD
        if undef:
            return False, f"undefined helpers: {', '.join(sorted(undef))}"
        return True, ""

    # ── Optional compile check (xvfb-aware & verbose) ─────────────────
    def compile_ok(self, code: str) -> Tuple[bool, str]:
        if not self.openscad_path:
            return True, "(OpenSCAD CLI not installed – skipped)"

        with tempfile.NamedTemporaryFile(suffix=".scad", delete=False) as tmp:
            tmp.write(code.encode())
            path = tmp.name

        try:
            cmd = _wrap([self.openscad_path, "--check", path])
            log.debug("🔧 [SCADGuard] running: %s", " ".join(cmd))
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            log.debug("🔧 [SCADGuard] return-code: %s", res.returncode)
            log.debug("🔧 [SCADGuard] stdout ▶\n%s", res.stdout)
            log.debug("🔧 [SCADGuard] stderr ▶\n%s", res.stderr)

            err = "\n".join(res.stderr.strip().splitlines()[: self.max_lines])
            return res.returncode == 0, err
        finally:
            Path(path).unlink(missing_ok=True)
