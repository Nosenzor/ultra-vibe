"""
Fibonacci number calculation functions.

This module provides several implementations for calculating Fibonacci numbers.
"""

from functools import lru_cache
from typing import Union


def fibonacci_iterative(n: int) -> int:
    """
    Calculate the nth Fibonacci number using an iterative approach.

    The Fibonacci sequence is defined as:
    - F(0) = 0
    - F(1) = 1
    - F(n) = F(n-1) + F(n-2) for n > 1

    Args:
        n: A non-negative integer representing the position in the Fibonacci sequence.

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.

    Examples:
        >>> fibonacci_iterative(0)
        0
        >>> fibonacci_iterative(1)
        1
        >>> fibonacci_iterative(10)
        55
        >>> fibonacci_iterative(20)
        6765
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


@lru_cache(maxsize=None)
def fibonacci_recursive(n: int) -> int:
    """
    Calculate the nth Fibonacci number using a memoized recursive approach.

    This implementation uses LRU caching to avoid redundant calculations,
    making it efficient for repeated calls with the same or smaller values.

    Args:
        n: A non-negative integer representing the position in the Fibonacci sequence.

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.

    Examples:
        >>> fibonacci_recursive(0)
        0
        >>> fibonacci_recursive(1)
        1
        >>> fibonacci_recursive(10)
        55
        >>> fibonacci_recursive(20)
        6765
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci(n: int, method: str = "iterative") -> int:
    """
    Calculate the nth Fibonacci number.

    This is the main entry point that selects the implementation method.

    Args:
        n: A non-negative integer representing the position in the Fibonacci sequence.
        method: The calculation method to use. Options are:
            - "iterative": Fast, O(n) time, O(1) space (default)
            - "recursive": Memoized recursive, efficient for repeated calls

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is negative or method is invalid.

    Examples:
        >>> fibonacci(10)
        55
        >>> fibonacci(20, method="iterative")
        6765
        >>> fibonacci(20, method="recursive")
        6765
    """
    methods = {
        "iterative": fibonacci_iterative,
        "recursive": fibonacci_recursive,
    }

    if method not in methods:
        raise ValueError(f"Invalid method: {method}. Choose from {list(methods.keys())}")

    return methods[method](n)


def fibonacci_sequence(n: int) -> list[int]:
    """
    Generate the first n Fibonacci numbers.

    Args:
        n: A non-negative integer representing how many Fibonacci numbers to generate.

    Returns:
        A list containing the first n Fibonacci numbers.

    Raises:
        ValueError: If n is negative.

    Examples:
        >>> fibonacci_sequence(10)
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        >>> fibonacci_sequence(5)
        [0, 1, 1, 2, 3]
    """
    if n < 0:
        raise ValueError("Cannot generate a negative number of Fibonacci numbers")
    if n == 0:
        return []
    if n == 1:
        return [0]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i - 1] + sequence[i - 2])
    return sequence


if __name__ == "__main__":
    # Demonstration
    print("Fibonacci Numbers:")
    print("-" * 50)

    # Single values
    for i in range(15):
        print(f"F({i}) = {fibonacci(i)}")

    print("\nFirst 15 Fibonacci numbers:")
    print(fibonacci_sequence(15))

    # Performance comparison
    import time

    n = 35
    print(f"\nPerformance comparison for F({n}):")

    start = time.time()
    result_iter = fibonacci(n, method="iterative")
    time_iter = time.time() - start
    print(f"Iterative: {result_iter} in {time_iter:.6f} seconds")

    # Clear cache for fair comparison
    fibonacci_recursive.cache_clear()
    start = time.time()
    result_rec = fibonacci(n, method="recursive")
    time_rec = time.time() - start
    print(f"Recursive (memoized): {result_rec} in {time_rec:.6f} seconds")

    # Now with cache warm
    start = time.time()
    result_rec_cached = fibonacci(n, method="recursive")
    time_rec_cached = time.time() - start
    print(f"Recursive (cached): {result_rec_cached} in {time_rec_cached:.6f} seconds")
