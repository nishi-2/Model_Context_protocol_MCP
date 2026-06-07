# MCP Client code to call the MCP server - this is without model, just to show how the client can call the server functions

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_direct_client():
    # Phase 1 - Define how to connect to the MCP server (using standard input/output)
    server_params = StdioServerParameters(
        command = "python",
        args=["mcp_server.py"],
    )
    print(" Connecting to MCP Server... ")

    # Phase 2 - Establish the client session with the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the protocol session
            await session.initialize()
            print(" Connected to MCP Server! ")

            # Phase 3 - Ask the connected server about the available tools (functions) it has registered
            print("\n Requesting list of available tools from MCP Server...")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f" - Tool Name: {tool.name}, Description: {tool.description}")
            print("\n")

            # Phase 4 - Calling the tool directly using CLI
            print(" Executing tools programatically: ")
            try:
                num1 = float(input("First number: "))
                num2 = float(input("Second number: "))
            except ValueError:
                print("Invalid input. Please enter numeric values.")
                return
            
            operation = input("Choose an operation (add, subtract, multiply, divide): ").strip().lower()
            if not operation: 
                print("No operation selected. Exiting.")
                return
            
            print(f"\n Calling tool '{operation}' with arguments: a={num1}, b={num2} ")
            mcp_result = await session.call_tool(operation, arguments={"a": num1, "b": num2})

            print(f"\n Result from MCP Server for '{operation}': {mcp_result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(run_direct_client())