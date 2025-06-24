# ui.py  ────────────────────────────────────────────────────────────────
# Streamlit app: Natural-language prompt ➜ OpenSCAD code ➜ PNG preview
#
# Key security:
#   • First tries st.secrets["OPENAI_API_KEY"]      (Streamlit Cloud)
#   • Falls back to env var  OPENAI_API_KEY         (local runs / CI)
#   • Abort with an error if neither is set.
#
# ----------------------------------------------------------------------
import os, uuid, tempfile
from pathlib import Path

import streamlit as st
from PIL import Image
from langchain_openai import ChatOpenAI

from txt_to_code import text_to_scad, save_scad_code, render_scad  # your helper module

# ── CONFIG (safe to keep in repo) ─────────────────────────────────────
OPENSCAD_EXE = r"C:\Program Files\OpenSCAD\openscad.exe"   # adjust for Linux/Mac
MODEL_NAME   = "gpt-4o-mini"
# ---------------------------------------------------------------------

# ── Securely obtain key ──────────────────────────────────────────────
api_key = (
    st.secrets.get("OPENAI_API_KEY") or    # Streamlit Cloud
    os.getenv("OPENAI_API_KEY")            # local / GitHub Actions / .env
)
if not api_key:
    st.error(
        "OPENAI_API_KEY not found.\n"
        "• Add it in Streamlit Cloud:  Settings → Secrets  (preferred)\n"
        "• Or set an environment variable locally:  export OPENAI_API_KEY='sk-…'"
    )
    st.stop()

# Expose the key so LangChain/OpenAI SDK can read it automatically
os.environ["OPENAI_API_KEY"] = api_key

# ── Sidebar controls ─────────────────────────────────────────────────
st.sidebar.title("Generation settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.05)

# ── UI main pane ─────────────────────────────────────────────────────
st.title("🖼️  Text → OpenSCAD → PNG")

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
    st.info("Generating OpenSCAD code…")
    llm_model = ChatOpenAI(model=MODEL_NAME, temperature=temperature)
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
        st.error("OpenSCAD CLI not found.  Check OPENSCAD_EXE path in ui.py.")
        st.stop()
    except Exception as e:
        st.error(f"Render failed:\n{e}")
        st.stop()

    # 4 ─ Show results & downloads ------------------------------------
    st.subheader("OpenSCAD source")
    st.code(scad_code, language="scad")

    st.subheader("Preview")
    st.image(Image.open(png_path), use_container_width=True)

    st.download_button("Download .scad", scad_path.read_bytes(), file_name="model.scad")
    st.download_button("Download .png",  png_path.read_bytes(),  file_name="preview.png")

    st.success("Done!  Share the link or these files with anyone.")
