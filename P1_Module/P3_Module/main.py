from .ast_builder import ASTBuilder
from .optimizer import ASTOptimizer


def run_ast_pipeline(ir):
    builder = ASTBuilder()
    program = builder.build(ir)

    optimizer = ASTOptimizer()
    program = optimizer.optimize(program)

    return program


# SAFE JSON CONVERTER
def ast_to_dict(node):
    if node is None:
        return None

    node_type = getattr(node, "type", None)

    if node_type == "program":
        return {
            "type": "Program",
            "body": ast_to_dict(node.body)
        }

    if node_type == "block":
        return {
            "type": "Block",
            "statements": [ast_to_dict(s) for s in node.statements]
        }

    if node_type == "assign":
        return {
            "type": "Assignment",
            "var": node.var,
            "value": node.value
        }

    if node_type == "print":
        return {
            "type": "Print",
            "value": node.value
        }

    if node_type == "if":
        return {
            "type": "IfElse",
            "condition": node.condition,
            "true_branch": [ast_to_dict(s) for s in node.true_branch],
            "false_branch": [ast_to_dict(s) for s in node.false_branch] if node.false_branch else []
        }

    if node_type == "while":
        return {
            "type": "WhileLoop",
            "condition": node.condition,
            "body": [ast_to_dict(s) for s in node.body]
        }

    if node_type == "for":
        return {
            "type": "ForLoop",
            "var": node.var,
            "start": node.start,
            "end": node.end,
            "body": [ast_to_dict(s) for s in node.body]
        }

    return str(node)
