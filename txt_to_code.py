# txt_to_code.py
# ---------------------------------------------------------------------
import subprocess, os
from pathlib import Path
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

from prompt import main_prompt, generic_prompt
from scad import SCADGuard

# Ensure key is in env (ui.py already sets it)
assert "GOOGLE_API_KEY" in os.environ, "GOOGLE_API_KEY not set!"

def text_to_scad(
    request: str,
    base_temperature: float = 0.0,
    retries: int = 5,
) -> str:
    """Return compilable OpenSCAD code or raise after `retries` attempts."""
    guard = SCADGuard()
    convo = [
        SystemMessage(content=main_prompt()),
        HumanMessage(content=generic_prompt(request)),
    ]

    for attempt in range(1, retries + 1):
        temp  = min(base_temperature + 0.05 * (attempt - 1), 1.0)
        top_p = 0.05 + 0.05 * (attempt - 1)

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",          # fast & inexpensive
            temperature=temp,
            top_p=top_p,
        )

        code = str(llm.invoke(convo).content).strip()

        result = guard.clean(code)
        if isinstance(result, tuple):
            ok, msg = result
        else:
            ok, msg = result, ""

        if not ok:
            convo.append(HumanMessage(content=f"RULE-VIOLATION\n{msg}\nRegenerate."))
            continue

        ok, err = guard.compile(code)
        if ok:
            return code
        convo.append(HumanMessage(content=f"COMPILER-ERROR\n{err}\nFix and resend."))

    raise RuntimeError("Failed to obtain valid OpenSCAD after several attempts.")

# ---------- I/O helpers ----------------------------------------------
def save_scad_code(code: str, filename: Path | str) -> Path:
    p = Path(filename).with_suffix(".scad")
    p.write_text(code, encoding="utf-8")
    return p

def render_scad(
    scad_path: Path,
    img_size: tuple[int, int] = (800, 600),
    openscad_path: str = "openscad",
) -> Path:
    if not scad_path.exists():
        raise FileNotFoundError(scad_path)
    png_path = scad_path.with_suffix(".png")
    subprocess.run(
        [
            openscad_path,
            "-o", str(png_path),
            "--imgsize", f"{img_size[0]},{img_size[1]}",
            str(scad_path),
        ],
        check=True,
    )
    return png_path
