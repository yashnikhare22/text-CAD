import subprocess
from langchain.schema import SystemMessage,HumanMessage
from prompt import main_prompt,generic_prompt
from scad import SCADGuard
from pathlib import Path

def text_to_scad (llm,request,retries=5):
    guard=SCADGuard()

    convo=[
        SystemMessage(content=main_prompt()),
        HumanMessage(content=generic_prompt(request))
    ]

    for attempt in range(1,retries+1):
        temp=0.0+0.01*(attempt -1 )
        top_p=0.05+0.05*(attempt -1)
        code=llm.invoke(convo,temperature=temp,top_p=top_p).content.strip()
        result = guard.clean(code)
        if isinstance(result, tuple):
            ok, msg = result
        else:
            ok, msg = result, ""

        if not ok:
            convo.append(HumanMessage(content=f"RULE VIOLATION\n{msg}"))
            continue
        ok,err=guard.compile(code)
        if ok:
            return code
        convo.append(HumanMessage(content=f"COMPLIER-ERROR\n{err}"))

    raise RuntimeError('Failed to obtain valid OPENSCAD after several attempts')


def save_scad_code(code,filename):
    p=Path(filename).with_suffix('.scad')
    p.write_text(code,encoding='utf-8')
    return p
  
    
    
def render_scad(scad_path: Path, img_size=(800,600),openscad_path='openscad'):
    if not scad_path.exists():
        raise FileNotFoundError(scad_path)

    png_path=scad_path.with_suffix('.png')

    cmd=[
        openscad_path, "-o",str(png_path),'--imgsize',f"{img_size[0]},{img_size[1]}",str(scad_path)
    ]

    subprocess.run(cmd,check=True)
    return png_path

