
def main_prompt():
    return (
        '''You are an expert in Openscad code generator
        Response with **Plain**, compatible and accurate OPENSCAD code with **No** Markdown fences.
        No coments and always declare every variable and **helper function** before it is used to make accurate code syntax.
        Expose each dimension passed ( or assumed)  as a top level variable so the model stays fuly parametric.
        **Never use an OPENSCAD reserved keywords for varaible name**  ( module) -- Use alternate words
        Do not hard code numeric contants inside geometry and if request is impossible, reply with single word: "ERROR" 
        '''
    )


def generic_prompt(request: str) -> str:
    return (
        "TASK\nCreate an OpenSCAD model that fulfils the entire user story below.\n\n"
        "RULES\n"
        "  • Output *plain* OpenSCAD code – no comments, no markdown fences.\n"
        "  • Declare every variable and helper function before first use.\n"
        "  • Surface **all** user-specified attributes *and* every constant or\n"
        "    standard multiplier (e.g. `dedendum_factor = 1.25`) as named\n"
        "    variables so *nothing* is hard-coded.\n"
        "  • Use only CSG primitives available in OpenSCAD ≥ 2021.01.\n"
        "  • Use the constant `PI` (uppercase).  Do not embed degree→rad\n"
        "    literals like 57.2958; provide your own deg2rad() helper if needed.\n"
        "  • For **gears**: generate discrete teeth, cut the root circle, keep\n"
        "    all cylinders centred, and expose addendum, dedendum,\n"
        "    clearance, and `$fn` as variables.\n"
        "    always use module_mm varaible name in entire code.\n"
        "\nUSER STORY\n  " + request.strip() + "\n\n"
        "DELIVERABLE\nReturn **only** the complete, compilable OpenSCAD source.\n"
    )