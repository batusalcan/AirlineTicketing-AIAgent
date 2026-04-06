# AI Agent - Airline Ticketing System ✈️🤖

## 📖 Project Overview

This project is an AI-powered chat application built for an airline ticketing system. It leverages a local Large Language Model (LLM) and the Model Context Protocol (MCP) to interact seamlessly with existing Midterm REST APIs. The AI Agent acts as an intelligent assistant capable of querying available flights, booking tickets, and performing passenger check-ins autonomously based on natural language user prompts.

---

## 🔗 Deliverables Links

As per the assignment requirements, here are the core links to the project artifacts:

- **Source Code Repository:** [AirlineTicketing-AIAgent on GitHub](https://github.com/batusalcan/AirlineTicketing-AIAgent)
- **Project Presentation Video:** [Insert YouTube/Drive Link Here]
- **Midterm Deployed Swagger URL:** [Airline API Gateway Swagger](https://batu-airline-gateway-final-d0hbhnc6c8fadgee.italynorth-01.azurewebsites.net/swagger/index.html)

---

## 🛠 Technology Stack

The application is built using a modern, decoupled stack, separating the client, agent backend, and tool server.

| Component               | Technology                   | Description                                                        |
| :---------------------- | :--------------------------- | :----------------------------------------------------------------- |
| **Frontend**            | React (Vite), Tailwind CSS   | Modern, responsive chat UI designed with Lucide React icons.       |
| **Backend API**         | FastAPI (Python), Uvicorn    | Exposes the `/chat` endpoint to the frontend React app.            |
| **LLM & Orchestration** | LangGraph, ChatOllama        | Implements the ReAct agent architecture with a local Ollama model. |
| **Tool Protocol**       | MCP (`mcp` library), FastMCP | Connects the LLM to the Midterm APIs via Standard I/O (`stdio`).   |
| **External APIs**       | C# .NET 8, Azure API Gateway | The Midterm Airline APIs hosted on the cloud.                      |

---

## 📂 Folder Structure

```text
AirlineTicketing-AIAgent/
│
├── frontend/                  # React (Vite) Frontend Application
│   ├── src/
│   │   ├── App.jsx            # Main Chat Interface & Logic
│   │   ├── index.css          # Tailwind CSS styles
│   │   └── main.jsx           # React Entry Point
│   ├── package.json           # Frontend dependencies
│   ├── tailwind.config.js     # Tailwind configurations
│   └── vite.config.js         # Vite bundler configurations
│
├── agent_backend.py           # FastAPI Backend & MCP Client (LangGraph Agent)
├── mcp_server.py              # Standalone FastMCP Server exposing Midterm APIs
├── config.py                  # Environment variables & API credentials
├── requirements.txt           # Python dependencies
└── README.md                  # Project Documentation
```

---

## 🏛 Architectural Decisions & Design Patterns

1. **ReAct (Reasoning and Acting) Pattern:** Utilized via `LangGraph` to allow the LLM to understand the user intent, decide which tool to call, execute the tool, and format the response to the user.
2. **Strategy Pattern (LLM Integration):** The architecture leverages the Strategy pattern through LangChain components. The LLM engine is decoupled from the agent logic, meaning transitioning from the local `ChatOllama` to a cloud provider like `ChatOpenAI` or `ChatAnthropic` requires only a single-line configuration change without altering the core agent execution flow.
3. **Facade Pattern (MCP Server):** The `mcp_server.py` acts as a structural Facade. It hides the underlying complexities of the Midterm C# APIs (such as JWT token generation, header management, and strict JSON payload formatting) from the AI Agent, providing a simplified and clean tool interface (`query_flight`, `book_ticket`, `check_in`).
4. **Model Context Protocol (MCP):** To decouple the LLM from the actual API implementations, the project uses the official MCP architecture. `mcp_server.py` acts as an independent tool server, while `agent_backend.py` acts as the MCP Client.
5. **Standard I/O (`stdio`) Communication:** The connection between the MCP Client and MCP Server is established using `stdio` subprocess communication. This ensures secure, robust, and isolated execution without opening unnecessary network ports for local tool execution, adhering to industry best practices.
6. **Client-Server Architecture:** The React frontend is completely decoupled from the Python backend, communicating strictly via RESTful HTTP `POST /chat` calls.
7. **Messaging Architecture (REST vs. Firestore):** While the assignment instructions suggested considering Firestore/Realtime Database for messaging, I opted for the "another API" approach mentioned in the same section and implemented a custom RESTful API (`POST /chat`) using FastAPI. This strictly aligns with the "Simple implementation idea" table provided in the assignment and ensures full control over the LangGraph execution and MCP tool routing without relying on third-party database triggers.

---

## 📋 Assignment Requirements & Assumptions

### Requirements Met:

- ✅ Developed a Frontend chat app (React/Vite).
- ✅ Created an Agent backend / LLM integration (FastAPI + LangGraph + Ollama).
- ✅ Implemented an MCP Client and Server layer.
- ✅ Integrated successfully with Midterm APIs via Azure API Gateway.
- ✅ Supported Query Flight, Book Flight, and Check-in operations.

### Assumptions:

- **Authentication:** As permitted by the assignment, the chat application uses a constant `userid/password` (defined in `config.py`) to fetch JWT Bearer tokens under the hood for protected endpoints (Buy Ticket, Check-in).
- **Check-in API Design:** Based on the midterm requirement table, the Check-in API expects `flightNumber`, `date`, and `passengerName`. It is assumed that a standard PNR (Ticket Number) is not strictly required for the backend logic if the passenger matches the flight manifest.

---

## 🐛 Issues Encountered & Solutions

1. **MCP Server SSE (Server-Sent Events) Host Assignment Error:**
   - _Issue:_ Attempting to force `FastMCP` to run on a specific host/port via kwargs (`mcp.run(transport='sse', host="127.0.0.1", port=5000)`) resulted in a `TypeError: FastMCP.run() got an unexpected keyword argument`.
   - _Solution:_ Switched the architecture back to the highly stable **Standard I/O (`stdio`)** communication method. The FastAPI backend now securely spins up the MCP server as a local subprocess.
2. **Check-in API Payload Mismatch:**
   - _Issue:_ The LLM initially tried to send a `{"ticketNumber": "7F5A65"}` payload to the Check-in API, causing a 400 Bad Request since the Midterm API was designed to accept Flight Number, Date, and Passenger Name.
   - _Solution:_ Updated the `check_in_passenger` MCP tool's docstring and function parameters to strictly demand `flight_number`, `date`, and `passenger_name`, bridging the gap between LLM hallucination and actual API specs.
3. **Missing Authentication Token in Check-in Tool:**
   - _Issue:_ The check-in request was rejected with a `401 Unauthorized` status code.
   - _Solution:_ Implemented the `get_auth_token()` helper function within the check-in MCP tool to attach the JWT Bearer token dynamically before hitting the API Gateway.
4. **LLM Context Window Limit (Token Overflow):**
   - _Issue:_ Continuous, long chat sessions caused the `_chat_history` list to grow without bounds, eventually exceeding the local LLM's maximum token context limit and causing crashes.
   - _Solution:_ Implemented array trimming (`_chat_history[-10:]`) before feeding the prompt to the LangGraph agent, ensuring only the most relevant recent memory is retained while preventing token overflow.
5. **JWT Token Expiration & Caching:**
   - _Issue:_ The `_JWT_TOKEN` was being permanently cached. If the system ran longer than the token's lifespan, subsequent tool calls (Book Flight, Check-in) silently failed with `401 Unauthorized`.
   - _Solution:_ Updated the token logic to handle expirations gracefully by passing `force_refresh=True` on a 401 response, allowing the system to fetch a fresh token dynamically when the old one expires.
6. **FastAPI Subprocess Memory Leaks (Zombie Processes):**
   - _Issue:_ Using the deprecated `@app.on_event("startup")` caused the MCP subprocess to remain open in the background even after shutting down the FastAPI server, leading to memory leaks.
   - _Solution:_ Migrated the application to FastAPI's modern `@asynccontextmanager` lifespan events. This guarantees that the `__aexit__` cleanup method is explicitly called on shutdown, safely terminating the `mcp_server.py` subprocess.

---

## 🚀 How to Run Locally

### Prerequisites

- Node.js (v18+ recommended) and `npm` installed.
- Python 3.10+ installed.
- **Ollama** installed and running locally with the necessary model downloaded: `ollama run llama3.1`

### Step 1: Start the Backend (API & Agent)

Open a terminal in the root directory (`AirlineTicketing-AIAgent/`):

```bash
# 1. Activate your virtual environment (if you have one)
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows

# 2. Install Python dependencies using the requirements file
pip install -r requirements.txt

# 3. Start the Agent Backend (this will auto-start the MCP Server via stdio)
python agent_backend.py
```

_The backend will now run on `http://localhost:8000`._

### Step 2: Start the Frontend (React Chat App)

Open a **new, second terminal** in the root directory:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node dependencies (only needed the first time)
npm install

# 3. Start the Vite development server
npm run dev
```

_The React UI will now run on `http://localhost:5173`. Open this URL in your browser to start chatting with the AI Agent!_

## 🧪 Example Usage / Test Scenarios

Once the application is running, you can test the AI Agent's capabilities by pasting the following prompts sequentially into the chat interface:

1. **Query Flight:**
   > _"Hi! Can you find available flights from Istanbul to Frankfurt on 2026-05-10?"_
2. **Book Flight:**
   > _"Great! I would like to book a ticket for Batuhan Salcan on flight TK1523 for that date."_
3. **Check-in Passenger:**
   > _"Awesome. Now I want to check in for my flight TK1523 on 2026-05-10 for Batuhan Salcan."_

The AI will autonomously call the respective Midterm APIs, parse the JSON responses, and provide you with natural language confirmations.

---

## 🔮 Future Improvements

While the current architecture successfully fulfills all assignment requirements, future iterations could include:

- **Persistent Chat Memory:** Integrating a database (like PostgreSQL or MongoDB) to save user sessions across browser reloads.
- **Cloud Deployment:** Containerizing the frontend, backend, and MCP server using Docker and deploying them to AWS or Azure.
- **Enhanced Error Handling:** Providing the frontend with explicit UI elements (like toasts or cards) when an API goes down, rather than relying solely on the LLM's text response.

```

```
