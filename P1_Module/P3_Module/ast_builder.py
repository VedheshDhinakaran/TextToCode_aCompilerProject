from .ast_nodes import *

def normalize_expr(expr):
    return (expr.replace("plus", "+")
                .replace("minus", "-")
                .replace("into", "*")
                .replace("by", "/"))

class ASTBuilder:

    def build(self, ir):
        self.nodes = ir.get("nodes", [])
        self.i = 0
        return Program(Block(self.parse_block()))

    def parse_block(self):
        stmts = []

        while self.i < len(self.nodes):
            node = self.nodes[self.i]

            # 🔥 SAFE TYPE HANDLING
            t = node.get("type", "").lower()

            # =====================
            # ASSIGNMENT
            # =====================
            if t == "process":
                code = node["code"]
                if "=" in code:
                    var, val = code.split("=")
                    stmts.append(Assignment(var.strip(), normalize_expr(val.strip())))

            # =====================
            # PRINT
            # =====================
            elif t == "output":
                val = node["code"].replace("print(", "").replace(")", "")
                stmts.append(Print(normalize_expr(val)))

            # =====================
            # IF
            # =====================
            elif t == "decision":
                condition = normalize_expr(node["condition"])
                self.i += 1

                true_branch = self.parse_block()

                false_branch = []
                if self.i < len(self.nodes) and self.nodes[self.i].get("type") == "else":
                    self.i += 1
                    false_branch = self.parse_block()

                stmts.append(IfElse(condition, true_branch, false_branch))
                continue

            # =====================
            # ELSE → STOP
            # =====================
            elif t == "else":
                return stmts

            # =====================
            # WHILE
            # =====================
            elif t == "loop":
                condition = normalize_expr(node["condition"])
                self.i += 1

                body = self.parse_block()

                stmts.append(WhileLoop(condition, body))
                continue

            # =====================
            # 🚀 FOR LOOP (FINAL FIX)
            # =====================
            elif t == "for":
                var = node.get("var")
                start = node.get("start")
                end = node.get("end")

                # 🚨 SAFETY CHECK
                if var is None or start is None or end is None:
                    print("ERROR: Invalid FOR node:", node)
                    self.i += 1
                    continue

                self.i += 1
                body = self.parse_block()

                stmts.append(ForLoop(var, start, end, body))
                continue

            # =====================
            # LOOP END
            # =====================
            elif t == "loop_end":
                return stmts

            # =====================
            # END
            # =====================
            elif t == "end":
                return stmts

            self.i += 1

        return stmts