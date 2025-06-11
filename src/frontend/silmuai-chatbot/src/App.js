import React, { useState, useRef, useEffect } from "react";
import './App.css';
import { Amplify } from "aws-amplify";
import { Auth } from "aws-amplify/auth";
import { fetchAuthSession, signOut } from "aws-amplify/auth";
import awsExports from "./aws-exports";
import Login from "./Login";
import { jwtDecode } from "jwt-decode";
import ReactMarkdown from "react-markdown";
Amplify.configure(awsExports);

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

function appendDedup(prev, next) {
  const maxOverlap = Math.min(prev.length, next.length);
  for (let i = maxOverlap; i > 0; i--) {
    if (prev.endsWith(next.slice(0, i))) {
      return prev + next.slice(i);
    }
  }
  return prev + next;
}

function App() {
  const [messages, setMessages] = useState([
    { sender: "assistant", text: "Hei! Miten voin auttaa kasveihisi liittyen?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);
  const ws = useRef(null);
  const inputRef = useRef(null);
  const [jwt, setJwt] = useState(null);
  const [user, setUser] = useState(null);

  const user_id = jwt ? jwtDecode(jwt).sub : "anonymous";
  const WS_API_URL = process.env.REACT_APP_WS_API_URL;

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (jwt) {
      connectWebSocket(jwt);
    }
    // eslint-disable-next-line
  }, [jwt]);

  // Check for existing session on mount
  useEffect(() => {
    fetchAuthSession()
      .then(session => {
        const jwt = session.tokens?.idToken?.toString();
        if (jwt) setJwt(jwt);
      })
      .catch(() => {
        // Not signed in, do nothing
      });
  }, []);

  useEffect(() => {
    if (inputRef.current && !loading) {
      inputRef.current.focus();
    }
  }, [loading]);

  const connectWebSocket = (jwt) => {
    console.log("Connecting to WebSocket:", `${WS_API_URL}?Authorization=${jwt}`);
    ws.current = new WebSocket(`${WS_API_URL}?Authorization=${jwt}`);

    ws.current.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.current.onerror = (e) => {
      console.error("WebSocket error", e);
    };

    ws.current.onmessage = (event) => {
      console.log("WebSocket message received:", event.data); // <-- log all incoming messages
      const data = JSON.parse(event.data);
      if (data.token) {
        setMessages((msgs) => {
          const last = msgs[msgs.length - 1];
          if (last && last.sender === "assistant" && last.streaming) {
            last.text = appendDedup(last.text, data.token);
            return [...msgs.slice(0, -1), last];
          } else {
            return [
              ...msgs,
              { sender: "assistant", text: data.token, streaming: true }
            ];
          }
        });
      }
      if (data.error) {
        console.error("Backend error:", data.error);
      }
      if (data.done) {
        setLoading(false);
        console.log("Stream done");
        if (inputRef.current) inputRef.current.focus(); // <-- keep focus after answer
      }
    };

    ws.current.onclose = () => {
      console.log("WebSocket closed");
    };
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim() || !ws.current || ws.current.readyState !== 1) return;
    console.log("Sending message:", { user_id, prompt: input });
    setMessages((msgs) => [
      ...msgs,
      { sender: "user", text: input },
      { sender: "assistant", text: "", streaming: true }
    ]);
    ws.current.send(JSON.stringify({ user_id, prompt: input }));
    setInput("");
    setLoading(true);
    if (inputRef.current) inputRef.current.focus(); // <-- keep focus after send
  };

  const handleLogout = async () => {
    await signOut();
    setJwt(null);
    setUser(null);
  };

  if (!jwt) {
    return <Login onSignIn={({ user, jwt }) => { setUser(user); setJwt(jwt); }} />;
  }

  return (
    <div style={{
      maxWidth: 700,
      margin: "40px auto",
      fontFamily: "system-ui, sans-serif",
      background: "#f4f7fa",
      borderRadius: 16,
      boxShadow: "0 4px 24px #0002",
      padding: 32,
      position: "relative" // <-- Add this for absolute positioning of the button
    }}>
      <button
        onClick={handleLogout}
        className="logout-btn"
      >
        Kirjaudu ulos
      </button>
      <h2 style={{ textAlign: "center", color: "#2e7d32", fontSize: 32 }}>SilmuAI Chat</h2>
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
                {msg.sender === "user" ? "Sinä" : "SilmuAI"}
              </b>
              <div style={{ marginTop: 2 }}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {loading && !messages.some(m => m.sender === "assistant" && m.streaming) && (
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
              <b>SilmuAI</b>
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
          ref={inputRef}
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
