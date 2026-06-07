# Pure Python Calculator - No MCP, No Model

import questionary

def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a+b

def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        return "Error: Cannot divide by zero."
    return a / b


if __name__ == "__main__":
    num1 = float(input("First number: "))
    num2 = float(input("Second number: "))

    operation = questionary.select(
        "Choose an operation:",
        choices=[
            "add",
            "subtract",
            "multiply",
            "divide",
        ],
    ).ask()

    operations = {
        "add": add,
        "subtract": subtract,
        "multiply": multiply,
        "divide": divide,
    }

    result = operations[operation](num1, num2)

    print(f"\nResult: {result}")



    '''
    print("Enter two numbers: ")
    num1 = float(input("First number: "))
    num2 = float(input("Second number: "))
    function = input("Choose an operation (add, subtract, multiply, divide): ").strip().lower()
    if function == "add":
        result = add(num1, num2)
    elif function == "subtract":
        result = subtract(num1, num2)
    elif function == "multiply":
        result = multiply(num1, num2)
    elif function == "divide":
        result = divide(num1, num2)
    else:
        result = "Invalid operation selected."
    print(f"Result: {result}")
    '''