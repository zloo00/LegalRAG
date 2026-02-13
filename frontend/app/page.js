"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:4000";

export default function Home() {
  const [telegramUserId, setTelegramUserId] = useState("");
  const [code, setCode] = useState("");
  const [token, setToken] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedToken = localStorage.getItem("legalrag_token");
    const savedUserId = localStorage.getItem("legalrag_user");
    const savedExpires = localStorage.getItem("legalrag_expires");
    if (savedToken) setToken(savedToken);
    if (savedUserId) setTelegramUserId(savedUserId);
    if (savedExpires) setExpiresAt(savedExpires);
  }, []);

  const handleVerify = async () => {
    setError("");
    if (!telegramUserId || !code) {
      setError("Укажите Telegram ID и код доступа.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegramUserId, code }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Ошибка валидации");
      }
      setToken(data.token);
      setExpiresAt(data.expiresAtUtc);
      localStorage.setItem("legalrag_token", data.token);
      localStorage.setItem("legalrag_user", String(telegramUserId));
      localStorage.setItem("legalrag_expires", data.expiresAtUtc);
    } catch (err) {
      setError(err.message || "Ошибка валидации");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    setError("");
    if (!prompt.trim()) return;
    const nextMessages = [...messages, { role: "user", content: prompt.trim() }];
    setMessages(nextMessages);
    setPrompt("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ prompt: nextMessages.at(-1).content }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Ошибка ответа");
      }
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, sources: data.sources || [] },
      ]);
    } catch (err) {
      setError(err.message || "Ошибка ответа");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken("");
    setExpiresAt("");
    setMessages([]);
    localStorage.removeItem("legalrag_token");
    localStorage.removeItem("legalrag_expires");
  };

  return (
    <main className="container">
      <div className="header">
        <h1>Legal RAG</h1>
        <p>Доступ к чату выдаётся по ежедневному коду для юристов.</p>
      </div>

      {!token ? (
        <div className="card auth-panel">
          <div>
            <div className="label">Telegram ID</div>
            <input
              className="input"
              value={telegramUserId}
              onChange={(e) => setTelegramUserId(e.target.value)}
              placeholder="Например, 123456789"
            />
          </div>
          <div>
            <div className="label">Код доступа на сегодня (цифры)</div>
            <input
              className="input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Например, 578123"
            />
          </div>
          {error && <div className="small">{error}</div>}
          <button className="primary-btn" onClick={handleVerify} disabled={loading}>
            {loading ? "Проверяем..." : "Получить доступ"}
          </button>
          <div className="disclaimer">
            Код действует только для вашего Telegram ID и истекает в конце суток (UTC).
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="chat-shell">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="small">Доступ до: {new Date(expiresAt).toUTCString()}</div>
              <button className="primary-btn" onClick={handleLogout} style={{ padding: "8px 12px" }}>
                Выйти
              </button>
            </div>

            {messages.length === 0 && (
              <div className="small">Задайте вопрос по законам РК — чат не виден другим пользователям.</div>
            )}

            {messages.map((msg, idx) => (
              <div key={`${msg.role}-${idx}`} className={`message ${msg.role}`}>
                <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources">
                    <strong>Источники</strong>
                    {msg.sources.map((src, index) => (
                      <div className="source" key={`${src.source}-${index}`}>
                        <div className="source-meta">
                          🔗 {index + 1}. {src.source} {src.code_ru ? `— ${src.code_ru}` : ""}{" "}
                          {src.article_number ? `ст.${src.article_number}` : ""}
                        </div>
                        <div className="source-quote">{src.preview}...</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="chat-input">
            <div className="label">Ваш вопрос</div>
            <textarea
              className="input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Опишите кейс и укажите статьи, если известны"
            />
            {error && <div className="small">{error}</div>}
            <button className="primary-btn" onClick={handleSend} disabled={loading}>
              {loading ? "Отвечаем..." : "Отправить"}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
