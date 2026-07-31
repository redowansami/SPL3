export default function TopBar({
  targetUrl,
  onTargetUrlChange,
  engine,
  onEngineChange,
  requestTemplateText,
  onRequestTemplateChange,
  responseField,
  onResponseFieldChange,
  requestTimeout,
  onRequestTimeoutChange,
}) {
  return (
    <header className="top-bar">
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
          title="Demo only — not implemented yet"
          onClick={() => onEngineChange("pyrit")}
        >
          PyRIT
        </button>
      </div>
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
