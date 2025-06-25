# ui.py ────────────────────────────────────────────────────────────────
"""
Streamlit front-end (Text ➜ OpenSCAD ➜ PNG) with root DEBUG logging.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import streamlit as st
from PIL import Image

# ── Global logging (everything DEBUG to Streamlit logs) ───────────────
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ── Secrets & environment ─────────────────────────────────────────────
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

from txt_to_code import text_to_scad, save_scad_code, render_scad  # noqa: E402

# Auto-detect OpenSCAD; env var wins, then PATH, then Windows fallback
OPENSCAD_EXE = (
    os.getenv("OPENSCAD_PATH")
    or shutil.which("openscad")
    or r"C:\Program Files\OpenSCAD\openscad.exe"
)

log.debug("🔍 OPENSCAD_EXE = %s", OPENSCAD_EXE)

# ── UI layout ─────────────────────────────────────────────────────────
st.title("🖼️  Text → OpenSCAD → PNG  (Gemini)")

prompt = st.text_area(
    "Describe your CAD part",
    placeholder="e.g. Create a spur gear with 60 teeth, module 2 mm, thickness 8 mm",
    height=140,
)

if st.button("Generate"):
    if not prompt.strip():
        st.error("Please enter a description first.")
        st.stop()

    # 1 ─ Generate SCAD -------------------------------------------------
    st.info("Generating OpenSCAD code with Gemini …")
    try:
        scad_code = text_to_scad(prompt)
    except Exception as e:
        st.error(f"LLM generation failed:\n{e}")
        log.exception("LLM generation failed")
        st.stop()

    # 2 ─ Save .scad ----------------------------------------------------
    tmp_dir = Path(tempfile.gettempdir()) / f"cad_{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir(exist_ok=True)
    scad_path = save_scad_code(scad_code, tmp_dir / "model")
    log.debug("💾 SCAD saved to %s", scad_path)

    # 3 ─ Render → PNG --------------------------------------------------
    st.info("Rendering with OpenSCAD CLI …")
    try:
        png_path = render_scad(scad_path, openscad_path=OPENSCAD_EXE)
    except FileNotFoundError:
        st.error("OpenSCAD CLI not found. Check OPENSCAD_EXE in ui.py.")
        log.exception("OpenSCAD binary not found")
        st.stop()
    except Exception as e:
        st.error(f"Render failed:\n{e}")
        log.exception("Render failed")
        st.stop()

    # 4 ─ Display & download -------------------------------------------
    st.subheader("OpenSCAD source")
    st.code(scad_code, language="scad")

    st.subheader("Preview")
    st.image(Image.open(png_path), use_container_width=True)

    st.download_button("Download .scad", scad_path.read_bytes(), file_name="model.scad")
    st.download_button("Download .png", png_path.read_bytes(), file_name="preview.png")

    st.success("Done ✔︎ Share the files or link with anyone.")
