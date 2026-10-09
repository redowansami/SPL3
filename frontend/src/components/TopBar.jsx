import { useLocation, useNavigate } from "react-router-dom";

export default function TopBar({
  targetUrl,
  onTargetUrlChange,
  engine,
  onEngineChange,
  requestTemplateText,
  onRequestTemplateChange,
  responseField,
  onResponseFieldChange,
  maxTurns,
  onMaxTurnsChange,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHistory = location.pathname.startsWith("/history");
  const isCustom = location.pathname.startsWith("/custom");

  return (
    <header className="top-bar">
      <button type="button" className="history-button" onClick={() => navigate(isHistory ? "/" : "/history")}>
        {isHistory ? "Back to Scan" : "History"}
      </button>
      <button type="button" className="history-button" onClick={() => navigate(isCustom ? "/" : "/custom")}>
        {isCustom ? "Back to Scan" : "Custom Attack"}
      </button>
      <div className="top-bar-row">
        <label className="top-bar-label" htmlFor="target-url">
          Target URL
        </label>
        <input
          id="target-url"
          className="target-url-input"
          type="text"
          placeholder="https://your-target.example.com/chat"
          value={targetUrl}
          onChange={(e) => onTargetUrlChange(e.target.value)}
        />
      </div>
      <div className="engine-toggle">
        <button
          type="button"
          className={`engine-button ${engine === "garak" ? "active" : ""}`}
          onClick={() => onEngineChange("garak")}
        >
          Garak
        </button>
        <button
          type="button"
          className={`engine-button ${engine === "pyrit" ? "active" : ""}`}
          title="Multi-turn attack driven by PyRIT"
          onClick={() => onEngineChange("pyrit")}
        >
          PyRIT
        </button>
      </div>
      {engine === "pyrit" && (
        <div className="max-turns-field">
          <label className="top-bar-label" htmlFor="max-turns">
            Max turns
          </label>
          <input
            id="max-turns"
            className="max-turns-input"
            type="number"
            min={1}
            max={10}
            value={maxTurns}
            onChange={(e) => onMaxTurnsChange(e.target.value)}
          />
        </div>
      )}
      <details className="advanced-config">
        <summary>Advanced target config</summary>
        <div className="top-bar-row">
          <label className="top-bar-label" htmlFor="request-template">
            Request template (JSON)
          </label>
          <textarea
            id="request-template"
            className="request-template-input"
            placeholder='{"message": "$INPUT"}'
            rows={3}
            value={requestTemplateText}
            onChange={(e) => onRequestTemplateChange(e.target.value)}
          />
        </div>
        <div className="top-bar-row">
          <label className="top-bar-label" htmlFor="response-field">
            Response field
          </label>
          <input
            id="response-field"
            className="response-field-input"
            type="text"
            placeholder="response"
            value={responseField}
            onChange={(e) => onResponseFieldChange(e.target.value)}
          />
        </div>
      </details>
    </header>
  );
}
