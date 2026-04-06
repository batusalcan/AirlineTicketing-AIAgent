import { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  Send,
  Plane,
  Search,
  CheckSquare,
  Plus,
  User,
  Bot,
} from "lucide-react";

function App() {
  const [messages, setMessages] = useState([
    { role: "ai", content: "Hello! How can I assist you today?" },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // Add user message to the UI
    const newMessages = [...messages, { role: "user", content: text }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      // Send the request to our Python FastAPI backend
      const response = await axios.post("http://localhost:8000/chat", {
        message: text,
      });

      // Add the AI's response to the UI
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: response.data.reply },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "Network error. Is the backend running on port 8000?",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    let text = "";
    if (action === "query") text = "I want to query a flight.";
    if (action === "book") text = "I want to book a ticket.";
    if (action === "checkin") text = "I want to check in.";
    sendMessage(text);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Phone-like Chat Container */}
      <div className="w-full max-w-md bg-white rounded-[2rem] shadow-2xl overflow-hidden flex flex-col h-[800px] max-h-[90vh] border-4 border-gray-100">
        {/* Header */}
        <div className="pt-8 pb-4 px-6 text-center border-b bg-white">
          <h1 className="text-xl font-bold text-gray-800">
            AI Agent - Flight Actions
          </h1>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#f8fafc]">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {/* AI Avatar */}
              {msg.role === "ai" && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3 flex-shrink-0 mt-1">
                  <Bot size={18} className="text-blue-600" />
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`p-4 rounded-2xl max-w-[80%] ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-white border text-gray-800 shadow-sm rounded-bl-none"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>

                {/* Add quick action buttons below the first AI message (matching the PDF design) */}
                {idx === 0 && msg.role === "ai" && (
                  <div className="mt-4 space-y-2">
                    <button
                      onClick={() => handleQuickAction("query")}
                      className="w-full flex items-center p-3 bg-blue-50 rounded-xl text-blue-700 hover:bg-blue-100 transition"
                    >
                      <Search size={18} className="mr-3" />{" "}
                      <span className="font-medium text-sm">Query Flight</span>
                    </button>
                    <button
                      onClick={() => handleQuickAction("book")}
                      className="w-full flex items-center p-3 bg-blue-50 rounded-xl text-blue-700 hover:bg-blue-100 transition"
                    >
                      <Plane size={18} className="mr-3" />{" "}
                      <span className="font-medium text-sm">Book Flight</span>
                    </button>
                    <button
                      onClick={() => handleQuickAction("checkin")}
                      className="w-full flex items-center p-3 bg-blue-50 rounded-xl text-blue-700 hover:bg-blue-100 transition"
                    >
                      <CheckSquare size={18} className="mr-3" />{" "}
                      <span className="font-medium text-sm">Check In</span>
                    </button>
                  </div>
                )}
              </div>

              {/* User Avatar */}
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center ml-3 flex-shrink-0 mt-1">
                  <User size={18} className="text-gray-600" />
                </div>
              )}
            </div>
          ))}

          {/* Loading Animation */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3 flex-shrink-0">
                <Bot size={18} className="text-blue-600" />
              </div>
              <div className="bg-white border p-4 rounded-2xl rounded-bl-none shadow-sm flex space-x-2 items-center">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Input Area */}
        <div className="p-4 bg-white border-t flex items-center">
          <button className="p-2 text-blue-500 hover:bg-blue-50 rounded-full transition mr-2">
            <Plus size={24} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
            placeholder="What can I assist you with?"
            className="flex-1 bg-gray-100 border-transparent rounded-full px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="ml-2 p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 transition shadow-md flex items-center justify-center"
          >
            <Send size={18} className="ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
