// poules.jsx — TV display of group standings (1920×1080)

function Poules({ accent }) {
  const [rotIdx, setRotIdx] = React.useState(0);
  // Auto-rotation indicator (visual only, all groups are visible at once)
  React.useEffect(() => {
    const t = setInterval(() => setRotIdx((i) => (i + 1) % window.POULES.length), 4000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="poules-screen">
      <div className="poules-bg" />
      <header className="poules-header">
        <div className="poules-header-left">
          <div className="tv-tournament-mark" style={{ color: accent }}>
            <svg viewBox="0 0 24 24" width="32" height="32">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.4" />
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.4"/>
            </svg>
          </div>
          <div>
            <div className="poules-title">PHASE DE POULES</div>
            <div className="poules-sub">Simple Homme · 16 joueurs · 4 groupes</div>
          </div>
        </div>
        <div className="poules-header-right">
          <div className="poules-rot">
            {window.POULES.map((_, i) => (
              <i key={i} data-on={i === rotIdx} />
            ))}
            <span>ROTATION AUTO</span>
          </div>
        </div>
      </header>

      <div className="poules-grid">
        {window.POULES.map((p, i) => (
          <PouleCard key={p.id} poule={p} accent={accent} highlight={i === rotIdx} />
        ))}
      </div>

      <footer className="poules-footer">
        <span><i className="poules-foot-dot q" /> Q&nbsp;·&nbsp;Qualifié pour le tableau final</span>
        <span className="poules-foot-meta">
          Mis à jour · <b className="tab">15:42:08</b>
        </span>
      </footer>
    </div>
  );
}

function PouleCard({ poule, accent, highlight }) {
  return (
    <div className={"poule-card " + (highlight ? "hi" : "")}>
      <div className="poule-card-head">
        <span className="poule-card-id" style={{ color: accent }}>{poule.id}</span>
        <span className="poule-card-title">{poule.title}</span>
      </div>

      <div className="poule-card-body">
        <div className="poule-table">
          <div className="poule-row poule-row-head">
            <span>JOUEUR</span>
            <span>V</span>
            <span>D</span>
            <span>JEUX</span>
            <span>PTS</span>
          </div>
          {poule.rows.map((r, i) => (
            <div key={i} className={"poule-row " + (r.q ? "q" : "")}>
              <span className="poule-row-name">
                <em className="poule-rank">{i + 1}</em>
                {r.player}
                {r.q && <i className="poule-q-badge" style={{ background: accent }}>Q</i>}
              </span>
              <span className="tab">{r.v}</span>
              <span className="tab">{r.d}</span>
              <span className="tab poule-jx">{r.jeux}</span>
              <span className="tab poule-pts">{r.pts}</span>
            </div>
          ))}
        </div>

        <div className="poule-cross">
          <div className="poule-cross-lbl">RÉSULTATS</div>
          <div className="poule-cross-grid" style={{ "--accent": accent }}>
            <div className="poule-cross-cell head"></div>
            {poule.rows.map((r, i) => (
              <div key={i} className="poule-cross-cell head">{i + 1}</div>
            ))}
            {poule.grid.map((row, i) => (
              <React.Fragment key={i}>
                <div className="poule-cross-cell rowhead">{i + 1}</div>
                {row.map((c, j) => (
                  <div key={j} className={"poule-cross-cell " + (c === "—" ? "diag" : "")}>{c}</div>
                ))}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Poules });
