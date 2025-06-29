# ui.py ─────────────────────────────────────────────────────────────
# Streamlit front-end: natural-language prompt ➜ OpenSCAD code ➜ PNG preview
#
# Prerequisites already handled elsewhere:
#   • txt_to_code.text_to_scad() generates valid OpenSCAD text.
#   • save_scad_code() writes a .scad file.
#   • render_scad() renders the .png via OpenSCAD + xvfb.
# -------------------------------------------------------------------
from pathlib import Path
import tempfile

import streamlit as st

from txt_to_code import text_to_scad, save_scad_code, render_scad

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Text → OpenSCAD",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️  Natural-language → OpenSCAD CAD generator")

# ── Prompt box ─────────────────────────────────────────────────────
request = st.text_area(
    "Describe the part you need",
    placeholder="e.g. Spur gear: module 1 mm, 20 teeth, 5 mm thickness, 4 mm bore",
    height=120,
)

generate = st.button("Generate CAD", disabled=not request.strip())

if generate:
    with st.spinner("Calling Gemini, cleaning code and compiling…"):
        try:
            scad_code = text_to_scad(request.strip())
        except Exception as err:
            st.error(f"🚨 Generation failed:\n\n{err}")
            st.stop()

    # ── Show generated code ─────────────────────────────────────────
    st.subheader("Generated OpenSCAD")
    st.code(scad_code, language="openscad")

    # ── Render preview image ───────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp_dir:
        scad_path = Path(tmp_dir) / "model.scad"
        save_scad_code(scad_code, scad_path)
        try:
            png_path = render_scad(scad_path)
            st.subheader("Preview")
            st.image(str(png_path))
        except Exception as err:
            st.warning(f"Could not render preview:\n\n{err}")

# ── Footer ─────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Powered by Google Gemini 1.5-flash · LangChain · OpenSCAD 2021.01 · Streamlit"
)
