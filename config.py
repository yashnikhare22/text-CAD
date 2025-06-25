# config.py  ───────────────────────────────────────────────────────────
import os, shutil

# --- Gemini key (⚠️ keep private in real projects) --------------------
GOOGLE_API_KEY = "AIzaSyCSTCvRgxbjzET4CS9e92sPkd21ooWdspQ"

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# --- Runtime constants -----------------------------------------------
MODEL_NAME   = "gemini-1.5-flash"         # fast + inexpensive
GOOGLE_API_VERSION = "v1"                 # avoid v1beta 404
OPENSCAD_PATH = shutil.which("openscad") or ""  # empty ⇒ skip compile
