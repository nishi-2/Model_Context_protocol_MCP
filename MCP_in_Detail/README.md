# Quickstart Guide: Model Context Protocol (MCP) Calculator Agent

This project demonstrates how to decouple custom internal tool execution from Large Language Models (LLMs) using the open-standard **Model Context Protocol (MCP)**. By isolating execution logic, you prevent model hallucinations and make your tool architecture independent of specific LLM provider APIs.

## Getting Started

### 1. Installation & Environment Configuration
Clone this repository or move the source files into a local workspace directory. Install the required asynchronous and tool orchestration dependencies via `pip`:

```bash
# Create and activate an insulated virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install core development dependencies
pip install -r requirements.txt

```

Create a secure `.env` file in the root configuration directory to declare your authorization tokens:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here

```

### 2. Execution Orchestration

To observe how an LLM dynamically discovers local capabilities and processes structural math requests without manual parameter wiring, execute the components in separate terminal instances:

* **Step 1: Start the isolated tool environment**
```bash
python mcp_server.py

```


* **Step 2: Run the intelligent router agent**
```bash
python intelligent_client.py

```



---

# MCP Core Functions Explained

Let's break down the key functions used throughout the project. Think of this section as a practical reference guide that explains what each component does and why it's important.

---

## 1. `FastMCP("Calculator Server")`

### What it does

This creates an MCP server instance and gives it a name. You can think of it as the starting point of your MCP application.

```python
mcp = FastMCP("Calculator Server")
```

### Why it's needed

Just like a web application needs a web server, an MCP application needs an MCP server. This server becomes the central place where all tools are registered and exposed to clients.

### Behind the scenes

When FastMCP starts, it automatically handles much of the heavy lifting, including:

* Managing tool registration
* Creating tool definitions from Python code
* Handling MCP communication
* Responding to requests from MCP clients

Without FastMCP, you would need to implement much of this functionality yourself.

---

## 2. `@mcp.tool()`

### What it does

This decorator tells FastMCP that a Python function should be exposed as an MCP tool.

```python
@mcp.tool()
def add(a: float, b: float):
    """Add two numbers."""
    return a + b
```

### Why it's needed

Normally, Python functions are only available inside your program. By adding `@mcp.tool()`, you're making that function discoverable and usable by MCP clients.

### Behind the scenes

FastMCP examines:

* The function name (`add`)
* The input parameters (`a`, `b`)
* The parameter types (`float`)
* The docstring description

Using this information, it automatically creates the metadata that clients need to understand how the tool works.

This means less manual configuration and fewer chances for schema mismatches.

---

## 3. `StdioServerParameters(command, args)`

### What it does

This tells the client how to start and connect to the MCP server.

```python
server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"]
)
```

### Why it's needed

Before a client can use tools, it needs to know where the server is and how to launch it.

### Behind the scenes

When the client starts, these parameters tell the operating system:

> "Run the file `mcp_server.py` using Python and establish a communication channel with it."

The client and server then communicate through standard input and output streams (`stdio`).

---

## 4. `stdio_client(server_params)`

### What it does

This creates a connection to the MCP server using the configuration provided above.

```python
async with stdio_client(server_params) as (read_stream, write_stream):
```

### Why it's needed

This function establishes the communication channel between the client and the server.

### Behind the scenes

When executed, it:

1. Starts the MCP server process
2. Opens communication streams
3. Creates channels for sending and receiving messages

Think of it as opening a dedicated conversation line between two programs.

---

## 5. `ClientSession(read_stream, write_stream)`

### What it does

This creates an MCP session over the communication streams.

```python
session = ClientSession(read_stream, write_stream)
```

### Why it's needed

The streams only allow raw data to move back and forth. The session adds MCP protocol awareness on top of those streams.

### Behind the scenes

The session handles:

* Sending requests
* Receiving responses
* Tracking connection state
* Formatting protocol messages

Without a session, you would need to manually create and parse protocol messages yourself.

---

## 6. `await session.initialize()`

### What it does

This starts the MCP handshake process.

```python
await session.initialize()
```

### Why it's needed

Before client and server can work together, they need to verify that both sides support the protocol and are ready to communicate.

### Behind the scenes

During initialization:

* The client introduces itself
* The server introduces itself
* Protocol capabilities are exchanged
* The connection becomes active

You can think of it as the "hello" phase of the MCP connection.

---

## 7. `await session.list_tools()`

### What it does

This asks the server:

> "What tools do you have available?"

```python
tools = await session.list_tools()
```

### Why it's useful

The client doesn't need to hardcode tool information.

Instead, it can dynamically discover available tools.

### Behind the scenes

The server responds with information such as:

* Tool names
* Tool descriptions
* Expected inputs
* Parameter types

This is one of MCP's biggest advantages because clients can adapt to new tools without requiring code changes.

---

## 8. `await session.call_tool(name, arguments)`

### What it does

This executes a specific tool on the MCP server.

```python
result = await session.call_tool(
    "divide",
    {
        "a": 1245,
        "b": 5
    }
)
```

### Why it's needed

This is the actual step where work gets done.

### Behind the scenes

The client sends:

```json
{
  "tool": "divide",
  "arguments": {
    "a": 1245,
    "b": 5
  }
}
```

The server:

1. Finds the requested tool
2. Validates the inputs
3. Executes the function
4. Returns the result

The client then receives the response and can use it directly or pass it back to an LLM.

---

# Why Do We Use Async (`async` / `await`)?

You may have noticed that most MCP examples use asynchronous programming.

This isn't just a coding style preference—it's a practical way to handle multiple waiting operations efficiently.

Imagine your application is:

* Waiting for an LLM response
* Waiting for an MCP server response
* Waiting for a database query
* Writing logs

Most of the time, the application isn't actually working—it is simply waiting.

With asynchronous programming, Python can use that waiting time to perform other tasks instead of sitting idle.

---

## Benefits of Async Programming

### 1. Better Resource Utilization

Suppose an LLM request takes 2 seconds.

A synchronous program waits for the entire 2 seconds doing nothing else.

An asynchronous program can use that same time to:

* Process another request
* Query another tool
* Handle logging
* Perform background tasks

This leads to better overall performance.

---

### 2. Running Multiple Tasks Concurrently

Imagine a user asks:

> "Fetch customer information, retrieve account history, and generate a summary."

Instead of waiting for each step one after another, asynchronous code can start multiple operations and process them concurrently.

This reduces overall response time and improves scalability.

---

# What If We Don't Use Async?

You can absolutely build MCP applications using synchronous code.

In a synchronous design:

```python
response = client.chat.completions.create(...)
```

The program pauses completely until a response arrives.

Only then does execution continue.

For small projects, this approach is often easier to understand and debug.

However, as traffic grows, the application spends more time waiting on network calls and external services, which can reduce throughput and responsiveness.

---

## When Should You Use Async?

A good rule of thumb is:

* **Learning MCP?** Start with synchronous code.
* **Building production agents?** Async is usually the better choice.
* **Working with multiple tools, APIs, or databases?** Async often provides significant performance benefits.

The important thing to remember is that MCP itself does not require asynchronous programming. Async simply helps your application handle communication more efficiently when multiple operations are happening at the same time.
