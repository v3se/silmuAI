import React, { useState, useRef, useEffect } from "react";
import './App.css';

function BlinkingDots() {
  const [dots, setDots] = useState("");
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 3 ? prev + "." : ""));
    }, 400);
    return () => clearInterval(interval);
  }, []);
  return <span>{dots}</span>;
}

function App() {
  const [messages, setMessages] = useState([
    { sender: "assistant", text: "Hei! Miten voin auttaa kasveihisi liittyen?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  const user_id = "demo-user";

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/plants/care-instructions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id, prompt: input })
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { sender: "assistant", text: data.answer }
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "assistant", text: "Virhe palvelussa." }
      ]);
    }
    setInput("");
    setLoading(false);
  };

  return (
    <div style={{
      maxWidth: 700,           // Increased width
      margin: "40px auto",
      fontFamily: "system-ui, sans-serif",
      background: "#f4f7fa",
      borderRadius: 16,        // Slightly more rounded
      boxShadow: "0 4px 24px #0002",
      padding: 32              // More padding
    }}>
      <h2 style={{ textAlign: "center", color: "#2e7d32", fontSize: 32 }}>Kasvichat</h2>
      <div
        ref={chatRef}
        style={{
          border: "1.5px solid #c8e6c9",
          background: "#fff",
          padding: 24,         // More padding
          minHeight: 420,      // Increased height
          maxHeight: 600,      // Increased max height
          overflowY: "auto",
          marginBottom: 24,
          borderRadius: 12,
          boxShadow: "0 2px 8px #0001"
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
              margin: "8px 0"
            }}
          >
            <div
              style={{
                background: msg.sender === "user" ? "#c8e6c9" : "#e3f2fd",
                color: "#222",
                padding: "10px 14px",
                borderRadius: 18,
                maxWidth: "75%",
                fontSize: 16,
                boxShadow: "0 1px 2px #0001"
              }}
            >
              <b style={{ fontWeight: 500 }}>
                {msg.sender === "user" ? "Sinä" : "Asiantuntija"}
              </b>
              <div style={{ marginTop: 2 }}>{msg.text}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div
              style={{
                background: "#e3f2fd",
                color: "#222",
                padding: "10px 14px",
                borderRadius: 18,
                fontSize: 16,
                boxShadow: "0 1px 2px #0001"
              }}
            >
              <b>Asiantuntija</b>
              <div style={{ marginTop: 2 }}>
                Vastataan
                <BlinkingDots />
              </div>
            </div>
          </div>
        )}
      </div>
      <form onSubmit={sendMessage} style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Kirjoita viesti..."
          style={{
            flex: 1,
            padding: 12,
            borderRadius: 8,
            border: "1px solid #bdbdbd",
            fontSize: 16
          }}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            background: "#388e3c",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "0 20px",
            fontSize: 16,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          Lähetä
        </button>
      </form>
    </div>
  );
}

export default App;
