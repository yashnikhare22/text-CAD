# ui.py
# ---------------------------------------------------------------------
# Streamlit app: natural-language prompt → OpenSCAD code → PNG preview
# ---------------------------------------------------------------------
import os, uuid, tempfile
from pathlib import Path

import streamlit as st
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI

from txt_to_code import text_to_scad, save_scad_code, render_scad

# ---------- CONSTANTS -------------------------------------------------
OPENSCAD_EXE = r"C:\Program Files\OpenSCAD\openscad.exe"  # adjust for Linux/Mac
MODEL_NAME   = "gemini-pro"                               # or gemini-1.5-pro, etc.

# ---------- HARD-CODED GEMINI KEY  (❗ replace with your real key) -----
GOOGLE_API_KEY = "AIzaSyCU7SL8v8PddBNKIs3Yhoua35uzjgt7gRE"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ---------- Sidebar controls -----------------------------------------
st.sidebar.title("Generation settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.05)

# ---------- Main UI ---------------------------------------------------
st.title("🖼️  Text → OpenSCAD → PNG (Gemini edition)")

prompt = st.text_area(
    "Describe your CAD part",
    placeholder="e.g. Create a spur gear with 60 teeth, module 2 mm, thickness 8 mm",
    height=140,
)

if st.button("Generate"):
    if not prompt.strip():
        st.error("Please enter a description first.")
        st.stop()

    # 1 ─ LLM call -----------------------------------------------------
    st.info("Generating OpenSCAD code with Gemini…")
    llm_model = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=temperature)
    try:
        scad_code = text_to_scad(llm_model, prompt)
    except Exception as e:
        st.error(f"LLM generation failed:\n{e}")
        st.stop()

    # 2 ─ Save .scad ---------------------------------------------------
    tmp_dir   = Path(tempfile.gettempdir()) / f"cad_{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir(exist_ok=True)
    scad_path = save_scad_code(scad_code, tmp_dir / "model")

    # 3 ─ Render → PNG -------------------------------------------------
    st.info("Rendering with OpenSCAD CLI…")
    try:
        png_path = render_scad(scad_path, openscad_path=OPENSCAD_EXE)
    except FileNotFoundError:
        st.error("OpenSCAD CLI not found. Check OPENSCAD_EXE path in ui.py.")
        st.stop()
    except Exception as e:
        st.error(f"Render failed:\n{e}")
        st.stop()

    # 4 ─ Show + download ---------------------------------------------
    st.subheader("OpenSCAD source")
    st.code(scad_code, language="scad")

    st.subheader("Preview")
    st.image(Image.open(png_path), use_container_width=True)

    st.download_button("Download .scad", scad_path.read_bytes(), file_name="model.scad")
    st.download_button("Download .png",  png_path.read_bytes(),  file_name="preview.png")

    st.success("Done!  Share the link or these files with anyone.")
