// scoreboard.jsx — TV Live screen with 3 variants
// 1) "classic"  — Broadcast TV overlay (full-width bottom bar)
// 2) "glass"    — Frosted glassmorphism scoreboard
// 3) "editorial"— Minimal type-driven layout

// ── Shared bits ────────────────────────────────────────────────────────────

function ServeBall({ active, size = 18 }) {
  if (!active) return <span className="serve-ball-spacer" style={{ width: size, height: size }} />;
  return (
    <span className="serve-ball" style={{ width: size, height: size }} aria-label="au service">
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="#E8F35A" />
        <path d="M2.5 12c4-1 8.5-1 12.5 3 1.5 1.5 4.5 2.5 6.5 2.5M2.5 12c4 1 8.5 1 12.5-3 1.5-1.5 4.5-2.5 6.5-2.5"
              fill="none" stroke="rgba(0,0,0,0.5)" strokeWidth="0.8" />
      </svg>
    </span>
  );
}

function CourtBackdrop({ children }) {
  return (
    <div className="court-bg">
      <div className="court-vignette" />
      {children}
    </div>
  );
}

function TopChrome({ tournament = "OPEN DE MOUTILLOUX", edition = "ÉDITION 2026" }) {
  return (
    <div className="tv-top-left">
      <div className="tv-tournament">
        <div className="tv-tournament-mark">
          <svg viewBox="0 0 24 24" width="36" height="36">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.4"/>
          </svg>
        </div>
        <div>
          <div className="tv-tournament-name">{tournament}</div>
          <div className="tv-tournament-sub">{edition}</div>
        </div>
      </div>
    </div>
  );
}

// "Joueurs à préparer" panel — displayed during a live match to call up the next players
function PrepPanel({ accent, players = ["CYRILLE", "SEB.LEC"], stage = "Demi-finale 2", court = "Court 2", time = "15:00", call = "Présentez-vous au juge-arbitre" }) {
  return (
    <div className="tv-prep" style={{ "--accent": accent }}>
      <div className="tv-prep-bar" />
      <div className="tv-prep-head">
        <span className="tv-prep-lbl">À PRÉPARER · {time}</span>
        <span className="tv-prep-stage">{stage}</span>
      </div>
      <div className="tv-prep-players">
        {players.map((p, i) => (
          <React.Fragment key={p}>
            <div className="tv-prep-player">
              <div className="tv-prep-avatar" style={{ background: i === 0 ? accent : "rgba(255,255,255,0.12)", color: i === 0 ? "#001215" : "var(--ink-0)" }}>
                {p.slice(0, 2)}
              </div>
              <span className="tv-prep-name">{p}</span>
            </div>
            {i === 0 && <em className="tv-prep-vs">vs</em>}
          </React.Fragment>
        ))}
      </div>
      <div className="tv-prep-foot">
        <span className="tv-prep-court">{court}</span>
        <span className="tv-prep-call">
          <i className="tv-prep-call-dot" />
          {call}
        </span>
      </div>
    </div>
  );
}

// ── Variant 1: CLASSIC broadcast bar ───────────────────────────────────────
function ScoreboardClassic({ m, accent, demoOn }) {
  const sets = m.sets;
  return (
    <CourtBackdrop>
      <TopChrome />
      <PrepPanel accent={accent} />

      <div className="sb-classic">
        <div className="sb-classic-title">
          <i className="sb-classic-live"><span /> EN DIRECT</i>
          <span className="sb-classic-cat">{m.category}</span>
          <span className="sb-classic-format">1 SET · 5 JEUX · TB&nbsp;4</span>
        </div>

        <div className="sb-classic-grid">
          <div className="sb-classic-side" data-leading={m.curGamesA > m.curGamesB}>
            <i className="sb-classic-bar" style={{ background: accent }} />
            <div className="sb-classic-flag">FR</div>
            <div className="sb-classic-name">
              <ServeBall active={m.serving === "A"} size={20} />
              <span>{m.players.A.name.toUpperCase()}</span>
              <em className="sb-classic-seed">[{m.players.A.seed}]</em>
            </div>
            <div className="sb-classic-sets">
              {[0, 1].map((i) => (
                <span key={i} className={"sb-set " + (sets[i]?.a > (sets[i]?.b ?? 0) ? "win" : "")}>
                  {sets[i]?.a ?? "—"}
                </span>
              ))}
            </div>
            <div className="sb-classic-games tab">{m.curGamesA}</div>
            <div className="sb-classic-pts tab">{window.pointLabel(m.ptsA, m.ptsB, m.inTB)}</div>
          </div>

          <div className="sb-classic-divider" />

          <div className="sb-classic-side" data-leading={m.curGamesB > m.curGamesA}>
            <i className="sb-classic-bar" style={{ background: "#ffffff" }} />
            <div className="sb-classic-flag">FR</div>
            <div className="sb-classic-name">
              <ServeBall active={m.serving === "B"} size={20} />
              <span>{m.players.B.name.toUpperCase()}</span>
              <em className="sb-classic-seed">[{m.players.B.seed}]</em>
            </div>
            <div className="sb-classic-sets">
              {[0, 1].map((i) => (
                <span key={i} className={"sb-set " + (sets[i]?.b > (sets[i]?.a ?? 0) ? "win" : "")}>
                  {sets[i]?.b ?? "—"}
                </span>
              ))}
            </div>
            <div className="sb-classic-games tab">{m.curGamesB}</div>
            <div className="sb-classic-pts tab">{window.pointLabel(m.ptsB, m.ptsA, m.inTB)}</div>
          </div>
        </div>

        <div className="sb-classic-footer">
          <div className="sb-foot-col">
            <span className="sb-foot-lbl">COURT</span>
            <span className="sb-foot-val">CENTRAL</span>
          </div>
          <div className="sb-foot-col">
            <span className="sb-foot-lbl">DURÉE</span>
            <span className="sb-foot-val tab">00:42</span>
          </div>
          <div className="sb-foot-col">
            <span className="sb-foot-lbl">ACES</span>
            <span className="sb-foot-val tab">4 · 2</span>
          </div>
          <div className="sb-foot-col">
            <span className="sb-foot-lbl">% 1<sup>RE</sup></span>
            <span className="sb-foot-val tab">68% · 71%</span>
          </div>
          <div className="sb-foot-col" style={{ marginLeft: "auto" }}>
            <span className="sb-foot-lbl" style={{ color: accent }}>{m.inTB ? "JEU DÉCISIF" : (demoOn ? "MODE DÉMO" : "AU SERVICE")}</span>
            <span className="sb-foot-val">{m.serving === "A" ? m.players.A.name : m.players.B.name}</span>
          </div>
        </div>
      </div>
    </CourtBackdrop>
  );
}

// ── Variant 2: GLASSMORPHISM ───────────────────────────────────────────────
function ScoreboardGlass({ m, accent }) {
  const sets = m.sets;
  return (
    <CourtBackdrop>
      <TopChrome />
      <PrepPanel accent={accent} />

      <div className="sb-glass">
        <div className="sb-glass-card">
          <div className="sb-glass-head">
            <div className="sb-glass-cat">
              <i className="sb-glass-live"><span /> EN DIRECT</i>
              {m.category}
            </div>
            <div className="sb-glass-meta">CENTRAL · 1 SET · 5 JEUX · TB&nbsp;4</div>
          </div>

          <div className="sb-glass-cols">
            <div className="sb-glass-cols-head">
              <span />
              <span>JOUEUR</span>
              <span>SET&nbsp;1</span>
              <span>JEU</span>
              <span>POINT</span>
            </div>

            <div className="sb-glass-row" data-leading={m.curGamesA > m.curGamesB}>
              <ServeBall active={m.serving === "A"} size={22} />
              <div className="sb-glass-name">
                <span>{m.players.A.name}</span>
                <em>[{m.players.A.seed}]</em>
              </div>
              <span className={"sb-glass-set tab " + (sets[0]?.a > (sets[0]?.b ?? 0) ? "win" : "")}>{sets[0]?.a ?? "—"}</span>
              <span className="sb-glass-game tab">{m.curGamesA}</span>
              <span className="sb-glass-pts tab" style={{ color: accent }}>
                {window.pointLabel(m.ptsA, m.ptsB, m.inTB)}
              </span>
            </div>

            <div className="sb-glass-rule" />

            <div className="sb-glass-row" data-leading={m.curGamesB > m.curGamesA}>
              <ServeBall active={m.serving === "B"} size={22} />
              <div className="sb-glass-name">
                <span>{m.players.B.name}</span>
                <em>[{m.players.B.seed}]</em>
              </div>
              <span className={"sb-glass-set tab " + (sets[0]?.b > (sets[0]?.a ?? 0) ? "win" : "")}>{sets[0]?.b ?? "—"}</span>
              <span className="sb-glass-game tab">{m.curGamesB}</span>
              <span className="sb-glass-pts tab" style={{ color: accent }}>
                {window.pointLabel(m.ptsB, m.ptsA, m.inTB)}
              </span>
            </div>
          </div>

          <div className="sb-glass-foot">
            <span>{m.inTB ? "JEU DÉCISIF EN COURS" : "AU SERVICE"}&nbsp;·&nbsp;<b>{m.serving === "A" ? m.players.A.name : m.players.B.name}</b></span>
            <span className="tab">00:42</span>
          </div>
        </div>
      </div>
    </CourtBackdrop>
  );
}

// ── Variant 3: EDITORIAL minimal ──────────────────────────────────────────
function ScoreboardEditorial({ m, accent }) {
  const sets = m.sets;
  return (
    <CourtBackdrop>
      <div className="sb-ed-top">
        <div className="sb-ed-tournament">
          <div className="sb-ed-tournament-name">OPEN DE MOUTILLOUX</div>
          <div className="sb-ed-tournament-sub">ÉDITION&nbsp;2026 · 25.05 — 02.06</div>
        </div>
        <div className="sb-ed-cat">
          <span>{m.category.toUpperCase()}</span>
          <em style={{ color: accent }}>EN DIRECT</em>
        </div>
        <div className="sb-ed-next">
          <span className="sb-ed-next-lbl">SUIVANT 15:30</span>
          <span>CYRILLE&nbsp;·&nbsp;MARC</span>
        </div>
      </div>

      <div className="sb-ed-numbers">
        <div className="sb-ed-num tab" style={{ color: accent }}>{m.curGamesA}</div>
        <div className="sb-ed-num-sep">—</div>
        <div className="sb-ed-num tab">{m.curGamesB}</div>
      </div>
      <div className="sb-ed-label">JEUX · SET 1</div>

      <div className="sb-ed-bottom">
        <div className="sb-ed-line">
          <ServeBall active={m.serving === "A"} size={26} />
          <span className="sb-ed-name">{m.players.A.name}</span>
          <span className="sb-ed-seed">[{m.players.A.seed}]</span>
          <span className="sb-ed-rule" />
          <span className="sb-ed-pts tab">{window.pointLabel(m.ptsA, m.ptsB, m.inTB)}</span>
          <span className="sb-ed-mini">SETS&nbsp;<b className="tab">{sets[0]?.a ?? 0}</b></span>
        </div>
        <div className="sb-ed-line">
          <ServeBall active={m.serving === "B"} size={26} />
          <span className="sb-ed-name">{m.players.B.name}</span>
          <span className="sb-ed-seed">[{m.players.B.seed}]</span>
          <span className="sb-ed-rule" />
          <span className="sb-ed-pts tab">{window.pointLabel(m.ptsB, m.ptsA, m.inTB)}</span>
          <span className="sb-ed-mini">SETS&nbsp;<b className="tab">{sets[0]?.b ?? 0}</b></span>
        </div>
      </div>
    </CourtBackdrop>
  );
}

// ── Switcher ───────────────────────────────────────────────────────────────
function Scoreboard({ match, variant, accent, demoOn }) {
  if (variant === "glass")     return <ScoreboardGlass m={match} accent={accent} />;
  if (variant === "editorial") return <ScoreboardEditorial m={match} accent={accent} />;
  return <ScoreboardClassic m={match} accent={accent} demoOn={demoOn} />;
}

Object.assign(window, { Scoreboard });
