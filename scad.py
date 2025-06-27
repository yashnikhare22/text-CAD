# scad.py — static hygiene + fast syntax check
from __future__ import annotations
import logging, platform, re, shutil, subprocess, tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from config import OPENSCAD_PATH

log = logging.getLogger(__name__)

# ── xvfb wrapper ───────────────────────────────────────────────────────
XVFB = shutil.which("xvfb-run") if platform.system() != "Windows" else None
def _wrap(cmd: list[str]) -> list[str]:
    return (
        [XVFB, "--auto-servernum", "--server-args=-screen 0 1280x1024x24", *cmd]
        if XVFB else cmd
    )

# ── regexes & std names ────────────────────────────────────────────────
FENCE_RE  = re.compile(r"```")
LINE_RE   = re.compile(r"//.*?$", re.M)
BLOCK_RE  = re.compile(r"/\*.*?\*/", re.S)
MOD_RE    = re.compile(r"\bmodule\s+(\w+)\s*\(")
FUNC_RE   = re.compile(r"\bfunction\s+(\w+)\s*\(")

_STD = {
    "if","for","difference","union","intersection","translate","rotate","scale",
    "mirror","linear_extrude","rotate_extrude","cylinder","sphere","cube",
    "circle","square","polygon","polyhedron","hull","offset","projection",
    "minkowski","color","text","import","render","surface","children",
    "sin","cos","tan","asin","acos","atan","sqrt","pow","abs","floor","ceil",
    "min","max","round","exp","log",
}

# ── guard class ────────────────────────────────────────────────────────
@dataclass
class SCADGuard:
    openscad_path: str = field(default_factory=lambda: OPENSCAD_PATH)
    max_lines: int = 15

    # hygiene check
    def clean(self, code: str) -> Tuple[bool, str]:
        if FENCE_RE.search(code):
            return False, "markdown fence present"
        if BLOCK_RE.search(code) or LINE_RE.search(code):
            return False, "comments present"

        defined = set(MOD_RE.findall(code)) | set(FUNC_RE.findall(code))
        called = {
            m.group(1)
            for m in re.finditer(r"\b(\w+)\s*\(", code)
            if m.group(1) != "function"     # ignore keyword itself
        }
        undef = called - defined - _STD
        if undef:
            return False, f"undefined helpers: {', '.join(sorted(undef))}"
        return True, ""

    # compile check
    def compile_ok(self, code: str) -> Tuple[bool, str]:
        if not self.openscad_path:
            return True, "(OpenSCAD CLI not installed – skipped)"

        code = re.sub(r'//Parameter\(""\)\s*', "", code)  # strip harmless artefacts

        with tempfile.NamedTemporaryFile(suffix=".scad", delete=False) as tmp:
            tmp.write(code.encode())
            path = tmp.name

        try:
            ok, err = self._run(["-o", "-", "--export-format", "ast", path], 10)
            if ok:
                return True, ""
            if not self._flag_unknown(err):
                return False, err

            ok, err = self._run(
                ["--check-parameters=true", "--check-parameter-ranges=true", path],
                120,
            )
            return ok, err
        finally:
            Path(path).unlink(missing_ok=True)

    # helper to run openscad
    def _run(self, extra: list[str], timeout: int) -> Tuple[bool, str]:
        cmd = _wrap([self.openscad_path, *extra])
        log.debug("🔧 compile-check: %s", " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, f"OpenSCAD timed out after {timeout}s"

        err = "\n".join(res.stderr.strip().splitlines()[: self.max_lines])
        return res.returncode == 0, err

    @staticmethod
    def _flag_unknown(msg: str) -> bool:
        msg = msg.lower()
        return (
            "unknown option" in msg
            or "unrecognised option" in msg
            or "unrecognized option" in msg
            or "export-format" in msg
        )
