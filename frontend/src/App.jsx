import { useEffect, useState } from "react";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "creators", label: "Generate lore wiki days" },
  { id: "mismatches", label: "Timeline Tracking mismatches" },
];

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }
  return payload;
}

function formatRefreshTime(value) {
  if (!value) return "Not refreshed yet";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function hasVod(value) {
  return typeof value === "string" && value.trim() !== "" && value.trim().toUpperCase() !== "UNAVAILABLE";
}

function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [health, setHealth] = useState(null);
  const [overview, setOverview] = useState(null);
  const [creators, setCreators] = useState([]);
  const [mismatches, setMismatches] = useState([]);
  const [selectedCreator, setSelectedCreator] = useState("");
  const [creatorData, setCreatorData] = useState(null);
  const [wiki, setWiki] = useState("");
  const [selectedDay, setSelectedDay] = useState("");
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingCreator, setLoadingCreator] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadData() {
    const [healthData] = await Promise.all([request("/api/health")]);
    setHealth(healthData);
    if (!healthData.data_loaded) return;

    const [overviewData, creatorList, mismatchData] = await Promise.all([
      request("/api/overview"),
      request("/api/creators"),
      request("/api/vod-mismatches"),
    ]);
    setOverview(overviewData);
    setCreators(creatorList);
    setMismatches(mismatchData.mismatches);
  }

  useEffect(() => {
    loadData().catch((requestError) => setError(requestError.message));
  }, []);

  async function refresh() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await request("/api/refresh", { method: "POST" });
      await loadData();
      setNotice("Data refreshed successfully.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function selectCreator(creator) {
    setSelectedCreator(creator);
    setLoadingCreator(true);
    setError("");
    try {
      const [history, wikiData] = await Promise.all([
        request(`/api/creators/${encodeURIComponent(creator)}`),
        request(`/api/creators/${encodeURIComponent(creator)}/wiki`),
      ]);
      setCreatorData(history);
      setWiki(wikiData.wiki);
      setSelectedDay("");
      setSelectedMonths([]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoadingCreator(false);
    }
  }

  async function generateDayTemplate() {
    if (!selectedCreator || !selectedDay) return;

    setError("");
    try {
      const dayData = await request(
        `/api/creators/${encodeURIComponent(selectedCreator)}/days/${encodeURIComponent(selectedDay)}/wiki`,
      );
      setWiki(dayData.wiki);
      setNotice("Single-day template generated.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function generateMonthTemplates() {
    if (!selectedCreator || !selectedMonths.length) return;

    setError("");
    try {
      const monthQuery = encodeURIComponent(selectedMonths.join(","));
      const monthData = await request(
        `/api/creators/${encodeURIComponent(selectedCreator)}/wiki?months=${monthQuery}`,
      );
      setWiki(monthData.wiki);
      setNotice("Selected month templates generated.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function copyWiki() {
    navigator.clipboard.writeText(wiki).then(() => setNotice("Wiki text copied."));
  }

  function downloadWiki() {
    const blob = new Blob([wiki], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedCreator || "creator"}-wiki.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadMismatches() {
    const rows = ["Creator,Date,VOD Title,VOD"];
    mismatches.forEach((item) => {
      rows.push([item.creator, item.calendar_day, item.vod_title || "", item.vod || ""]
        .map((value) => `"${String(value).replaceAll('"', '""')}"`)
        .join(","));
    });
    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "timeline-mismatches.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const filteredCreators = creators.filter((creator) =>
    creator.toLowerCase().includes(search.toLowerCase()),
  );
  const ready = health?.data_loaded;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <span className="brand-mark">CCS</span>
          <div>
            <p className="eyebrow">Wiki desk</p>
            <h1>QSMP 2 Wiki Helper</h1>
          </div>
        </div>
        <nav className="nav-tabs" aria-label="Primary navigation">
          {tabs.map((tab) => (
            <button
              className={activeTab === tab.id ? "nav-tab active" : "nav-tab"}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="nav-index">0{tabs.indexOf(tab) + 1}</span>
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className={ready ? "status-dot online" : "status-dot"} />
          <div>
            <strong>{ready ? "Data loaded" : "Waiting for refresh"}</strong>
            <span>{formatRefreshTime(health?.last_refresh)}</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Content operations</p>
            <h2>{tabs.find((tab) => tab.id === activeTab)?.label}</h2>
          </div>
          <button className="refresh-button" onClick={refresh} disabled={loading}>
            <span className="button-icon">{loading ? "..." : "↻"}</span>
            {loading ? "Refreshing" : "Refresh data"}
          </button>
        </header>

        {error && <div className="alert error-alert">{error}</div>}
        {notice && <div className="alert success-alert">{notice}</div>}

        {!ready && (
          <section className="empty-state hero-empty">
            <span className="empty-kicker">Start here</span>
            <h3>Bring the latest timeline into view.</h3>
            <p>Refresh the connected spreadsheets to populate creator history, wiki previews, and Timeline Tracking mismatches.</p>
            <button className="primary-button" onClick={refresh} disabled={loading}>
              {loading ? "Loading sheets..." : "Load spreadsheet data"}
            </button>
          </section>
        )}

        {ready && activeTab === "overview" && <Overview overview={overview} />}
        {ready && activeTab === "creators" && (
          <CreatorsView
            creators={filteredCreators}
            search={search}
            setSearch={setSearch}
            selectedCreator={selectedCreator}
            selectCreator={selectCreator}
            creatorData={creatorData}
            wiki={wiki}
            selectedDay={selectedDay}
            setSelectedDay={setSelectedDay}
            generateDayTemplate={generateDayTemplate}
            selectedMonths={selectedMonths}
            setSelectedMonths={setSelectedMonths}
            generateMonthTemplates={generateMonthTemplates}
            loadingCreator={loadingCreator}
            copyWiki={copyWiki}
            downloadWiki={downloadWiki}
          />
        )}
        {ready && activeTab === "mismatches" && (
          <MismatchView mismatches={mismatches} downloadMismatches={downloadMismatches} />
        )}
      </main>
    </div>
  );
}

function Overview({ overview }) {
  return (
    <div className="page-grid">
      <section className="intro-panel">
        <div>
          <p className="eyebrow">Workspace pulse</p>
          <h3>Review creator activity and prepare wiki entries.</h3>
          <p className="lede">Spot missing creators in Timeline Tracking spreadsheet, and prepare wiki-ready lore entries from one calm workspace.</p>
        </div>
        <div className="intro-stamp">LIVE<br /><span>sheet sync</span></div>
      </section>
      <section className="overview-lower">
        <article className="sync-panel">
          <p className="eyebrow">Last successful refresh</p>
          <strong>{formatRefreshTime(overview?.last_refresh)}</strong>
          <span>Data is held in the active API session.</span>
        </article>
      </section>
    </div>
  );
}

function CreatorsView({ creators, search, setSearch, selectedCreator, selectCreator, creatorData, wiki, selectedDay, setSelectedDay, generateDayTemplate, selectedMonths, setSelectedMonths, generateMonthTemplates, loadingCreator, copyWiki, downloadWiki }) {
  const availableMonths = creatorData
    ? [...new Set(creatorData.history.map((entry) => entry.wiki_date.split(" ")[0]))]
    : [];
  const visibleHistory = creatorData?.history.filter((entry) => {
    if (!selectedMonths.length) return true;
    return selectedMonths.includes(entry.wiki_date.split(" ")[0]);
  }) || [];

  function toggleMonth(month) {
    setSelectedMonths((currentMonths) => currentMonths.includes(month)
      ? currentMonths.filter((currentMonth) => currentMonth !== month)
      : [...currentMonths, month]);
    setSelectedDay("");
  }

  return (
    <div className="creator-layout">
      <section className="creator-list-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Browse history</p>
            <h3>Creators <span>{creators.length}</span></h3>
          </div>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search creators" aria-label="Search creators" />
        </div>
        <div className="creator-list">
          {creators.map((creator) => (
            <button className={selectedCreator === creator ? "creator-row selected" : "creator-row"} key={creator} onClick={() => selectCreator(creator)}>
              <span className="creator-avatar">{creator.slice(0, 2).toUpperCase()}</span>
              <span>{creator}</span>
              <span className="row-arrow">-&gt;</span>
            </button>
          ))}
          {!creators.length && <p className="muted">No creators match this search.</p>}
        </div>
      </section>
      <section className="detail-panel">
        {!creatorData && !loadingCreator && (
          <div className="empty-state detail-empty"><span className="empty-kicker">Creator workspace</span><h3>Select a creator to inspect their archive.</h3><p>The generated wiki preview will appear beside the timeline.</p></div>
        )}
        {loadingCreator && <div className="loading-state">Loading creator history...</div>}
        {creatorData && !loadingCreator && (
          <>
            <div className="detail-heading">
              <div><p className="eyebrow">Creator history</p><h3>{creatorData.creator}</h3></div>
              <span className="count-badge">{creatorData.history.length} entries</span>
            </div>
            <div className="month-filter-controls">
              <span className="filter-label">Show and generate months</span>
              <div className="month-options">
                {availableMonths.map((month) => (
                  <label className="month-option" key={month}>
                    <input
                      type="checkbox"
                      checked={selectedMonths.includes(month)}
                      onChange={() => toggleMonth(month)}
                    />
                    {month}
                  </label>
                ))}
              </div>
              <button className="secondary-button small" onClick={generateMonthTemplates} disabled={!selectedMonths.length}>
                Generate selected months
              </button>
              {selectedMonths.length > 0 && (
                <button className="text-button" onClick={() => setSelectedMonths([])}>
                  Show all months
                </button>
              )}
            </div>
            <div className="history-list">
              {visibleHistory.map((entry) => {
                const vodLinked = hasVod(entry.vod);
                return (
                <div className="history-row" key={`${entry.calendar_day}-${entry.server_day}`}>
                  <span className="day-number">Server day {entry.server_day}</span>
                  <div><strong>{entry.wiki_date}</strong><span>{vodLinked ? "VOD linked" : "VOD unavailable"}</span></div>
                  {vodLinked ? <a href={entry.vod.trim()} target="_blank" rel="noreferrer">Open VOD</a> : <span>-</span>}
                </div>
                );
              })}
            </div>
            <div className="wiki-panel">
              <div className="detail-heading"><div><p className="eyebrow">Wiki preview</p><h3>Ready to copy</h3></div><div className="button-group"><button className="secondary-button small" onClick={copyWiki}>Copy text</button><button className="secondary-button small" onClick={downloadWiki}>Download</button></div></div>
              <div className="day-template-controls">
                <label htmlFor="day-template-select">Generate one day</label>
                <select id="day-template-select" value={selectedDay} onChange={(event) => setSelectedDay(event.target.value)}>
                  <option value="">Select a day</option>
                  {visibleHistory.map((entry) => (
                    <option key={entry.calendar_day} value={entry.calendar_day}>
                      Day {entry.server_day} - {entry.wiki_date}
                    </option>
                  ))}
                </select>
                <button className="secondary-button small" onClick={generateDayTemplate} disabled={!selectedDay}>
                  Generate day template
                </button>
              </div>
              <textarea value={wiki} readOnly aria-label="Generated wiki text" />
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function MismatchView({ mismatches, downloadMismatches }) {
  return (
    <div className="review-page">
      <section className="review-heading"><div><p className="eyebrow">Data quality</p><h3>Timeline Tracking mismatches queue</h3><p className="lede">Below you can find any mismatches between the Timeline Tracking spreadsheet and the VODs, with VOD links. Orange highlights indicate potential non-QSMP stream.</p></div><button className="secondary-button" onClick={downloadMismatches}>Download CSV</button></section>
      {mismatches.length === 0 ? <div className="empty-state"><span className="empty-kicker">All clear</span><h3>No mismatches found.</h3><p>The activity and VOD sheets are currently aligned.</p></div> : <section className="table-wrap"><div className="table-head"><span>Date</span><span>Creator</span><span>Title</span><span>Link</span></div>{mismatches.map((item, index) => <div className="table-row" key={`${item.creator}-${item.calendar_day}-${index}`}><span className="date-cell">{item.calendar_day}</span><strong>{item.creator}</strong><span className={item.vod_title?.toLowerCase().includes("qsmp") ? "" : "warning-text"}>{item.vod_title || "Untitled VOD"}</span><a href={item.vod} target="_blank" rel="noreferrer">Open VOD</a></div>)}</section>}
    </div>
  );
}

export default App;
