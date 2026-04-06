"""
Agent Backend Module (MCP Client + FastAPI).
Connects to the standalone MCP Server, loads tools, and exposes a REST API 
so the React Frontend can communicate with the LangGraph Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import config

# Initialize FastAPI App
app = FastAPI(title="Airline Ticket AI Agent API")

# Setup CORS so React frontend (running on port 5173) can talk to this backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to keep the MCP session alive
_agent = None
_chat_history = []
_mcp_context = None

# Pydantic model for receiving React messages
class ChatRequest(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    """Starts the MCP server and LangGraph agent when FastAPI boots up."""
    global _agent, _mcp_context
    print("\n--- Starting FastAPI and Connecting to MCP Server ---")
    
    llm = ChatOllama(model=config.LLM_MODEL_NAME, temperature=0.1)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    # Establish the connection and keep it open
    _mcp_context = stdio_client(server_params)
    read, write = await _mcp_context.__aenter__()
    
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    
    tools = await load_mcp_tools(session)
    print(f"Successfully loaded {len(tools)} tools from MCP.\n")
    
    _agent = create_react_agent(llm, tools)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint for React frontend to send messages and get AI responses."""
    global _chat_history
    
    system_message = """You are a helpful, professional AI assistant for an airline company.
    You help users query flights, book tickets, and perform check-ins.
    Always use the provided tools to fetch real data. DO NOT make up flight numbers or ticket IDs.
    If the user provides city names (e.g., Istanbul), figure out the airport code (e.g., IST) before calling the tool.
    The date_from must always be in 'YYYY-MM-DD' format.
    Respond in a friendly and polite manner. Avoid technical jargon.
    Structure your responses cleanly."""

    _chat_history.append(("user", request.message))
    messages_to_send = [("system", system_message)] + _chat_history
    
    response = await _agent.ainvoke({"messages": messages_to_send})
    ai_response = response["messages"][-1].content
    _chat_history.append(("assistant", ai_response))
    
    return {"reply": ai_response}

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)