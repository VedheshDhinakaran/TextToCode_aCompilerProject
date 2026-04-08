from .python_generator import PythonGenerator
from .java_generator import JavaGenerator


def generate_code(ast, language):

    if language == "java":
        generator = JavaGenerator()
        return generator.generate(ast)

    # default python
    generator = PythonGenerator()
    return generator.generate(ast)