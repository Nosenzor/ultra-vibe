"""
Simple addition function.

A Python function to add two numbers.
"""


def add(a: int | float, b: int | float) -> int | float:
    """
    Add two numbers and return their sum.
    
    Args:
        a: First number (int or float)
        b: Second number (int or float)
        
    Returns:
        The sum of a and b as int or float
        
    Examples:
        >>> add(2, 3)
        5
        >>> add(2.5, 3.5)
        6.0
        >>> add(-1, 1)
        0
    """
    return a + b


if __name__ == "__main__":
    # Quick test
    print(f"add(2, 3) = {add(2, 3)}")
    print(f"add(2.5, 3.5) = {add(2.5, 3.5)}")
    print(f"add(-1, 1) = {add(-1, 1)}")
