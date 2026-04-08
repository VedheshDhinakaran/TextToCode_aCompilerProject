class PythonGenerator:

    def generate(self, node, indent=0):
        space = "    " * indent

        if node is None:
            return ""

        # PROGRAM
        if node.type == "program":
            return self.generate(node.body, indent)

        # BLOCK
        if node.type == "block":
            code = ""
            for stmt in node.statements:
                code += self.generate(stmt, indent)
            return code

        # ASSIGN
        if node.type == "assign":
            return f"{space}{node.var} = {node.value}\n"

        # PRINT
        if node.type == "print":
            return f"{space}print({node.value})\n"

        # IF ELSE
        if node.type == "if":
            code = f"{space}if {node.condition}:\n"

            if node.true_branch:
                for stmt in node.true_branch:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    pass\n"

            if node.false_branch:
                code += f"{space}else:\n"
                for stmt in node.false_branch:
                    code += self.generate(stmt, indent + 1)

            return code

        # WHILE LOOP (FIXED)
        if node.type == "while":
            code = f"{space}while {node.condition}:\n"

            if node.body:
                for stmt in node.body:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    pass\n"

            return code

        # FOR LOOP (NEW)
        if node.type == "for":
            code = f"{space}for {node.var} in range({node.start}, {node.end}):\n"

            if node.body:
                for stmt in node.body:
                    code += self.generate(stmt, indent + 1)
            else:
                code += f"{space}    pass\n"

            return code

        return ""