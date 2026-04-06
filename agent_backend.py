"""
Agent Backend Module (MCP Client).
Connects to the standalone MCP Server via standard I/O, loads the tools dynamically,
and runs the modern LangGraph ReAct agent loop.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import config

async def run_agent():
    print("\n--- Airline Ticketing AI Agent Initializing ---")
    print("Starting MCP Client and connecting to MCP Server...")

    # 1. Injecting the LLM Engine (Lokal Ollama)
    llm = ChatOllama(model=config.LLM_MODEL_NAME, temperature=0.1)

    # 2. Setup standard I/O parameters to spawn and connect to the MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    # 3. Establish the async connection to the MCP Server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 4. Dynamically load tools from the connected MCP Server
            tools = await load_mcp_tools(session)
            print(f"Successfully loaded {len(tools)} tools from the MCP Server.\n")

            # 5. Create the Modern LangGraph Agent (Removed state_modifier to avoid version conflicts)
            agent = create_react_agent(llm, tools)
            
            print("Agent is ready! Type 'exit' to quit.\n")
            
            # System Prompt Setup (We will inject this directly into the messages)
            system_message = """You are a helpful, professional AI assistant for an airline company.
            You help users query flights, book tickets, and perform check-ins.
            Always use the provided tools to fetch real data. DO NOT make up flight numbers or ticket IDs.
            If the user provides city names (e.g., Istanbul), figure out the airport code (e.g., IST) before calling the tool.
            The date_from must always be in 'YYYY-MM-DD' format.
            Respond in a friendly and polite manner. Avoid technical jargon."""

            # Simple list to hold conversation history
            chat_history = []

            # 6. Terminal Chat Loop
            while True:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break

                print("\nAgent is thinking...")
                
                # Append user message to history
                chat_history.append(("user", user_input))
                
                # Combine system prompt + history to guarantee the LLM understands its role
                messages_to_send = [("system", system_message)] + chat_history
                
                # ainvoke runs the agent loop (reasoning -> tool call -> response)
                response = await agent.ainvoke({"messages": messages_to_send})
                
                # The final AI response is the last message in the array
                ai_response = response["messages"][-1].content
                
                # Append AI response to history
                chat_history.append(("assistant", ai_response))
                
                print(f"\nAI Agent: {ai_response}\n")
                print("-" * 50)

if __name__ == "__main__":
    # Run the async loop
    asyncio.run(run_agent())