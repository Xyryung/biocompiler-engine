import ast
import re


def extract_code(response: str) -> str:
    """Accept Python fences, or a bare module with a prose preamble."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
    candidates = blocks or [response[response.find("from opentrons import protocol_api") :]]
    for candidate in candidates:
        try:
            tree = ast.parse(candidate.strip())
        except SyntaxError:
            continue
        if any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in tree.body):
            return candidate.strip() + "\n"
    raise ValueError("No syntactically valid Opentrons run() protocol was returned")
