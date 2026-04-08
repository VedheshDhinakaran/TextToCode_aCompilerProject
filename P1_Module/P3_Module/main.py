from .ast_builder import ASTBuilder
from .optimizer import ASTOptimizer


def run_ast_pipeline(ir):
    builder = ASTBuilder()
    program = builder.build(ir)

    optimizer = ASTOptimizer()
    program = optimizer.optimize(program)

    return program


# ✅ SAFE JSON CONVERTER
def ast_to_dict(node):
    if node is None:
        return None

    if hasattr(node, "body"):
        return {
            "type": "Program",
            "body": ast_to_dict(node.body)
        }

    if hasattr(node, "statements"):
        return {
            "type": "Block",
            "statements": [ast_to_dict(s) for s in node.statements]
        }

    if hasattr(node, "var"):
        return {
            "type": "Assignment",
            "var": node.var,
            "value": node.value
        }

    if hasattr(node, "value") and not hasattr(node, "var"):
        return {
            "type": "Print",
            "value": node.value
        }

    if hasattr(node, "condition"):
        return {
            "type": "IfElse",
            "condition": node.condition
        }

    return str(node)