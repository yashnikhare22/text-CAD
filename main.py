from langchain_openai import ChatOpenAI
from txt_to_code import text_to_scad,render_scad,save_scad_code
import os

llm='gpt-4o-mini'
openai_api_key='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'
os.environ["OPENAI_API_KEY"] = openai_api_key
llm_model = ChatOpenAI(model=llm, temperature=0)

question='Create gear with 60 teeth, module 2.5 mm, and thickness 10 mm.'

scad_code = text_to_scad(llm_model,question)
scad_file=save_scad_code(scad_code, 'gear')

# print(scad_code)

pg_file = render_scad(scad_file, openscad_path=r"C:\Program Files\OpenSCAD\openscad.exe")


