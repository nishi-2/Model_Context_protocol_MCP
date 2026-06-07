import asyncio
import json
import os
import time
from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# gpt-4o-mini Pricing (per 1 Million Tokens)
INPUT_PRICE_PER_MILLION = 0.150
OUTPUT_PRICE_PER_MILLION = 0.600

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates the cost of an API call based on token usage."""
    input_cost = (prompt_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
    return input_cost + output_cost

def print_metrics(stage: str, latency: float, usage, cost: float):
    """Helper to print nicely formatted metric logs."""
    print(f"\n📊 --- METRICS: {stage} ---")
    print(f"⏱️  Latency: {latency:.2f} seconds")
    if usage:
        print(f"🪙  Tokens : {usage.prompt_tokens} In | {usage.completion_tokens} Out | {usage.total_tokens} Total")
        print(f"💸  Cost   : ${cost:.8f}")
    print("--------------------------------------")

async def run_intelligent_client(query: str):
    # Phase 1 - Connect to the MCP server created
    server_params = StdioServerParameters(
        command = "python",
        args=["mcp_server.py"],
    )
    client = AsyncOpenAI()

    print("User Query: ", query)

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            print("\n✅ Connected to MCP Server!")

            # Phase 2 - Ask MCP Server for the available tools (functions) it has registered
            mcp_tools = await session.list_tools()

            # Phase 3 - Format the MCP tools into OpenAI's required JSON format
            openai_tools = []
            for tool in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "function":
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # Phase 4 - Sending the prompt and the tool to OpenAI
            print("\n⏳ Sending query to OpenAI to determine routing...")
            messages = [{"role": "user", "content": query}]
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto" # Let the model decide if it needs a tool
            )
            stage1_latency = time.time() - start_time
            stage1_cost = calculate_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
            print_metrics("Initial API Call (Routing)", stage1_latency, response.usage, stage1_cost)

            response_message = response.choices[0].message
            total_run_cost = stage1_cost

            # Phase 5 - Check if OpenAI decided to call a tool
            if response_message.tool_calls:
                # Append the assistant's request ONCE before the loop
                messages.append(response_message)
                
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"\n🧠 AI routing to tool: '{tool_name}' with arguments: {tool_args}")
                    
                    # Phase 6 - Execute the tool locally on our MCP Server!
                    mcp_start_time = time.time()
                    mcp_result = await session.call_tool(tool_name, arguments=tool_args)
                    result_text = mcp_result.content[0].text
                    mcp_latency = time.time() - mcp_start_time
                    
                    print(f"⚡ MCP Server calculated: {result_text}")
                    print_metrics("MCP Server Execution", mcp_latency, None, 0.0)
                    
                    # Append the tool response for this specific call
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(result_text)
                    })
                    
                # Phase 7 - Send the math result back to OpenAI for a final friendly answer
                print("\n⏳ Sending math result back to OpenAI for final answer...")
                start_time_final = time.time()
                
                final_response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
                
                stage3_latency = time.time() - start_time_final
                stage3_cost = calculate_cost(final_response.usage.prompt_tokens, final_response.usage.completion_tokens)
                print_metrics("Final API Call (Answer Generation)", stage3_latency, final_response.usage, stage3_cost)
                
                total_run_cost += stage3_cost
                
                print(f"\n🤖 AI Final Answer: {final_response.choices[0].message.content}")
                print(f"💰 Total Cost for this interaction: ${total_run_cost:.8f}\n")
            else:
                print(f"\n🤖 AI Answered directly: {response_message.content}")
                print(f"💰 Total Cost for this interaction: ${total_run_cost:.8f}\n")

if __name__ == "__main__":
    question = "I have 1245 apples. If I divide them equally among 5 friends, how many does each get?"
    asyncio.run(run_intelligent_client(question))