# config.py  ───────────────────────────────────────────────────────────
import os, shutil

GOOGLE_API_KEY = "AIzaSyCwhz43NGdjhXROifeblISrDxas37ZZ47A"

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

MODEL_NAME   = "gemini-1.5-flash"         
GOOGLE_API_VERSION = "v1"                 
OPENSCAD_PATH = shutil.which("openscad") or "" 
