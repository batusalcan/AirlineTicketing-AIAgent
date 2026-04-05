"""
Main entry point for testing the AI Agent in the terminal.
Demonstrates the use of the FlightAgentFacade.
"""

from agent_core import FlightAgentFacade

def main():
    print("\n--- Airline Ticketing AI Agent Initializing ---")
    print("Connecting to Local LLM (Ollama) and loading Midterm APIs...\n")
    
    # Instantiate the Facade
    agent = FlightAgentFacade()
    
    print("Agent is ready! Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        print("\nAgent is thinking...")
        
        # The Facade hides all ReAct and API calling complexities
        response = agent.ask_agent(user_input)
        
        print(f"\nAI Agent: {response}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()