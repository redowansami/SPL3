export default function MitigationModal({ title, loading, error, data, onClose }) {
  return (
    <div className="mitigation-modal-overlay" onClick={onClose}>
      <div className="mitigation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="mitigation-modal-header">
          <h3>Mitigation — {title}</h3>
          <button className="mitigation-modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {loading && <p className="mitigation-modal-status">Loading mitigation data…</p>}
        {error && <p className="mitigation-modal-status mitigation-modal-error">{error}</p>}

        {data && (
          <div className="mitigation-modal-body">
            <div className="mitigation-section">
              <span className="mitigation-section-label">ATLAS Techniques</span>
              <div className="mitigation-badge-row">
                {data.atlas_techniques.map((t) => (
                  <span key={t.id} className="mitigation-technique-badge">
                    {t.id} — {t.name}
                  </span>
                ))}
              </div>
            </div>

            <div className="mitigation-section">
              <span className="mitigation-section-label">ATLAS Mitigations</span>
              <ul className="mitigation-list">
                {data.atlas_mitigations.map((m) => (
                  <li key={m.id} className="mitigation-item">
                    <span className="mitigation-item-title">
                      Follow {m.id} ({m.name})
                    </span>
                    <span className="mitigation-item-desc">{m.description}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mitigation-section">
              <span className="mitigation-section-label">Recommended Strategies</span>
              <ul className="mitigation-list">
                {data.strategies.map((s, i) => (
                  <li key={i} className="mitigation-item mitigation-strategy">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
