import { useEffect, useRef, useState } from "react";
type Observation = {
  version: string;
  hostname: string;
  timestamp: string;
  status: string;
};
type Sample = {
  id: number;
  ok: boolean;
  ms: number;
  at: string;
  data?: Observation;
};
const frontendVersion = import.meta.env.VITE_APP_VERSION || "dev";
export default function App() {
  const [running, setRunning] = useState(false);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [counts, setCounts] = useState({ ok: 0, failed: 0 });
  const [versions, setVersions] = useState<Record<string, number>>({});
  const [health, setHealth] = useState({
    live: "Unobserved",
    ready: "Unobserved",
  });
  const sequence = useRef(0);
  useEffect(() => {
    if (!running) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function tick() {
      const start = performance.now();
      let data: Observation | undefined;
      let ok = false;
      try {
        const response = await fetch("/api/version", {
          cache: "no-store",
          signal: AbortSignal.any([
            controller.signal,
            AbortSignal.timeout(5000),
          ]),
        });
        const body = await response.json();
        if (
          typeof body.version !== "string" ||
          typeof body.hostname !== "string" ||
          typeof body.timestamp !== "string" ||
          typeof body.status !== "string"
        )
          throw new Error("Invalid response");
        data = body;
        ok = response.ok;
      } catch {
        /* Network failures count as failed observations. */
      }
      const ms = performance.now() - start;
      if (disposed) return;
      const sample = {
        id: ++sequence.current,
        ok,
        ms,
        at: new Date().toISOString(),
        data,
      };
      setSamples((previous) => [...previous.slice(-59), sample]);
      setCounts((previous) => ({
        ok: previous.ok + Number(ok),
        failed: previous.failed + Number(!ok),
      }));
      if (data)
        setVersions((previous) => ({
          ...previous,
          [data!.version]: (previous[data!.version] || 0) + 1,
        }));
      const statuses = await Promise.all(
        ["/health/live", "/health/ready"].map(async (path) => {
          try {
            const response = await fetch(path, {
              cache: "no-store",
              signal: AbortSignal.any([
                controller.signal,
                AbortSignal.timeout(5000),
              ]),
            });
            const body = await response.json();
            return `${response.status} · ${body.status}`;
          } catch {
            return "Unreachable";
          }
        }),
      );
      if (disposed) return;
      setHealth({ live: statuses[0], ready: statuses[1] });
      timer = setTimeout(tick, 500);
    }
    void tick();
    return () => {
      disposed = true;
      clearTimeout(timer);
      controller.abort();
    };
  }, [running]);
  const latest = samples.at(-1);
  const total = counts.ok + counts.failed;
  const max = Math.max(10, ...samples.map((sample) => sample.ms));
  return (
    <div className="shell">
      <aside>
        <a className="brand" href="#">
          ↗{" "}
          <span>
            rollout<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="workspace">
          WORKSPACE
          <br />
          <strong>Local / Minikube</strong>
        </div>
        <nav>
          <a className="selected" href="#overview">
            ◉ &nbsp; Overview
          </a>
          <a href="#traffic">⌁ &nbsp; Live traffic</a>
          <a href="#versions">▧ &nbsp; Release observations</a>
        </nav>
        <div className="aside-bottom">
          <span className="dot" /> Application observatory
          <br />
          <small>Browser measurements only</small>
        </div>
      </aside>
      <main id="overview">
        <header>
          <span>
            WORKSPACE <b>/</b> DEPLOYMENT OBSERVATORY
          </span>
          <span className="tag">LOCAL ENVIRONMENT</span>
        </header>
        <section className="intro">
          <div>
            <div className="eyebrow">CONTINUITY, MADE VISIBLE</div>
            <h1>Every request counts.</h1>
            <p>
              Watch your application change versions while traffic keeps moving.
            </p>
          </div>
          <button
            aria-label={running ? "Stop traffic" : "Start traffic"}
            className={running ? "stop" : ""}
            onClick={() => setRunning(!running)}
          >
            {running ? "■ Stop traffic" : "▶ Start traffic"}
          </button>
        </section>
        <div className="notice">
          <span className={running ? "dot pulse" : "dot idle"} />
          <strong>
            {running ? "Observing live traffic" : "Ready to observe"}
          </strong>
          <span>
            500 ms between cycles · 5 s request timeout · no automatic retries
          </span>
        </div>
        <section className="stats">
          <article>
            <label>REQUEST SUCCESS</label>
            <strong>
              {total ? `${((counts.ok / total) * 100).toFixed(1)}%` : "—"}
            </strong>
            <small>{total} total API requests</small>
          </article>
          <article>
            <label>SUCCESSFUL</label>
            <strong className="green">{counts.ok}</strong>
            <small>HTTP 2xx responses</small>
          </article>
          <article>
            <label>FAILED</label>
            <strong className={counts.failed ? "red" : ""}>
              {counts.failed}
            </strong>
            <small>HTTP errors or network failures</small>
          </article>
          <article>
            <label>LATEST LATENCY</label>
            <strong>
              {latest ? latest.ms.toFixed(0) : "—"}
              <em> ms</em>
            </strong>
            <small>Measured in this browser</small>
          </article>
        </section>
        <section className="middle">
          <article className="panel" id="traffic">
            <div className="panel-title">
              <h2>Request latency</h2>
              <span>LAST 60 REQUESTS</span>
            </div>
            <div className="chart">
              <div className="axis">{max.toFixed(0)} ms</div>
              {samples.length ? (
                <svg
                  viewBox="0 0 600 150"
                  role="img"
                  aria-label="Measured request latency"
                >
                  <polyline
                    fill="none"
                    stroke="#007f69"
                    strokeWidth="2.5"
                    points={samples
                      .map(
                        (sample, index) =>
                          `${(index * 600) / Math.max(1, samples.length - 1)},${145 - (sample.ms / max) * 130}`,
                      )
                      .join(" ")}
                  />
                  {samples.map((sample, index) => (
                    <circle
                      key={sample.id}
                      cx={(index * 600) / Math.max(1, samples.length - 1)}
                      cy={145 - (sample.ms / max) * 130}
                      r="3"
                      fill={sample.ok ? "#007f69" : "#dc493a"}
                    />
                  ))}
                </svg>
              ) : (
                <div className="empty">
                  Start traffic to see real request measurements.
                </div>
              )}
            </div>
            <footer>
              <span>
                ● Successful &nbsp; <span className="red">● Failed</span>
              </span>
              <span>Older → Newer</span>
            </footer>
          </article>
          <article className="panel health">
            <div className="panel-title">
              <h2>Application signals</h2>
              <span>API</span>
            </div>
            <dl>
              <dt>Liveness</dt>
              <dd>{health.live}</dd>
              <dt>Readiness</dt>
              <dd>{health.ready}</dd>
              <dt>Backend version</dt>
              <dd>{latest?.data?.version || "Unobserved"}</dd>
              <dt>Frontend build</dt>
              <dd>{frontendVersion}</dd>
              <dt>Latest backend pod</dt>
              <dd>{latest?.data?.hostname || "Unobserved"}</dd>
            </dl>
            <p>
              Probes may reach different pods. These observations do not
              describe cluster-wide readiness.
            </p>
          </article>
        </section>
        <section className="panel" id="versions">
          <div className="panel-title">
            <h2>Release observations</h2>
            <span>{Object.keys(versions).length} VERSIONS SEEN</span>
          </div>
          <div className="versions">
            {Object.entries(versions).map(([version, count]) => (
              <div key={version}>
                <span className="version-icon">↗</span>
                <strong>{version}</strong>
                <span>{count} responses</span>
                <div className="bar">
                  <i style={{ width: `${(count / total) * 100}%` }} />
                </div>
              </div>
            ))}
            {!Object.keys(versions).length && (
              <p className="empty">
                Versions will appear as the API responds. No deployment data has
                been inferred.
              </p>
            )}
          </div>
        </section>
        <section className="panel log">
          <div className="panel-title">
            <h2>Request stream</h2>
            <span>MOST RECENT 10</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>STATUS</th>
                  <th>VERSION</th>
                  <th>BACKEND POD</th>
                  <th>LATENCY</th>
                  <th>SERVER TIMESTAMP</th>
                </tr>
              </thead>
              <tbody>
                {samples
                  .slice(-10)
                  .reverse()
                  .map((sample) => (
                    <tr key={sample.id}>
                      <td className={sample.ok ? "green" : "red"}>
                        {sample.ok ? "● Success" : "● Failed"}
                      </td>
                      <td>{sample.data?.version || "—"}</td>
                      <td>{sample.data?.hostname || "—"}</td>
                      <td>{sample.ms.toFixed(1)} ms</td>
                      <td>
                        {sample.data?.timestamp || `No response (${sample.at})`}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
            {!samples.length && (
              <p className="empty">Waiting for your first request.</p>
            )}
          </div>
        </section>
        <div className="page-footer">
          ROLLOUT / ZERO-DOWNTIME LAB
          <span>Session counters reset when this page reloads.</span>
        </div>
      </main>
    </div>
  );
}
