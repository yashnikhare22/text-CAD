# txt_to_code.py
import subprocess
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

from config import MODEL_NAME, GOOGLE_API_VERSION
from prompt import main_prompt, generic_prompt
from scad import SCADGuard


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
        temp  = min(base_temperature + 0.1 * (attempt - 1), 1.0)

        llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=temp,
        )

        code = str(llm.invoke(convo).content).strip()

        ok, msg = guard.clean(code)
        if not ok:
            convo.append(HumanMessage(content=f"RULE-VIOLATION: {msg}\nRegenerate."))
            continue

        ok, err = guard.compile_ok(code)
        if ok:
            return code

        convo.append(HumanMessage(content=f"COMPILER-ERROR: {err}\nFix & resend."))

    raise RuntimeError("Failed to obtain valid OpenSCAD.")

# ---------- helpers ---------------------------------------------------
def save_scad_code(code: str, outfile: Path | str) -> Path:
    p = Path(outfile).with_suffix(".scad")
    p.write_text(code, encoding="utf-8")
    return p


def render_scad(
    scad_path: Path,
    img_size: tuple[int, int] = (800, 600),
    openscad_path: str = "openscad",
) -> Path:
    png = scad_path.with_suffix(".png")
    subprocess.run(
        [openscad_path, "-o", str(png), "--imgsize",
         f"{img_size[0]},{img_size[1]}", str(scad_path)],
        check=True,
    )
    return png
