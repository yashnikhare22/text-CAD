# scad.py
import re, subprocess, tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple
from config import OPENSCAD_PATH

FENCE_RE = re.compile(r"```")
LINE_RE  = re.compile(r"//.*?$", re.M)
BLOCK_RE = re.compile(r"/\*.*?\*/", re.S)
MOD_RE   = re.compile(r"\bmodule\s+(\w+)\s*\(")
FUNC_RE  = re.compile(r"\bfunction\s+(\w+)\s*\(")

_STD = {  # built-ins
    "if","for","difference","union","intersection",
    "translate","rotate","scale","mirror",
    "linear_extrude","rotate_extrude","cylinder","sphere","cube",
    "circle","square","polygon","polyhedron",
    "hull","offset","projection","minkowski","color","text",
    "import","render","surface","children",
    "sin","cos","tan","asin","acos","atan","sqrt","pow","abs",
    "floor","ceil","min","max","round","exp","log",
}


@dataclass
class SCADGuard:
    openscad_path: str = field(default_factory=lambda: OPENSCAD_PATH)
    max_lines: int = 15

    # static hygiene ---------------------------------------------------
    def clean(self, code: str) -> Tuple[bool, str]:
        if FENCE_RE.search(code):           return False, "markdown fence"
        if BLOCK_RE.search(code) or LINE_RE.search(code):
                                              return False, "comments present"
        defined   = set(MOD_RE.findall(code)) | set(FUNC_RE.findall(code))
        called    = set(re.findall(r"\b(\w+)\s*\(", code))
        undef     = called - defined - _STD
        if undef: return False, f"undefined helpers: {', '.join(sorted(undef))}"
        return True, ""

    # optional compile check ------------------------------------------
    def compile_ok(self, code: str) -> Tuple[bool, str]:
        if not self.openscad_path:
            return True, "(OpenSCAD CLI not installed – skipped)"
        with tempfile.NamedTemporaryFile(suffix=".scad", delete=False) as tmp:
            tmp.write(code.encode()); path = tmp.name
        try:
            res = subprocess.run(
                [self.openscad_path, "--check", path],
                capture_output=True, text=True, timeout=30
            )
            err = "\n".join(res.stderr.strip().splitlines()[: self.max_lines])
            return res.returncode == 0, err
        finally:
            Path(path).unlink(missing_ok=True)
