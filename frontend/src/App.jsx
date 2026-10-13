import { useEffect, useRef, useState } from "react";
import { Route, Routes } from "react-router-dom";
import "./App.css";
import {
  fetchProbes,
  startScan,
  getScanStatus,
  cancelScan,
  fetchObjectives,
  startPyritScan,
  getPyritScanStatus,
  cancelPyritScan,
} from "./api/client";
import TopBar from "./components/TopBar";
import ProbeSidebar from "./components/ProbeSidebar";
import AttackPathPanel from "./components/AttackPathPanel";
import PyritResultPanel from "./components/PyritResultPanel";
import ScanHistoryPanel from "./components/ScanHistoryPanel";
import ScanHistoryDetail from "./components/ScanHistoryDetail";
import CustomAttackPage from "./components/CustomAttackPage";

const POLL_INTERVAL_MS = 1200;
const POLL_RETRY_DELAY_MS = 1500;
const POLL_MAX_RETRIES = 3;

function App() {
  const [targetUrl, setTargetUrl] = useState("");
  const [engine, setEngine] = useState("garak");
  const [requestTemplateText, setRequestTemplateText] = useState("");
  const [responseField, setResponseField] = useState("");
  const [authHeadersText, setAuthHeadersText] = useState("");
  const [maxTurns, setMaxTurns] = useState("5");
  const [probes, setProbes] = useState([]);
  const [selectedProbeId, setSelectedProbeId] = useState(null);
  const [objectives, setObjectives] = useState([]);
  const [selectedObjectiveId, setSelectedObjectiveId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [runStartedAt, setRunStartedAt] = useState(null);
  const [runEndedAt, setRunEndedAt] = useState(null);

  const pollTimer = useRef(null);
  // The engine the in-flight run was started with, so STOP / result rendering
  // can't be mis-routed if the user toggles the engine mid-run.
  const runEngine = useRef(engine);

  useEffect(() => {
    fetchProbes()
      .then((data) => {
        setProbes(data);
        if (data.length > 0) {
          setSelectedProbeId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));

    fetchObjectives()
      .then((data) => {
        setObjectives(data);
        if (data.length > 0) {
          setSelectedObjectiveId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => () => clearTimeout(pollTimer.current), []);

  const canRun =
    targetUrl.trim().length > 0 &&
    !isRunning &&
    (engine === "garak" ? Boolean(selectedProbeId) : Boolean(selectedObjectiveId));

  const poll = (id, statusFn, failCount = 0) => {
    statusFn(id)
      .then((data) => {
        setElapsed(data.elapsed_seconds);
        if (data.status === "running") {
          pollTimer.current = setTimeout(() => poll(id, statusFn, 0), POLL_INTERVAL_MS);
          return;
        }
        setResult(data);
        setRunEndedAt(new Date());
        setIsRunning(false);
      })
      .catch((err) => {
        if (failCount < POLL_MAX_RETRIES) {
          pollTimer.current = setTimeout(() => poll(id, statusFn, failCount + 1), POLL_RETRY_DELAY_MS);
        } else {
          setError(err.message);
          setIsRunning(false);
        }
      });
  };

  const handleRun = async () => {
    setError(null);
    setResult(null);
    setRunStartedAt(new Date());
    setRunEndedAt(null);

    let requestTemplate = null;
    if (requestTemplateText.trim()) {
      try {
        requestTemplate = JSON.parse(requestTemplateText);
      } catch {
        setError("Request template must be valid JSON.");
        return;
      }
    }

    let authHeaders = null;
    if (authHeadersText.trim()) {
      try {
        authHeaders = JSON.parse(authHeadersText);
      } catch {
        setError("Auth headers must be valid JSON.");
        return;
      }
    }

    runEngine.current = engine;
    setIsRunning(true);
    setElapsed(0);
    try {
      if (engine === "garak") {
        const { run_id } = await startScan({
          targetUrl,
          probeId: selectedProbeId,
          engine,
          requestTemplate,
          responseField,
          authHeaders,
        });
        setRunId(run_id);
        poll(run_id, getScanStatus);
      } else {
        const { run_id } = await startPyritScan({
          targetUrl,
          objectiveId: selectedObjectiveId,
          maxTurns: maxTurns.trim() ? Number(maxTurns) : null,
          requestTemplate,
          responseField,
          authHeaders,
        });
        setRunId(run_id);
        poll(run_id, getPyritScanStatus);
      }
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    clearTimeout(pollTimer.current);
    try {
      const cancel = runEngine.current === "garak" ? cancelScan : cancelPyritScan;
      const data = await cancel(runId);
      setResult(data);
      setRunEndedAt(new Date());
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
        authHeadersText={authHeadersText}
        onAuthHeadersChange={setAuthHeadersText}
        maxTurns={maxTurns}
        onMaxTurnsChange={setMaxTurns}
      />

      <main className="content-grid">
        <Routes>
          <Route
            path="/"
            element={
              <>
                {engine === "garak" ? (
                  <ProbeSidebar
                    heading="Probes"
                    items={probes}
                    selectedId={selectedProbeId}
                    onSelect={setSelectedProbeId}
                    onRun={handleRun}
                    onStop={handleStop}
                    canRun={canRun}
                    isRunning={isRunning}
                  />
                ) : (
                  <ProbeSidebar
                    heading="Objectives"
                    items={objectives}
                    selectedId={selectedObjectiveId}
                    onSelect={setSelectedObjectiveId}
                    onRun={handleRun}
                    onStop={handleStop}
                    canRun={canRun}
                    isRunning={isRunning}
                  />
                )}

                {/* While a run is active or showing a result, follow the engine that ran;
                    otherwise follow the current toggle so the empty state matches. */}
                {(isRunning || result ? runEngine.current : engine) === "garak" ? (
                  <AttackPathPanel
                    isRunning={isRunning}
                    error={error}
                    result={result}
                    elapsed={elapsed}
                    meta={
                      result && {
                        targetUrl,
                        engine: "garak",
                        runId,
                        startedAt: runStartedAt,
                        endedAt: runEndedAt,
                      }
                    }
                  />
                ) : (
                  <PyritResultPanel
                    isRunning={isRunning}
                    error={error}
                    result={result}
                    elapsed={elapsed}
                    meta={
                      result && {
                        targetUrl,
                        engine: "pyrit",
                        runId,
                        startedAt: runStartedAt,
                        endedAt: runEndedAt,
                      }
                    }
                  />
                )}
              </>
            }
          />
          <Route path="/history" element={<ScanHistoryPanel />} />
          <Route path="/history/:runId" element={<ScanHistoryDetail />} />
          <Route
            path="/custom"
            element={<CustomAttackPage targetUrl={targetUrl} authHeadersText={authHeadersText} />}
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
