# txt_to_code.py ────────────────────────────────────────────────────────
"""
Gemini → OpenSCAD generation helpers.

UPDATED 2025-06-25:
• render_scad() now head-less-aware (xvfb-run).
• openscad_path is auto-detected; Windows hard-code no longer needed.
"""
from __future__ import annotations

import platform, shutil, subprocess
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

from config import MODEL_NAME, GOOGLE_API_VERSION  # noqa: F401 (version kept for future use)
from prompt import main_prompt, generic_prompt
from scad import SCADGuard

# ── SCAD generation loop (unchanged) ──────────────────────────────────
def text_to_scad(
    request: str,
    retries: int = 5,
    base_temperature: float = 0.0,
) -> str:
    guard = SCADGuard()
    convo = [
        SystemMessage(content=main_prompt()),
        HumanMessage(content=generic_prompt(request)),
    ]

    for attempt in range(1, retries + 1):
        temp = min(base_temperature + 0.1 * (attempt - 1), 1.0)
        llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=temp)
        code = str(llm.invoke(convo).content).strip()
        code = code.removeprefix("```").removesuffix("```").lstrip()
        if code.startswith("BLOCKED"):
            continue

        ok, msg = guard.clean(code)
        if not ok:
            convo.append(
                HumanMessage(content=f"RULE-VIOLATION: {msg}\nRegenerate.")
            )
            continue

        ok, err = guard.compile_ok(code)
        if ok:
            return code

        convo.append(HumanMessage(content=f"COMPILER-ERROR: {err}\nFix & resend."))

    raise RuntimeError("Failed to obtain valid OpenSCAD.")

# ── Helpers ───────────────────────────────────────────────────────────
def save_scad_code(code: str, outfile: Path | str) -> Path:
    p = Path(outfile).with_suffix(".scad")
    p.write_text(code, encoding="utf-8")
    return p


def render_scad(
    scad_path: Path,
    img_size: tuple[int, int] = (800, 600),
    openscad_path: str | None = None,
) -> Path:
    """
    Render *scad_path* to PNG under xvfb if necessary.
    Returns the PNG Path.
    """
    png = scad_path.with_suffix(".png")
    openscad_path = (
        openscad_path
        or shutil.which("openscad")
        or "openscad"  # fallback – will raise if truly missing
    )

    xvfb = shutil.which("xvfb-run") if platform.system() != "Windows" else None
    cmd = [
        openscad_path,
        "-o",
        str(png),
        "--imgsize",
        f"{img_size[0]},{img_size[1]}",
        str(scad_path),
    ]
    if xvfb:
        cmd = [
            xvfb,
            "--auto-servernum",
            "--server-args=-screen 0 1280x1024x24",
            *cmd,
        ]

    subprocess.run(cmd, check=True)
    return png
