"""Accept only the straight-line Opentrons DSL used by this demo.

This is a restriction on generated code, not a general-purpose Python sandbox.
Modal adds process, filesystem and network isolation when selected.
"""

import ast

METHODS = {
    "load_labware",
    "load_instrument",
    "pick_up_tip",
    "drop_tip",
    "transfer",
    "distribute",
    "consolidate",
    "mix",
    "delay",
    "comment",
}
NODES = (
    ast.Module,
    ast.ImportFrom,
    ast.alias,
    ast.Assign,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.Dict,
    ast.List,
    ast.Tuple,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Expr,
    ast.Call,
    ast.Attribute,
    ast.Subscript,
    ast.keyword,
    ast.Pass,
)


def validate_protocol(code: str) -> None:
    if len(code) > 100_000:
        raise ValueError("Protocol exceeds 100 KB")
    tree = ast.parse(code)
    imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    if len(imports) != 1 or imports[0].module != "opentrons" or imports[0].level:
        raise ValueError("Only the opentrons protocol_api import is allowed")
    if [(a.name, a.asname) for a in imports[0].names] != [("protocol_api", None)]:
        raise ValueError("Only protocol_api may be imported")
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if len(functions) != 1 or functions[0].name != "run" or functions[0].decorator_list:
        raise ValueError("Exactly one undecorated run function is required")
    function = functions[0]
    if (
        [a.arg for a in function.args.args] != ["protocol"]
        or function.args.defaults
        or function.args.kw_defaults
        or function.args.kwarg
        or function.args.vararg
        or function.args.posonlyargs
        or function.args.kwonlyargs
        or function.returns
    ):
        raise ValueError("run must take exactly one protocol argument")
    known = {"protocol", "protocol_api", "metadata"}
    for node in ast.walk(tree):
        if not isinstance(node, NODES):
            raise ValueError(f"Unsupported Python construct: {type(node).__name__}")
        if isinstance(node, ast.Attribute) and node.attr not in METHODS | {"ProtocolContext"}:
            raise ValueError(f"Unsupported attribute: {node.attr}")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Attribute) or node.func.attr not in METHODS
        ):
            raise ValueError("Only documented Opentrons method calls are allowed")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError("Private names are forbidden")
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                raise ValueError("Only simple variable assignments are allowed")
            target = node.targets[0].id
            if target in known and target != "metadata":
                raise ValueError("Cannot reassign a protected name")
            known.add(target)
    # No calls at module scope; metadata must be a literal dictionary.
    metadata = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            assert isinstance(node.targets[0], ast.Name)
            if node.targets[0].id != "metadata":
                raise ValueError("Only metadata may be assigned at module scope")
            metadata = ast.literal_eval(node.value)
        elif not isinstance(node, ast.ImportFrom | ast.FunctionDef):
            raise ValueError("Unexpected top-level statement")
    if not isinstance(metadata, dict) or metadata.get("apiLevel") != "2.19":
        raise ValueError("metadata must specify apiLevel 2.19")
    # Bind every method to its expected receiver type; prevent aliasing or calls
    # through arbitrary expressions. Values can only be literals or well refs.
    bindings = {"protocol": "context"}

    def value(expr: ast.AST) -> None:
        if isinstance(expr, ast.Constant):
            if not isinstance(expr.value, str | int | float | type(None)):
                raise ValueError("Unsupported literal")
        elif isinstance(expr, ast.Name) and expr.id in bindings:
            return
        elif isinstance(expr, ast.List | ast.Tuple):
            for elt in expr.elts:
                value(elt)
        elif (
            isinstance(expr, ast.Subscript)
            and isinstance(expr.value, ast.Name)
            and bindings.get(expr.value.id) == "labware"
            and isinstance(expr.slice, ast.Constant)
            and isinstance(expr.slice.value, str)
        ):
            return
        else:
            raise ValueError("Unsupported method argument")

    for stmt in function.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Assign | ast.Expr):
            call = stmt.value
        else:
            raise ValueError("Only straight-line Opentrons calls are allowed")
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            raise ValueError("Expected an Opentrons call")
        receiver = call.func.value
        if not isinstance(receiver, ast.Name) or receiver.id not in bindings:
            raise ValueError("Unknown method receiver")
        method = call.func.attr
        allowed = (
            {"load_labware", "load_instrument", "delay", "comment"}
            if bindings[receiver.id] == "context"
            else METHODS - {"load_labware", "load_instrument", "delay", "comment"}
            if bindings[receiver.id] == "pipette"
            else set()
        )
        if method not in allowed:
            raise ValueError("Method is not allowed on this receiver")
        for arg in call.args:
            value(arg)
        for kw in call.keywords:
            if kw.arg is None:
                raise ValueError("Keyword unpacking is forbidden")
            value(kw.value)
        if isinstance(stmt, ast.Assign):
            if method not in {"load_labware", "load_instrument"}:
                raise ValueError("Only labware and instrument calls may be assigned")
            assert isinstance(stmt.targets[0], ast.Name)
            target = stmt.targets[0].id
            if target in bindings or target in {"metadata", "protocol_api"}:
                raise ValueError("Variables cannot be rebound")
            bindings[target] = "labware" if method == "load_labware" else "pipette"
