"""
Agent Backend Module (MCP Client + FastAPI).
Connects to the standalone MCP Server, loads tools, and exposes a REST API
so the React Frontend can communicate with the LangGraph Agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import config

# Maximum number of past messages kept in history to prevent token overflow
MAX_HISTORY = 10

# Global state shared across requests
_agent = None
_chat_history = []
_mcp_exit_stack = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the full lifecycle of the MCP connection and LangGraph agent.

    On startup: spawns the MCP server subprocess, initializes the session, and
    builds the ReAct agent with the loaded tools.
    On shutdown: cleanly closes the MCP session and terminates the subprocess.
    """
    global _agent, _mcp_exit_stack

    print("\n--- Starting FastAPI: Connecting to MCP Server ---")

    llm = ChatOllama(model=config.LLM_MODEL_NAME, temperature=0.1)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    # Use an async context manager stack so we can close both the transport
    # and the session cleanly in the shutdown phase.
    mcp_context = stdio_client(server_params)
    read, write = await mcp_context.__aenter__()
    _mcp_exit_stack = mcp_context

    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()

    tools = await load_mcp_tools(session)
    print(f"Successfully loaded {len(tools)} tools from MCP.\n")

    _agent = create_react_agent(llm, tools)

    yield  # Application runs here

    # --- Shutdown phase ---
    print("\n--- Shutting down: Closing MCP connection ---")
    try:
        await session.__aexit__(None, None, None)
        await _mcp_exit_stack.__aexit__(None, None, None)
    except Exception as e:
        print(f"Warning: Error during MCP cleanup: {e}")


# Initialize FastAPI with the lifespan context manager
app = FastAPI(title="Airline Ticket AI Agent API", lifespan=lifespan)

# Allow the React frontend (port 5173) to communicate with this backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for incoming chat messages from the frontend
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Receives a message from the React frontend, runs it through the ReAct agent,
    and returns the AI response. Chat history is kept bounded to MAX_HISTORY entries.
    """
    global _chat_history

    system_message = """You are a helpful, professional AI assistant for an airline company.
    You help users query flights, book tickets, and perform check-ins.
    Always use the provided tools to fetch real data. DO NOT make up flight numbers or ticket IDs.
    If the user provides city names (e.g., Istanbul), figure out the airport code (e.g., IST) before calling the tool.
    The date_from must always be in 'YYYY-MM-DD' format.
    Respond in a friendly and polite manner. Avoid technical jargon.
    Structure your responses cleanly."""

    # Trim history to the last MAX_HISTORY entries before appending the new message.
    # This prevents the prompt from growing unboundedly and causing token overflow.
    _chat_history = _chat_history[-MAX_HISTORY:]
    _chat_history.append(("user", request.message))

    messages_to_send = [("system", system_message)] + _chat_history

    response = await _agent.ainvoke({"messages": messages_to_send})
    ai_response = response["messages"][-1].content
    _chat_history.append(("assistant", ai_response))

    return {"reply": ai_response}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
