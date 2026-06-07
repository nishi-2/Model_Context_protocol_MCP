# Creating MCP server - which is where functions are registered and called by the model

from fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("Calculator Server")

# Expose the calculator functions as tools using the @mcp.tool decorator
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a+b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide the first number by the second. Returns an error string if dividing by zero."""
    if b == 0:
        return "Error: Cannot divide by zero."
    return a / b


if __name__ == "__main__":
    print("Starting MCP Server...")
    mcp.run()