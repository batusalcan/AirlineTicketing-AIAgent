"""
Agent Core Module.
Implements the ReAct (Reasoning and Acting) architecture.
Utilizes the Facade Design Pattern to hide LangChain complexities from the UI.
Utilizes the Strategy Design Pattern for the LLM injection.
"""

from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from api_tools import query_available_flights, book_flight_ticket, check_in_passenger
import config

class FlightAgentFacade:
    """
    Facade class that handles LLM initialization, tool binding, and memory management.
    The outside world only needs to call the 'ask_agent' method.
    """
    
    def __init__(self):
        # 1. Strategy Pattern: Injecting the LLM Engine (Local Ollama)
        self.llm = ChatOllama(model=config.LLM_MODEL_NAME, temperature=0.1)
        
        # 2. Bind the tools to the agent
        self.tools = [query_available_flights, book_flight_ticket, check_in_passenger]
        
        # 3. System Prompt & ReAct Setup
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful, professional AI assistant for an airline company.
            You help users query flights, book tickets, and perform check-ins.
            Always use the provided tools to fetch real data. DO NOT make up flight numbers or ticket IDs.
            If the user provides city names (e.g., Istanbul), figure out the airport code (e.g., IST) before calling the tool.
            Respond in a friendly and polite manner. Avoid technical jargon in your final response to the user."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"), # This is where ReAct thinking happens
        ])
        
        # 4. Create the Tool Calling Agent and Executor
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # verbose=True allows us to see the AI's thought process in the terminal
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        
        # Simple memory to remember conversation context
        self.chat_history = []

    def ask_agent(self, user_message: str) -> str:
        """
        Takes a user message, processes it through the ReAct agent, 
        updates history, and returns the AI's response.
        """
        response = self.agent_executor.invoke({
            "input": user_message,
            "chat_history": self.chat_history
        })
        
        # Update memory
        self.chat_history.append(("human", user_message))
        self.chat_history.append(("ai", response["output"]))
        
        return response["output"]