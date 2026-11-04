import ast
import re


def extract_code(response: str) -> str:
    """Accept fences or prose around a module without discarding broken Python."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
    candidates = blocks
    if not candidates:
        imported = re.search(r"(?m)^from[ \t]+opentrons[ \t]+import[ \t]+protocol_api\b", response)
        if imported is None:
            raise ValueError("No Opentrons module was returned")
        module = response[imported.start() :]
        candidates = [module]
        # Only a clearly marked, unindented explanation can end an unfenced
        # module. Never salvage an arbitrary syntax error by dropping later steps.
        lines = module.splitlines()
        for index, line in enumerate(lines):
            if re.match(
                r"^(?:Explanation:|Notes?:|Summary:|This (?:protocol|script|code)\b)", line
            ):
                candidates.append("\n".join(lines[:index]))
                break
    for candidate in candidates:
        try:
            tree = ast.parse(candidate.strip())
        except SyntaxError:
            continue
        if any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in tree.body) and any(
            isinstance(n, ast.ImportFrom) and n.module == "opentrons" for n in tree.body
        ):
            return candidate.strip() + "\n"
    raise ValueError("No syntactically valid Opentrons run() protocol was returned")
