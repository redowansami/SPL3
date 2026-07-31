export default function ProbeSidebar({
  probes,
  selectedProbeId,
  onSelectProbe,
  onRun,
  onStop,
  canRun,
  isRunning,
}) {
  return (
    <aside className="probe-sidebar">
      <h2 className="sidebar-heading">Probes</h2>
      <div className="probe-list">
        {probes.map((probe) => (
          <button
            key={probe.id}
            type="button"
            className={`probe-button ${selectedProbeId === probe.id ? "active" : ""}`}
            title={probe.description}
            onClick={() => onSelectProbe(probe.id)}
          >
            {probe.label}
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
