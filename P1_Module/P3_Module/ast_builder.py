from .ast_nodes import *

def normalize_expr(expr):
    return (expr.replace("plus", "+")
                .replace("minus", "-")
                .replace("into", "*")
                .replace("by", "/")
                .replace(" mod ", " % "))

class ASTBuilder:

    def build(self, ir):
        self.nodes = ir.get("nodes", [])
        self.i = 0
        self.node_id_to_stmt = {}  # Track which IR node IDs map to which statements
        return Program(Block(self.parse_block(is_root=True)))

    def should_end_block(self, node, base_indent, parent_line, is_root):
        if is_root:
            return False

        t = node.get("type", "").lower()
        if t in ["else", "end"]:
            return True

        indent = node.get("indent", 0)
        line = node.get("line", -1)
        return line > parent_line and indent <= base_indent

    def parse_block(self, base_indent=0, parent_line=-1, is_root=False):
        stmts = []
        do_context = None  # Track do-while body start in stmts array

        while self.i < len(self.nodes):
            node = self.nodes[self.i]

            if self.should_end_block(node, base_indent, parent_line, is_root):
                return stmts

            # 🔥 SAFE TYPE HANDLING
            t = node.get("type", "").lower()

            # =====================
            # ASSIGNMENT
            # =====================
            if t == "process":
                code = node["code"]
                if "=" in code:
                    var, val = code.split("=")
                    stmt = Assignment(var.strip(), normalize_expr(val.strip()))
                    stmts.append(stmt)
                    self.node_id_to_stmt[node["id"]] = stmt

            # =====================
            # PRINT
            # =====================
            elif t == "output":
                val = node["code"].replace("print(", "").replace(")", "")
                stmt = Print(normalize_expr(val))
                stmts.append(stmt)
                self.node_id_to_stmt[node["id"]] = stmt

            # =====================
            # IF
            # =====================
            elif t == "decision":
                condition = normalize_expr(node["condition"])
                header_indent = node.get("indent", base_indent)
                header_line = node.get("line", parent_line)
                self.i += 1

                true_branch = self.parse_block(base_indent=header_indent, parent_line=header_line)

                false_branch = []
                if self.i < len(self.nodes) and self.nodes[self.i].get("type") == "else":
                    else_node = self.nodes[self.i]
                    else_indent = else_node.get("indent", header_indent)
                    else_line = else_node.get("line", header_line)
                    self.i += 1
                    false_branch = self.parse_block(base_indent=else_indent, parent_line=else_line)

                stmts.append(IfElse(condition, true_branch, false_branch))
                self.node_id_to_stmt[node["id"]] = stmts[-1]
                continue

            # =====================
            # ELSE → STOP
            # =====================
            elif t == "else":
                return stmts

            # =====================
            # WHILE / DO-WHILE
            # =====================
            elif t == "loop":
                condition = normalize_expr(node["condition"])
                
                # Check if this is a do-while loop
                if node.get("is_do_while"):
                    # For do-while: extract body statements by IR node IDs
                    first_stmt_ir_id = node.get("do_first_stmt_id")
                    last_stmt_ir_id = node.get("do_last_stmt_id")
                    
                    if first_stmt_ir_id is not None and last_stmt_ir_id is not None:
                        # Find statements that correspond to IR node IDs in the body range
                        body = []
                        stmts_to_remove = set()
                        
                        for ir_node_id, stmt in self.node_id_to_stmt.items():
                            if first_stmt_ir_id <= ir_node_id <= last_stmt_ir_id:
                                body.append(stmt)
                                stmts_to_remove.add(id(stmt))
                        
                        # Remove body statements from stmts (by object identity)
                        stmts = [stmt for stmt in stmts if id(stmt) not in stmts_to_remove]
                    else:
                        # Fallback: use all stmts as body
                        body = stmts
                        stmts = []
                    
                    stmts.append(DoWhileLoop(condition, body))
                    self.node_id_to_stmt[node["id"]] = stmts[-1]
                    self.i += 1
                    continue
                else:
                    # For regular while: parse body after condition node
                    header_indent = node.get("indent", base_indent)
                    header_line = node.get("line", parent_line)
                    self.i += 1

                    body = self.parse_block(base_indent=header_indent, parent_line=header_line)
                    stmt = WhileLoop(condition, body)
                    stmts.append(stmt)
                    self.node_id_to_stmt[node["id"]] = stmt
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

                header_indent = node.get("indent", base_indent)
                header_line = node.get("line", parent_line)
                self.i += 1
                body = self.parse_block(base_indent=header_indent, parent_line=header_line)

                stmt = ForLoop(var, start, end, body)
                stmts.append(stmt)
                self.node_id_to_stmt[node["id"]] = stmt
                continue

            # =====================
            # LOOP END
            # =====================
            elif t == "loop_end":
                self.i += 1
                # Only return from nested blocks, not from root
                if not is_root:
                    return stmts
                continue

            # =====================
            # END
            # =====================
            elif t == "end":
                self.i += 1
                if is_root:
                    continue
                return stmts

            # =====================
            # END IF
            # =====================
            elif t == "end_if":
                self.i += 1
                if is_root:
                    continue
                return stmts

            self.i += 1

        return stmts

    def parse_statement(self):
        if self.i >= len(self.nodes):
            return None

        node = self.nodes[self.i]
        t = node.get("type", "").lower()

        if t == "process":
            code = node["code"]
            self.i += 1
            if "=" in code:
                var, val = code.split("=")
                return Assignment(var.strip(), normalize_expr(val.strip()))
            return None

        if t == "output":
            code = node["code"]
            self.i += 1
            val = code.replace("print(", "").replace(")", "")
            return Print(normalize_expr(val))

        if t == "decision":
            condition = normalize_expr(node["condition"])
            self.i += 1
            true_branch = self.parse_block()

            false_branch = []
            if self.i < len(self.nodes) and self.nodes[self.i].get("type") == "else":
                self.i += 1
                if self.i < len(self.nodes):
                    next_type = self.nodes[self.i].get("type", "").lower()
                    if next_type in ["decision", "loop", "for"]:
                        false_branch = self.parse_block()
                    else:
                        stmt = self.parse_statement()
                        if stmt is not None:
                            false_branch.append(stmt)

            return IfElse(condition, true_branch, false_branch)

        if t == "loop":
            condition = normalize_expr(node["condition"])
            self.i += 1
            body = self.parse_block()
            return WhileLoop(condition, body)

        if t == "for":
            var = node.get("var")
            start = node.get("start")
            end = node.get("end")
            self.i += 1
            body = self.parse_block()
            return ForLoop(var, start, end, body)

        if t in ["loop_end", "end", "else"]:
            return None

        self.i += 1
        return None