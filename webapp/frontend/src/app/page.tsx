'use client'
import { useState, useEffect, useRef } from "react";

export default function Home() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isError, setIsError] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [fullHistory, setHistory] = useState<JSON|null>(null);
  const [message, setMessage] = useState<string>("");
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  interface Message {
    role: string;
    content: string;
  }

  //post chat message on send press
  //stream the response and append it to the last message
  const handleSend = async () => {
    if (message.trim() === "") return;
    const newMessage: Message = {
      role: "user",
      content: message,
    };
    setMessages(prev => [...prev, newMessage]);
    setMessage("");
    setIsLoading(true);
    setIsError(false);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, history: fullHistory }),
      });
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (!line) continue;
          const prefix = line[0];
          const content = line.slice(2);
          try {
            if (prefix === "0") {
                const parsedContent = JSON.parse(content);
                console.log("Parsed content:", parsedContent);
                setMessages(prevMessages => {
                    if (prevMessages.length > 0 && prevMessages[prevMessages.length - 1].role === 'assistant') {
                      // Create a completely new array with a new message object at the end
                      return [
                        ...prevMessages.slice(0, -1),
                        {
                          role: 'assistant',
                          content: prevMessages[prevMessages.length - 1].content + parsedContent
                        }
                      ];
                    } else {
                      return [...prevMessages, { role: 'assistant', content: parsedContent }];
                    }
                  });
            } else if (prefix === "h") {
              const history = JSON.parse(content);
              setHistory(history);
            } else {
              console.log(prefix, JSON.parse(content));
            }
          } catch (err) {
            console.error(err);
          }
        }
      }
    } catch (error) {
      console.error(error);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full items-center p-4">
      <div className="flex-1 flex-col w-11/12 overflow-auto space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`chat ${msg.role === 'user' ? 'chat-start' : 'chat-end'}`}>
            <div className="chat-bubble whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form 
        className="flex h-1/12 w-11/12 flex-row space-x-1" 
        onSubmit={e => {
          e.preventDefault();
          if (!isLoading) handleSend();
        }}
      >
        <input 
          type="text" 
          placeholder="Ask me anything" 
          className="input w-full" 
          value={message} 
          onChange={(e) => setMessage(e.target.value)} 
        />
        <button type="submit" disabled={isLoading} className="btn btn-primary">Send</button>
      </form>
    </div>
  );
}
