export default function ProbeSidebar({
  items,
  selectedId,
  onSelect,
  onRun,
  onStop,
  canRun,
  isRunning,
  heading = "Probes",
}) {
  return (
    <aside className="probe-sidebar">
      <h2 className="sidebar-heading">{heading}</h2>
      <div className="probe-list">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`probe-button ${selectedId === item.id ? "active" : ""}`}
            title={item.description}
            onClick={() => onSelect(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {isRunning ? (
        <button type="button" className="stop-button" onClick={onStop}>
          STOP
        </button>
      ) : (
        <button type="button" className="run-button" onClick={onRun} disabled={!canRun}>
          RUN
        </button>
      )}
    </aside>
  );
}
