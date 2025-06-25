# config.py  ───────────────────────────────────────────────────────────
import os, shutil

GOOGLE_API_KEY = "AIzaSyDXZ1U6xV_fGfiG4RSDVPmcJzlcVmUc-Yo"

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# --- Runtime constants -----------------------------------------------
MODEL_NAME   = "gemini-1.5-flash"         # fast + inexpensive
GOOGLE_API_VERSION = "v1"                 # avoid v1beta 404
OPENSCAD_PATH = shutil.which("openscad") or ""  # empty ⇒ skip compile
