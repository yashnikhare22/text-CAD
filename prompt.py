# prompt.py
def main_prompt() -> str:
    return (
        "You are an expert in Openscad code generator\n"
        "Respond with **plain**, compatible and accurate OPENSCAD code — "
        "**no** Markdown fences, **no** comments.\n"
        "Expose every dimension passed (or assumed) as a top-level variable so "
        "the model stays fully parametric.\n"
        "Always declare every variable *and* helper function before it is used, "
        "and never use an OpenSCAD reserved keyword (e.g. `module`) as a "
        "variable name.\n"
        "If the request is impossible, reply with the single word: ERROR\n"
    )


def generic_prompt(request: str) -> str:
    return (
        "TASK\nCreate an OpenSCAD model that fulfils the entire user story below.\n"
        "RULES\n"
        "  • Output *plain* OpenSCAD code – no comments, no markdown fences.\n"
        "  • Declare **every** variable, helper function and module *before* the "
        "first reference.  Order matters.\n"
        "  • Surface all user-specified attributes **and** every constant or "
        "standard multiplier (e.g. `dedendum_factor = 1.25`) as named "
        "variables so *nothing* is hard-coded.\n"
        "  • Use only CSG primitives available in OpenSCAD ≥ 2021.01.\n"
        "  • Use the constant `PI` for π.  Provide a `deg2rad()` helper if "
        "angular conversion is needed (do **not** embed 57.2958 literals).\n"
        "  • For **gears**: generate discrete teeth, cut the root circle, keep "
        "all cylinders centred, and expose `addendum`, `dedendum`, "
        "`clearance`, `module_mm`, and `$fn` as variables.\n"
        "USER STORY\n"
        f"  {request.strip()}\n\n"
        "DELIVERABLE\nReturn **only** the complete, compilable OpenSCAD source."
    )
