import { useRef, useState } from "react";

import { evaluateCustomAttack, sendCustomChat } from "../api/client";
import EvaluateAttackModal from "./EvaluateAttackModal";

export default function CustomAttackPage({ targetUrl }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [showEvaluate, setShowEvaluate] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  function resetInputHeight() {
    if (inputRef.current) inputRef.current.style.height = "auto";
  }

  function handleInputChange(e) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }

  async function handleSend() {
    const message = input.trim();
    if (!message || sending) return;
    if (!targetUrl.trim()) {
      setError("Set a target URL above before chatting.");
      return;
    }

    setError(null);
    setSending(true);
    setMessages((prev) => [...prev, { role: "attacker", text: message }]);
    setInput("");
    resetInputHeight();

    try {
      const { reply } = await sendCustomChat({ targetUrl, message });
      setMessages((prev) => [...prev, { role: "target", text: reply }]);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleEvaluate(objective) {
    return evaluateCustomAttack({
      targetUrl,
      objective,
      conversation: messages,
    });
  }

  return (
    <section className="custom-attack-page attack-path-panel">
      <div className="results-summary-head">
        <h2>Custom Attack</h2>
        <button
          type="button"
          className="mitigation-button"
          disabled={messages.length === 0}
          onClick={() => setShowEvaluate(true)}
        >
          Evaluate attack now
        </button>
      </div>

      <div className="custom-attack-chat">
        {messages.length === 0 ? (
          <p className="no-failures" style={{ color: "var(--text)" }}>
            Send a message below to start chatting with the target.
          </p>
        ) : (
          <div className="chat-thread">
            {messages.map((turn, idx) => (
              <div key={idx} className={`chat-row ${turn.role === "attacker" ? "chat-row-user" : "chat-row-target"}`}>
                <div className={`chat-bubble ${turn.role === "attacker" ? "chat-bubble-user" : "chat-bubble-target"}`}>
                  {turn.text}
                </div>
              </div>
            ))}
            {sending && (
              <div className="chat-row chat-row-target">
                <div className="chat-bubble chat-bubble-target chat-bubble-typing">Target is typing…</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {error && <p className="mitigation-modal-error" style={{ marginTop: 12 }}>{error}</p>}

      <div className="custom-attack-composer">
        <textarea
          ref={inputRef}
          className="custom-attack-input"
          rows={1}
          placeholder="Type a message to send to the target…"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <button
          type="button"
          className="run-button custom-attack-send"
          disabled={!input.trim() || sending}
          onClick={handleSend}
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </div>

      {showEvaluate && (
        <EvaluateAttackModal onEvaluate={handleEvaluate} onClose={() => setShowEvaluate(false)} />
      )}
    </section>
  );
}
