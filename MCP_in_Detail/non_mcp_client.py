# Using OpenAI Model to perform calculations instead of us using pure Python functions
# Here, we will not use MCP, but will use OpenAI and pass query to it and get the answer
# This will help us understand the difference between using MCP and using model with tools directly

import json
import os
import time
import MCP_in_Detail.calculator as calculator
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

# Setting up OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# GPT-4o-mini Pricing in Dollars (per 1 Million Tokens)
INPUT_PRICE_PER_MILLION = 0.15
OUTPUT_PRICE_PER_MILLION = 0.60


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates the cost of an API Call based on Token Usage"""
    input_cost = (prompt_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
    return input_cost + output_cost


def print_metrics(stage: str, latency: float, usage, cost: float):
    """Helper function to print formatted metric logs"""
    print(f"\n📊 --- METRICS: {stage} ---")
    print(f"⏱️  Latency: {latency:.2f} seconds")
    if usage:
        print(f"🪙  Tokens : {usage.prompt_tokens} In | {usage.completion_tokens} Out | {usage.total_tokens} Total")
        print(f"💸  Cost   : ${cost:.6f}")
    print("-" * 40, "\n")


def main(query: str):
    client = OpenAI()

    # Define the schema manually
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "subtract",
                "description": "Subtract two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "divide",
                "description": "Divide two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        },
    ]

    messages = [{"role": "user", "content": query}]
    print(f"👤 User Query: {query}")

    # Phase 1 - Initial AI Call
    print("\n⏳ Sending query to OpenAI to determine routing and arguments...")
    start_time = time.time()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto",
    )

    phase1_latency = time.time() - start_time
    phase1_cost = calculate_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
    print_metrics("Phase 1 - Initial API Call for Routing", phase1_latency, response.usage, phase1_cost)

    response_message = response.choices[0].message
    total_run_cost = phase1_cost

    print(f"📥 OpenAI Phase 1 Response Message:\n{response_message}")

    if response_message.tool_calls:
        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"\n🧠 AI routed to tool: '{tool_name}' with arguments: {tool_args}")

            # Phase 2 - Execute the tool function selected by the model
            local_start_time = time.time()

            if tool_name == "add":
                result = calculator.add(tool_args["a"], tool_args["b"])
            elif tool_name == "subtract":
                result = calculator.subtract(tool_args["a"], tool_args["b"])
            elif tool_name == "multiply":
                result = calculator.multiply(tool_args["a"], tool_args["b"])
            elif tool_name == "divide":
                result = calculator.divide(tool_args["a"], tool_args["b"])
            else:
                result = "Error: Unknown tool called."

            local_latency = time.time() - local_start_time
            print(f"⚡ Local execution of calculation completed: {result}")
            print_metrics("Phase 2 - Local Tool Execution", local_latency, None, 0.0)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(result),
            })

        # Phase 3 - Final API Call to get the final response after tool execution
        print("⏳ Sending math result back to OpenAI for final response generation...")
        start_time_final = time.time()
        
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        
        phase3_latency = time.time() - start_time_final
        phase3_cost = calculate_cost(final_response.usage.prompt_tokens, final_response.usage.completion_tokens)
        print_metrics("Phase 3 - Final API Call after Tool Execution", phase3_latency, final_response.usage, phase3_cost)

        total_run_cost += phase3_cost
        print(f"🤖 AI Final Answer: {final_response.choices[0].message.content}")
        print(f"\n💰 Total Cost of this operation: ${total_run_cost:.6f}")

    else:
        print(f"\n🤖 AI Answered directly: {response_message.content}")
        print(f"\n💰 Total Cost of this operation: ${total_run_cost:.6f}")


if __name__ == "__main__":
    QUERY = "Where is Kolkata? Tell me within 20 words."
    main(QUERY)