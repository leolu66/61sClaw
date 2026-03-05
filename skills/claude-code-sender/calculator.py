"""
Calculator class with basic arithmetic operations
"""


class Calculator:
    """A simple calculator class supporting basic arithmetic operations."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        """Subtract second number from first."""
        return a - b

    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b

    def divide(self, a, b):
        """Divide first number by second. Raises ValueError if divisor is zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


# Example usage
if __name__ == "__main__":
    calc = Calculator()

    print("Calculator Tests:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"20 / 4 = {calc.divide(20, 4)}")
