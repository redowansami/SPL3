import { useEffect, useRef, useState } from "react";
import "./App.css";
import { fetchProbes, startScan, getScanStatus, cancelScan } from "./api/client";
import TopBar from "./components/TopBar";
import ProbeSidebar from "./components/ProbeSidebar";
import AttackPathPanel from "./components/AttackPathPanel";

const POLL_INTERVAL_MS = 1200;
const POLL_RETRY_DELAY_MS = 1500;
const POLL_MAX_RETRIES = 3;

function App() {
  const [targetUrl, setTargetUrl] = useState("");
  const [engine, setEngine] = useState("garak");
  const [requestTemplateText, setRequestTemplateText] = useState("");
  const [responseField, setResponseField] = useState("");
  const [probes, setProbes] = useState([]);
  const [selectedProbeId, setSelectedProbeId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const pollTimer = useRef(null);

  useEffect(() => {
    fetchProbes()
      .then((data) => {
        setProbes(data);
        if (data.length > 0) {
          setSelectedProbeId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => () => clearTimeout(pollTimer.current), []);

  const canRun =
    engine === "garak" && targetUrl.trim().length > 0 && selectedProbeId && !isRunning;

  const poll = (id, failCount = 0) => {
    getScanStatus(id)
      .then((data) => {
        setElapsed(data.elapsed_seconds);
        if (data.status === "running") {
          pollTimer.current = setTimeout(() => poll(id, 0), POLL_INTERVAL_MS);
          return;
        }
        setResult(data);
        setIsRunning(false);
      })
      .catch((err) => {
        if (failCount < POLL_MAX_RETRIES) {
          pollTimer.current = setTimeout(() => poll(id, failCount + 1), POLL_RETRY_DELAY_MS);
        } else {
          setError(err.message);
          setIsRunning(false);
        }
      });
  };

  const handleRun = async () => {
    setError(null);
    setResult(null);

    let requestTemplate = null;
    if (requestTemplateText.trim()) {
      try {
        requestTemplate = JSON.parse(requestTemplateText);
      } catch {
        setError("Request template must be valid JSON.");
        return;
      }
    }

    setIsRunning(true);
    setElapsed(0);
    try {
      const { run_id } = await startScan({
        targetUrl,
        probeId: selectedProbeId,
        engine,
        requestTemplate,
        responseField,
      });
      setRunId(run_id);
      poll(run_id);
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    clearTimeout(pollTimer.current);
    try {
      const data = await cancelScan(runId);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="app">
      <TopBar
        targetUrl={targetUrl}
        onTargetUrlChange={setTargetUrl}
        engine={engine}
        onEngineChange={setEngine}
        requestTemplateText={requestTemplateText}
        onRequestTemplateChange={setRequestTemplateText}
        responseField={responseField}
        onResponseFieldChange={setResponseField}
      />

      {engine === "pyrit" && (
        <div className="pyrit-banner">PyRIT is a demo placeholder and does not run scans yet.</div>
      )}

      <main className="content-grid">
        <ProbeSidebar
          probes={probes}
          selectedProbeId={selectedProbeId}
          onSelectProbe={setSelectedProbeId}
          onRun={handleRun}
          onStop={handleStop}
          canRun={canRun}
          isRunning={isRunning}
        />
        <AttackPathPanel isRunning={isRunning} error={error} result={result} elapsed={elapsed} />
      </main>
    </div>
  );
}

export default App;
