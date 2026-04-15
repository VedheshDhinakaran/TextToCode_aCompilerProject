class ASTOptimizer:

    def constant_folding(self, program):
        values = {}

        for stmt in program.body.statements:
            if hasattr(stmt, "var") and hasattr(stmt, "value"):
                try:
                    val = int(stmt.value)
                    values[stmt.var] = val
                except:
                    if stmt.value in values:
                        stmt.value = str(values[stmt.value])

            if hasattr(stmt, "value"):
                if stmt.value in values:
                    stmt.value = str(values[stmt.value])

        return program

    def dead_code_elimination(self, program):
        # simple version: remove empty nodes
        program.body.statements = [
            stmt for stmt in program.body.statements if stmt is not None
        ]
        return program

    def optimize(self, program):
        program = self.constant_folding(program)
        program = self.dead_code_elimination(program)
        return program