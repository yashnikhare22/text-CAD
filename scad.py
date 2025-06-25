# scad.py ───────────────────────────────────────────────────────────────
"""
Static hygiene + compile check for OpenSCAD code.

• Works with ALL known OpenSCAD versions (2019.05 → 2025.02.x)
• Falls back automatically if the legacy '--check' flag is gone
• Rich DEBUG logging for Streamlit Cloud
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

# ── xvfb wrapper for head-less Linux containers ────────────────────────
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

    # ── robust compile check (multi-strategy) ──────────────────────────
    def compile_ok(self, code: str) -> Tuple[bool, str]:
        if not self.openscad_path:
            return True, "(OpenSCAD CLI not installed – skipped)"

        with tempfile.NamedTemporaryFile(suffix=".scad", delete=False) as tmp:
            tmp.write(code.encode())
            path = tmp.name

        try:
            # 1️⃣ original flag (2019/2021 builds)
            ok, err = self._run(["--check", path])
            if ok or not self._ambiguous(err):
                return ok, err  # success OR real failure on old versions

            # 2️⃣ new flags (2025+ builds)
            ok, err = self._run(
                ["--check-parameters=true", "--check-parameter-ranges=true", path]
            )
            if ok or not self._unknown_option(err):
                return ok, err  # success OR something other than 'unknown option'

            # 3️⃣ last resort: syntax-only (-o - term) works on every build
            ok, err = self._run(["-o", "-", "--preview", path])
            return ok, err
        finally:
            Path(path).unlink(missing_ok=True)

    # ── helpers ────────────────────────────────────────────────────────
    def _run(self, extra_args: list[str]) -> Tuple[bool, str]:
        cmd = _wrap([self.openscad_path, *extra_args])
        log.debug("🔧 compile-check: %s", " ".join(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        log.debug("🔧 return-code %s", res.returncode)
        if res.stdout:
            log.debug("🔧 stdout ▶\n%s", res.stdout)
        if res.stderr:
            log.debug("🔧 stderr ▶\n%s", res.stderr)
        err_msg = "\n".join(res.stderr.strip().splitlines()[: self.max_lines])
        return res.returncode == 0, err_msg

    @staticmethod
    def _ambiguous(msg: str) -> bool:
        return "ambiguous" in msg and "--check" in msg

    @staticmethod
    def _unknown_option(msg: str) -> bool:
        return "unrecognised option" in msg or "unrecognized option" in msg
