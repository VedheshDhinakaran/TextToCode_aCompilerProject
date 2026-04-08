class JavaGenerator:

    def generate(self, node, indent=0):
        space = "    " * indent

        if node is None:
            return ""

        # =========================
        # PROGRAM ROOT
        # =========================
        if node.type == "program":
            code = "public class Main {\n"
            code += "    public static void main(String[] args) {\n"
            code += self.generate(node.body, 2)
            code += "    }\n}"
            return code

        # =========================
        # BLOCK
        # =========================
        if node.type == "block":
            code = ""
            for stmt in node.statements:
                code += self.generate(stmt, indent)
            return code

        # =========================
        # ASSIGNMENT
        # =========================
        if node.type == "assign":
            return f"{space}int {node.var} = {node.value};\n"

        # =========================
        # PRINT
        # =========================
        if node.type == "print":
            return f"{space}System.out.println({node.value});\n"

        # =========================
        # IF ELSE (FIXED)
        # =========================
        if node.type == "if":
            code = f"{space}if ({node.condition}) {{\n"

            if node.true_branch:
                for stmt in node.true_branch:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    // empty\n"

            code += f"{space}}}"

            if node.false_branch:
                code += " else {\n"
                for stmt in node.false_branch:
                    code += self.generate(stmt, indent + 1)
                code += f"{space}}}"

            code += "\n"
            return code

        # =========================
        # WHILE LOOP (FIXED)
        # =========================
        if node.type == "while":
            code = f"{space}while ({node.condition}) {{\n"

            if node.body:
                for stmt in node.body:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    // empty\n"

            code += f"{space}}}\n"
            return code

        # =========================
        # FOR LOOP (OPTIONAL)
        # =========================
        if node.type == "for":
            code = f"{space}for (int {node.var} = {node.start}; {node.var} < {node.end}; {node.var}++) {{\n"

            if node.body:
                for stmt in node.body:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    // empty\n"

            code += f"{space}}}\n"
            return code

        return ""