# scad.py ───────────────────────────────────────────────────────────────
"""
Static hygiene + version-agnostic compile check for OpenSCAD code.

Strategy order (fast ➜ slow):
1. `-o - --preview`  (syntax-only, < 2 s, works 2019.05 → 2025.02)
2. `--check-parameters=true --check-parameter-ranges=true`
   (new 2025 builds;  raise timeout to 120 s)
If all fail we return the *last* error to the caller.

Works on head-less Linux via xvfb-run and on local Windows/Mac desktops.
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

log = logging.getLogger(__name__)

# ── xvfb wrapper for Streamlit Cloud / HF Spaces ───────────────────────
XVFB = shutil.which("xvfb-run") if platform.system() != "Windows" else None


def _wrap(cmd: list[str]) -> list[str]:
    return (
        [XVFB, "--auto-servernum", "--server-args=-screen 0 1280x1024x24", *cmd]
        if XVFB
        else cmd
    )


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
    openscad_path: str = field(default_factory=lambda: OPENSCAD_PATH)
    max_lines: int = 15

    # ───────────────────────────────────────────────────────────────────
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

    # ── robust compile check ───────────────────────────────────────────
    def compile_ok(self, code: str) -> Tuple[bool, str]:
        if not self.openscad_path:
            return True, "(OpenSCAD CLI not installed – skipped)"

        with tempfile.NamedTemporaryFile(suffix=".scad", delete=False) as tmp:
            tmp.write(code.encode())
            path = tmp.name

        try:
            # 1️⃣ ultra-fast syntax check (always available)
            ok, err = self._run(["-o", "-", "--preview", path], timeout=25)
            if ok:
                return True, ""
            # only continue if *syntax* is OK but flags unknown
            if not self._only_preview_allowed(err):
                return False, err

            # 2️⃣ new 2025 flags (could be slow → 120 s timeout)
            ok, err = self._run(
                ["--check-parameters=true", "--check-parameter-ranges=true", path],
                timeout=120,
            )
            return ok, err
        finally:
            Path(path).unlink(missing_ok=True)

    # ── helpers ────────────────────────────────────────────────────────
    def _run(self, extra: list[str], timeout: int) -> Tuple[bool, str]:
        cmd = _wrap([self.openscad_path, *extra])
        log.debug("🔧 compile-check: %s", " ".join(cmd))
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            err_msg = "\n".join(res.stderr.strip().splitlines()[: self.max_lines])
            if res.stdout:
                log.debug("🔧 stdout ▶\n%s", res.stdout)
            if res.stderr:
                log.debug("🔧 stderr ▶\n%s", res.stderr)
            return res.returncode == 0, err_msg
        except subprocess.TimeoutExpired:
            log.debug("⏳ OpenSCAD timed out after %s s", timeout)
            return False, f"OpenSCAD timed out after {timeout} s"

    @staticmethod
    def _only_preview_allowed(msg: str) -> bool:
        """
        Detect messages that mean the flags were unknown but the file parsed.
        If other fatal errors appear we should surface them immediately.
        """
        lowered = msg.lower()
        return (
            "unknown option" in lowered
            or "unrecognised option" in lowered
            or "unrecognized option" in lowered
            or "ambiguous" in lowered
        )
