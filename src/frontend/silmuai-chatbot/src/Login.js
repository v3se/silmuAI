import React, { useState } from "react";
import { signIn, signOut, fetchAuthSession } from "aws-amplify/auth";

export default function Login({ onSignIn }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSignIn = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await signOut();
            await signIn({ username, password });
            const session = await fetchAuthSession();
            const jwt = session.tokens?.idToken?.toString();
            if (!jwt) throw new Error("Kirjautumistunnusta ei löytynyt");
            onSignIn({ user: username, jwt });
        } catch (err) {
            setError(err.message || "Kirjautuminen epäonnistui");
        }
        setLoading(false);
    };

    return (
        <div style={{
            maxWidth: 400,
            margin: "100px auto",
            padding: 32,
            background: "#fff",
            borderRadius: 16,
            boxShadow: "0 4px 24px #0002",
            fontFamily: "system-ui, sans-serif"
        }}>
            <h2 style={{ textAlign: "center", color: "#2e7d32" }}>Kirjaudu sisään</h2>
            <form onSubmit={handleSignIn} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input
                    type="text"
                    placeholder="Käyttäjätunnus"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    style={{ padding: 12, borderRadius: 8, border: "1px solid #bdbdbd" }}
                    required
                />
                <input
                    type="password"
                    placeholder="Salasana"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    style={{ padding: 12, borderRadius: 8, border: "1px solid #bdbdbd" }}
                    required
                />
                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        background: "#388e3c",
                        color: "#fff",
                        border: "none",
                        borderRadius: 8,
                        padding: "12px 0",
                        fontSize: 16,
                        cursor: loading ? "not-allowed" : "pointer"
                    }}
                >
                    {loading ? "Kirjaudutaan..." : "Kirjaudu"}
                </button>
                {error && <div style={{ color: "red", marginTop: 8 }}>{error}</div>}
            </form>
        </div>
    );
}