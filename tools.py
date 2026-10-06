import os
import ast
import operator

from memory import load_memory, save_memory


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression: str):
    """Safely evaluate a mathematical expression."""

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):

        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError(
                "Only numbers are allowed."
            )

        if isinstance(node, ast.BinOp):

            operator_type = type(node.op)

            if operator_type not in _ALLOWED_OPERATORS:
                raise ValueError(
                    f"Operator {operator_type.__name__} "
                    "is not allowed."
                )

            left = evaluate(node.left)
            right = evaluate(node.right)

            if operator_type is ast.Pow and abs(right) > 100:
                raise ValueError(
                    "Exponent is too large."
                )

            return _ALLOWED_OPERATORS[operator_type](
                left,
                right,
            )

        if isinstance(node, ast.UnaryOp):

            operator_type = type(node.op)

            if operator_type not in _ALLOWED_OPERATORS:
                raise ValueError(
                    f"Operator {operator_type.__name__} "
                    "is not allowed."
                )

            operand = evaluate(node.operand)

            return _ALLOWED_OPERATORS[operator_type](
                operand
            )

        raise ValueError(
            "Only basic mathematical expressions "
            "are allowed."
        )

    return evaluate(tree.body)


def calculator(expression: str) -> str:
    """Safely calculate a mathematical expression."""

    try:

        result = safe_calculate(expression)

        return str(result)

    except ZeroDivisionError:

        return "Calculator error: Cannot divide by zero."

    except SyntaxError:

        return "Calculator error: Invalid mathematical expression."

    except Exception as e:

        return f"Calculator error: {e}"


def read_file(filename: str) -> str:
    """Read a text file from the workspace."""

    try:

        filename = os.path.basename(filename)

        workspace = os.path.abspath("workspace")

        path = os.path.abspath(
            os.path.join(
                workspace,
                filename,
            )
        )

        if not (
            path == workspace
            or path.startswith(workspace + os.sep)
        ):

            return "Error: Access outside workspace is not allowed."

        if not os.path.isfile(path):

            return f"File not found: {filename}"

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return file.read()

    except Exception as e:

        return f"Error reading file: {e}"


def write_file(filename: str, content: str) -> str:
    """
    Safely create or overwrite a text file
    inside the workspace.
    """

    try:

        filename = os.path.basename(filename)

        workspace = os.path.abspath("workspace")

        os.makedirs(
            workspace,
            exist_ok=True,
        )

        path = os.path.abspath(
            os.path.join(
                workspace,
                filename,
            )
        )

        if not path.startswith(
            workspace + os.sep
        ):

            return (
                "Error: Access outside "
                "workspace is not allowed."
            )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(content)

        return (
            f"File '{filename}' "
            "created successfully."
        )

    except Exception as e:

        return f"Error writing file: {e}"


def save_memory_tool(memory: str) -> str:
    """Save important information for future conversations."""

    try:

        if not memory.strip():

            return "Memory cannot be empty."

        existing_memory = load_memory()

        if existing_memory.strip():

            updated_memory = (
                existing_memory.rstrip()
                + "\n\n- "
                + memory.strip()
            )

        else:

            updated_memory = (
                "# Agent Memory\n\n"
                "- "
                + memory.strip()
            )

        save_memory(
            updated_memory
        )

        return "Memory saved successfully."

    except Exception as e:

        return f"Error saving memory: {e}"


def get_memory() -> str:
    """Retrieve persistent memory."""

    try:

        memory = load_memory()

        if not memory.strip():

            return "No memories have been saved yet."

        return memory

    except Exception as e:

        return f"Error loading memory: {e}"


tools_registry = {
    "calculator": calculator,
    "read_file": read_file,
    "write_file": write_file,
    "save_memory": save_memory_tool,
    "get_memory": get_memory,
}