import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass,field
from typing import Tuple

FENCE_RE=re.compile(r"```")
LINE_RE=re.compile(r"//.*?$",re.M)
BLOCK_RE=re.compile(r"/\*.*?\*/",re.S)
MOD_RE=re.compile(r"\bmodule\s+(\w+)\s*\(")
FUNC_RE   = re.compile(r"\bfunction\s+(\w+)\s*\(")

_STD = {
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
    openscad_path: str =field(default_factory=lambda:shutil.which('openscad') or "")
    max_lines = 40

    def clean( self,code):
        if FENCE_RE.search(code):
            return False, "Found markdown fence"
        elif BLOCK_RE.search(code) or LINE_RE.search(code):
            return False, "Found Comments"
        
        defined=set(MOD_RE.findall(code)) | set(FUNC_RE.findall(code))
        called= set(re.findall(r"\b(\w+)\s*\(",code))
        undefined=called - defined - _STD

        if undefined:
            return False, f"Undefined Helpers: {','.join(sorted(undefined))}"

        return True

    def compile(self,code):
        if not self.openscad_path:
            return True, "( OPENSCAD not installed)"
        with tempfile.NamedTemporaryFile(suffix=".scad",delete=False) as tmp:
            tmp.write(code.encode());path=tmp.name
        try:
            res=subprocess.run(
                [self.openscad_path,path], capture_output=True,text=True,timeout=10
            )

            err="\n".join(res.stderr.strip().splitlines()[:self.max_lines])
            return res.returncode==0,err
        finally:
            Path(path).unlink(missing_ok=True)



