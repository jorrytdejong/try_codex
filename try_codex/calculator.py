"""
Calculator engine: parse expressions and use operations.
"""
from operations import add, subtract, multiply, divide

def calculate(expression: str) -> float:
    """Calculate a simple expression 'a op b'."""
    parts = expression.strip().split()
    if len(parts) != 3:
        raise ValueError("Expression must be: <number> <operator> <number>")

    a_str, op, b_str = parts
    try:
        a = float(a_str)
        b = float(b_str)
    except ValueError:
        raise ValueError(f"Invalid numbers: {a_str}, {b_str}")

    if op == '+':
        return add(a, b)
    if op == '-':
        return subtract(a, b)
    if op == '*':
        return multiply(a, b)
    if op == '/':
        return divide(a, b)

    raise ValueError(f"Unsupported operator: {op}")
