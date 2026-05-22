"""
Basic arithmetic operations.

This module provides simple arithmetic functions.
"""


def add(a: int | float, b: int | float) -> int | float:
    """
    Add two numbers.

    Args:
        a: The first number to add.
        b: The second number to add.

    Returns:
        The sum of a and b.

    Examples:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
        >>> add(2.5, 3.5)
        6.0
        >>> add(0, 0)
        0
    """
    return a + b


if __name__ == "__main__":
    # Demonstration
    print("Addition Examples:")
    print("-" * 30)
    print(f"add(2, 3) = {add(2, 3)}")
    print(f"add(-1, 1) = {add(-1, 1)}")
    print(f"add(2.5, 3.5) = {add(2.5, 3.5)}")
    print(f"add(0, 0) = {add(0, 0)}")
