class Program:
    def __init__(self, body):
        self.type = "program"
        self.body = body


class Block:
    def __init__(self, statements):
        self.type = "block"
        self.statements = statements


class Assignment:
    def __init__(self, var, value):
        self.type = "assign"
        self.var = var
        self.value = value


class Print:
    def __init__(self, value):
        self.type = "print"
        self.value = value


class IfElse:
    def __init__(self, condition, true_branch, false_branch):
        self.type = "if"
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch


class WhileLoop:
    def __init__(self, condition, body):
        self.type = "while"
        self.condition = condition
        self.body = body


# OPTIONAL (for future)
class ForLoop:
    def __init__(self, var, start, end, body):
        self.type = "for"
        self.var = var
        self.start = start
        self.end = end
        self.body = body