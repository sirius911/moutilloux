// extras.jsx — Login, Arbitre selection (home), Admin Tournoi tab, TV idle

// ── 1) Login (1440×900, light) ─────────────────────────────────────────────
function LoginScreen({ accent }) {
  const [role, setRole] = React.useState(null);
  const ROLES = {
    admin:   { email: "marie@moutilloux.fr",   label: "Organisateur", sub: "Administration du tournoi" },
    arbitre: { email: "arbitre@moutilloux.fr", label: "Arbitre",      sub: "Saisie des scores" },
  };
  return (
    <div className="lgn light-scope">
      <div className="lgn-bg" />
      <div className="lgn-wrap">
        <div className="lgn-card">
          <div className="lgn-brand">
            <div className="lgn-mark" style={{ background: accent, color: "#001215" }}>
              <svg viewBox="0 0 24 24" width="22" height="22">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.6"/>
                <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.6"/>
              </svg>
            </div>
            <div>
              <div className="lgn-tournament">OPEN DE MOUTILLOUX</div>
              <div className="lgn-edition">Édition 2026 · 25.05 → 02.06</div>
            </div>
          </div>

          <h1 className="lgn-title">Connexion</h1>
          <p className="lgn-sub">Sélectionnez le compte assigné à cet appareil</p>

          <div className="lgn-roles">
            {Object.entries(ROLES).map(([id, r]) => (
              <button key={id}
                className={"lgn-role-card " + (role === id ? "on" : "")}
                onClick={() => setRole(id)}
                style={role === id ? { borderColor: accent, background: "rgba(255,200,61,0.08)" } : {}}>
                <div className="lgn-role-card-icon" style={role === id ? { background: accent, color: "#001215" } : {}}>
                  {id === "admin"
                    ? <svg viewBox="0 0 24 24" width="22" height="22"><rect x="3" y="4" width="18" height="14" rx="2" fill="none" stroke="currentColor" strokeWidth="1.6"/><path d="M3 9h18M8 14h3M8 17h2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
                    : <svg viewBox="0 0 24 24" width="22" height="22"><rect x="6" y="3" width="12" height="18" rx="2" fill="none" stroke="currentColor" strokeWidth="1.6"/><circle cx="12" cy="18" r="0.8" fill="currentColor"/><path d="M9 6h6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>}
                </div>
                <div className="lgn-role-card-text">
                  <div className="lgn-role-card-lbl">{r.label}</div>
                  <div className="lgn-role-card-sub">{r.sub}</div>
                </div>
                <i className="lgn-role-card-check" style={role === id ? { borderColor: accent, background: accent } : {}}>
                  {role === id && <svg viewBox="0 0 16 16" width="10" height="10"><path d="M3 8l3 3 7-7" fill="none" stroke="#001215" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                </i>
              </button>
            ))}
          </div>

          <div className={"lgn-form " + (role ? "shown" : "")}>
            <Field label="Mot de passe">
              <input className="inp" type="password" defaultValue="••••••••••" autoFocus={!!role} />
            </Field>
            <div className="lgn-form-meta">
              <span className="adm-mono">{role ? ROLES[role].email : "—"}</span>
              <label className="sw"><input type="checkbox" defaultChecked /><i style={{ "--accent": accent }} /><span>Rester connecté</span></label>
            </div>
            <button className="lgn-submit" style={{ background: accent, opacity: role ? 1 : 0.5 }} disabled={!role}>
              Se connecter en tant que {role ? ROLES[role].label.toLowerCase() : "…"}
              <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>

          <div className="lgn-divider"><span>OU</span></div>

          <button className="lgn-kiosk">
            <i className="lgn-kiosk-dot" />
            En direct
            <span className="lgn-kiosk-sub">accès libre · TV, poules, tableau final</span>
          </button>
        </div>

        <aside className="lgn-side">
          <div className="lgn-side-mark">
            <svg viewBox="0 0 24 24" width="56" height="56" style={{ color: accent }}>
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.4"/>
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.4"/>
            </svg>
          </div>
          <div className="lgn-side-quote">
            <em>«</em>
            Le tournoi du village, géré au cordeau.
            <em>»</em>
          </div>
          <div className="lgn-side-stats">
            <div><b className="tab">48</b><span>joueurs inscrits</span></div>
            <div><b className="tab">4</b><span>épreuves</span></div>
            <div><b className="tab">86</b><span>matchs prévus</span></div>
          </div>
          <div className="lgn-side-foot">
            <span><i className="lgn-side-dot" /> Serveur en ligne · raspberrypi.local</span>
            <span>v1.4.2</span>
          </div>
        </aside>
      </div>
    </div>
  );
}

// ── 2) Arbitre — sélection du match (iPad 834×1112) ─────────────────────────
function ArbitreHome({ accent }) {
  const [filter, setFilter] = React.useState("all");
  const all = window.ARB_MATCHES;
  const list = filter === "all" ? all : filter === "live" ? all.filter((m) => m.status === "LIVE")
              : filter === "soon" ? all.filter((m) => m.status === "SCHEDULED")
              : all.filter((m) => m.status === "FINISHED");

  return (
    <div className="arh">
      <div className="arh-bg" />
      <header className="arh-header">
        <div className="arh-greeting">
          <div className="arh-greeting-hi">Bonjour Pierre,</div>
          <div className="arh-greeting-sub">Vous êtes l'arbitre désigné · {all.filter(m => m.status==="LIVE").length} match en cours</div>
        </div>
        <button className="arh-logout">
          <svg viewBox="0 0 24 24" width="16" height="16"><path d="M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3M10 17l5-5-5-5M3 12h12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      </header>

      <div className="arh-tabs">
        {[
          { id: "all",  label: "Tous",      count: all.length },
          { id: "live", label: "En direct", count: all.filter(m => m.status==="LIVE").length, hot: true },
          { id: "soon", label: "À venir",   count: all.filter(m => m.status==="SCHEDULED").length },
          { id: "done", label: "Terminés",  count: all.filter(m => m.status==="FINISHED").length },
        ].map((t) => (
          <button key={t.id}
            className={"arh-tab " + (filter === t.id ? "on" : "")}
            style={filter === t.id ? { background: accent, color: "#001215" } : {}}
            onClick={() => setFilter(t.id)}>
            {t.hot && <span className="arh-tab-hot" />}
            {t.label}
            <em className="tab">{t.count}</em>
          </button>
        ))}
      </div>

      <div className="arh-list">
        {list.map((m) => (
          <button key={m.id} className={"arh-match arh-match-" + m.status.toLowerCase()}>
            <div className="arh-match-stripe" style={{ background: m.status === "LIVE" ? accent : m.status === "FINISHED" ? "var(--ink-4)" : "var(--ink-3)" }} />
            <div className="arh-match-top">
              <span className={"arh-match-status " + m.status.toLowerCase()}>
                {m.status === "LIVE" && <i />}
                {m.status === "LIVE" ? "EN DIRECT" : m.status === "FINISHED" ? "TERMINÉ" : "PRÉVU"}
              </span>
              <span className="arh-match-time tab">{m.time}</span>
              <span className="arh-match-court">{m.court}</span>
            </div>
            <div className="arh-match-players">
              <span>{m.a}</span>
              <em>vs</em>
              <span>{m.b}</span>
            </div>
            <div className="arh-match-bottom">
              <span className="arh-match-event">{m.event} · {m.stage}</span>
              {m.score && <span className="arh-match-score tab" style={m.status === "LIVE" ? { color: accent } : {}}>{m.score}</span>}
              <span className="arh-match-go">
                {m.status === "LIVE" ? "Reprendre" : m.status === "FINISHED" ? "Voir" : "Démarrer"}
                <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14m0 0l-5-5m5 5l-5 5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </span>
            </div>
          </button>
        ))}
      </div>

      <footer className="arh-foot">
        <i className="lgn-side-dot" /> Synchronisé · 15:42:08
      </footer>
    </div>
  );
}

// ── 3) Admin — Tournoi (éditions + épreuves) ────────────────────────────────
function AdminTournoi({ accent }) {
  return (
    <div className="adm-tournoi">
      <section className="adm-card adm-edition-card">
        <div className="adm-card-head">
          <h3><span className="adm-edition-dot" style={{ background: accent }} /> Édition active · Open de Moutilloux 2026</h3>
          <em className="adm-card-count">25 mai → 02 juin 2026</em>
        </div>
        <div className="adm-edition-body">
          <div className="adm-edition-stats">
            <div className="adm-stat">
              <span className="adm-stat-lbl">Joueurs inscrits</span>
              <span className="adm-stat-val tab">48</span>
              <span className="adm-stat-delta">+3 cette semaine</span>
            </div>
            <div className="adm-stat">
              <span className="adm-stat-lbl">Épreuves</span>
              <span className="adm-stat-val tab">4</span>
              <span className="adm-stat-delta">2 en phase finale</span>
            </div>
            <div className="adm-stat">
              <span className="adm-stat-lbl">Matchs joués</span>
              <span className="adm-stat-val tab">42<em>/86</em></span>
              <span className="adm-stat-delta">~3 jours restants</span>
            </div>
            <div className="adm-stat">
              <span className="adm-stat-lbl">Courts ouverts</span>
              <span className="adm-stat-val tab">5</span>
              <span className="adm-stat-delta">Central · 2 · 3 · 4 · Terre</span>
            </div>
          </div>

          <div className="adm-edition-meta">
            <div className="adm-edition-meta-row">
              <span>Lieu</span>
              <b>TC Moutilloux · 3 chemin des Tilleuls</b>
            </div>
            <div className="adm-edition-meta-row">
              <span>Directeur de tournoi</span>
              <b>Marie Lavoix</b>
            </div>
            <div className="adm-edition-meta-row">
              <span>Juge-arbitre principal</span>
              <b>Pierre Garnier</b>
            </div>
            <div className="adm-edition-meta-row">
              <span>Sauvegarde locale</span>
              <b className="adm-mono">raspberrypi.local · auto · 15:42</b>
            </div>
          </div>
        </div>
      </section>

      <section className="adm-card">
        <div className="adm-card-head">
          <h3>Épreuves de l'édition</h3>
          <button className="adm-btn primary" style={{ background: accent }}>+ Nouvelle épreuve</button>
        </div>
        <div className="adm-events">
          {window.EVENTS.map((ev) => (
            <article key={ev.id} className="adm-event">
              <div className="adm-event-head">
                <span className="adm-event-mode" style={{ background: ev.color, color: "#001215" }}>{ev.mode}</span>
                <div className="adm-event-name">
                  <h4>{ev.name}</h4>
                  <span>{ev.category} · {ev.mode === "S" ? "Simple" : "Double"}</span>
                </div>
                <button className="adm-row-act" aria-label="Plus">
                  <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/></svg>
                </button>
              </div>
              <div className="adm-event-stats">
                <span><em>{ev.players}</em> joueurs</span>
                <span className="adm-event-status">{ev.status}</span>
              </div>
              <div className="adm-event-prog">
                <div className="adm-event-prog-bar" style={{ width: ev.progress + "%", background: ev.color }} />
              </div>
              <div className="adm-event-acts">
                <button className="adm-btn">Joueurs</button>
                <button className="adm-btn">Poules</button>
                <button className="adm-btn">Matchs</button>
                <button className="adm-btn" style={{ marginLeft: "auto" }}>Activer</button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="adm-card">
        <div className="adm-card-head">
          <h3>Historique des éditions</h3>
          <button className="adm-btn">+ Nouvelle édition</button>
        </div>
        <table className="adm-table">
          <thead>
            <tr>
              <th>Édition</th>
              <th>Dates</th>
              <th>Épreuves</th>
              <th>Joueurs</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {window.EDITIONS.map((e) => (
              <tr key={e.id}>
                <td>
                  <div className="adm-player">
                    <div className="adm-avatar" style={{ background: e.active ? accent : "var(--bg-4)", color: e.active ? "#001215" : "var(--ink-2)" }}>
                      {String(e.year).slice(2)}
                    </div>
                    <div>
                      <div className="adm-player-name">{e.name}</div>
                      <div className="adm-player-meta">{e.active ? "Édition active" : "Archive"}</div>
                    </div>
                  </div>
                </td>
                <td className="adm-mono">{e.start} → {e.end}</td>
                <td className="tab">{e.events}</td>
                <td className="tab">{e.players}</td>
                <td>
                  <span className={"adm-pill " + (e.active ? "" : "adm-pill-ghost")}
                        style={e.active ? { background: accent, color: "#001215" } : {}}>{e.status}</span>
                </td>
                <td>
                  <button className="adm-btn">Voir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

// ── 4) TV idle / waiting carousel ──────────────────────────────────────────
// Rotates between: Hero "en attente" + next match, Recent results, Group standings preview, Bracket preview.
const TV_IDLE_SLIDES = ["hero", "results", "groups", "bracket"];

function TvIdle({ accent }) {
  const [slide, setSlide] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  React.useEffect(() => {
    if (paused) return;
    const t = setInterval(() => setSlide((i) => (i + 1) % TV_IDLE_SLIDES.length), 6000);
    return () => clearInterval(t);
  }, [paused]);

  return (
    <div className="tv-idle">
      <div className="tv-idle-bg" />
      <div className="tv-idle-glow" style={{ background: `radial-gradient(ellipse 60% 40% at 50% 50%, ${accent}33, transparent 70%)` }} />

      <header className="tv-idle-top">
        <div className="tv-tournament-mark" style={{ color: accent }}>
          <svg viewBox="0 0 24 24" width="48" height="48">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.4"/>
          </svg>
        </div>
        <div>
          <div className="tv-idle-tournament">OPEN DE MOUTILLOUX</div>
          <div className="tv-idle-edition">ÉDITION&nbsp;2026 · 25.05 → 02.06</div>
        </div>
        <div className="tv-idle-clock tab">15<em>:</em>42</div>
      </header>

      <main className="tv-idle-main">
        {TV_IDLE_SLIDES.map((id, i) => (
          <section key={id} className={"tv-slide " + (i === slide ? "on" : "off")} aria-hidden={i !== slide}>
            {id === "hero"    && <TvIdleHero accent={accent} />}
            {id === "results" && <TvIdleResults accent={accent} />}
            {id === "groups"  && <TvIdleGroups accent={accent} />}
            {id === "bracket" && <TvIdleBracket accent={accent} />}
          </section>
        ))}
      </main>

      <footer className="tv-idle-foot">
        <div className="tv-idle-next-bar">
          <span className="tv-idle-next-bar-lbl">PROCHAIN MATCH</span>
          <span className="tv-idle-next-bar-time tab">14:00</span>
          <span className="tv-idle-next-bar-stage">DEMI-FINALE 1</span>
          <span className="tv-idle-next-bar-sep" />
          <span className="tv-idle-next-bar-side">
            <em className="tv-idle-next-bar-seed" style={{ background: accent }}>A1</em>
            <b>DOUDOU</b>
          </span>
          <span className="tv-idle-next-bar-vs">vs</span>
          <span className="tv-idle-next-bar-side">
            <em className="tv-idle-next-bar-seed">C1</em>
            <b>MAXIME</b>
          </span>
          <span className="tv-idle-next-bar-sep" />
          <span className="tv-idle-next-bar-court">CENTRAL</span>
        </div>
        <div className="tv-idle-foot-pager" style={{ "--accent": accent }}>
          {TV_IDLE_SLIDES.map((id, i) => (
            <i key={id} data-on={i === slide} aria-label={id} />
          ))}
        </div>
      </footer>
    </div>
  );
}

function TvIdleHero({ accent }) {
  return (
    <div className="tv-idle-hero">
      <div className="tv-idle-ball" style={{ "--accent": accent }}>
        <span />
      </div>
      <div className="tv-idle-status" style={{ color: accent }}>EN&nbsp;ATTENTE DU PROCHAIN MATCH</div>
      <div className="tv-idle-head">Reprise dans <b className="tab">12&apos;</b></div>

      <div className="tv-idle-hero-stats">
        <div className="tv-idle-hero-stat">
          <span>TERRAINS</span><b>5 ouverts</b>
        </div>
        <div className="tv-idle-hero-stat">
          <span>MATCHS JOUÉS</span><b className="tab">42<em>/86</em></b>
        </div>
        <div className="tv-idle-hero-stat">
          <span>PROCHAINE PHASE</span><b style={{ color: accent }}>FINALE · 17:00</b>
        </div>
      </div>
    </div>
  );
}

function TvIdleResults({ accent }) {
  const results = [
    { time: "13:42", court: "Central", stage: "Quart 1", a: "Doudou",  aSeed: "A1", b: "Huguette", bSeed: "D2", score: "6–2", winner: "A" },
    { time: "12:58", court: "Court 2", stage: "Quart 2", a: "Maxime",  aSeed: "C1", b: "Seb.La",   bSeed: "B2", score: "6–4", winner: "A" },
    { time: "12:30", court: "Court 3", stage: "Quart 3", a: "Cyrille", aSeed: "B1", b: "Marc",     bSeed: "D1", score: "6–3", winner: "A" },
    { time: "11:48", court: "Central", stage: "Quart 4", a: "Seb.Lec", aSeed: "A2", b: "Ambre",    bSeed: "C2", score: "6–1", winner: "A" },
    { time: "11:10", court: "Court 2", stage: "Poule A · J3", a: "Hugo R.", aSeed: "A3", b: "Léa B.",  bSeed: "A4", score: "5–7", winner: "B" },
  ];
  return (
    <div className="tv-rotate">
      <h2 className="tv-rotate-title">
        DERNIERS RÉSULTATS
        <em style={{ color: accent }}>SIMPLE HOMME</em>
      </h2>
      <div className="tv-results">
        {results.map((r, i) => (
          <div key={i} className="tv-result-row" style={{ animationDelay: `${i * 80}ms` }}>
            <span className="tv-result-time adm-mono">{r.time}</span>
            <span className="tv-result-stage">{r.stage}</span>
            <div className="tv-result-match">
              <div className={"tv-result-side " + (r.winner === "A" ? "win" : "")}>
                <span className="tv-result-seed" style={{ background: r.winner === "A" ? accent : "rgba(255,255,255,0.08)", color: r.winner === "A" ? "#001215" : "var(--ink-2)" }}>{r.aSeed}</span>
                <span className="tv-result-name">{r.a}</span>
                {r.winner === "A" && <i className="tv-result-w" style={{ color: accent }}>▶</i>}
              </div>
              <div className={"tv-result-side " + (r.winner === "B" ? "win" : "")}>
                <span className="tv-result-seed" style={{ background: r.winner === "B" ? accent : "rgba(255,255,255,0.08)", color: r.winner === "B" ? "#001215" : "var(--ink-2)" }}>{r.bSeed}</span>
                <span className="tv-result-name">{r.b}</span>
                {r.winner === "B" && <i className="tv-result-w" style={{ color: accent }}>▶</i>}
              </div>
            </div>
            <span className="tv-result-score tab">{r.score}</span>
            <span className="tv-result-court">{r.court}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TvIdleGroups({ accent }) {
  const pair = window.POULES.slice(0, 2);
  return (
    <div className="tv-rotate">
      <h2 className="tv-rotate-title">
        CLASSEMENT DES POULES
        <em style={{ color: accent }}>SIMPLE HOMME · APERÇU</em>
      </h2>
      <div className="tv-groups">
        {pair.map((p, idx) => (
          <div key={p.id} className="tv-group" style={{ animationDelay: `${idx * 120}ms` }}>
            <div className="tv-group-head">
              <span className="tv-group-letter" style={{ background: accent }}>{p.id}</span>
              <span className="tv-group-title">{p.title}</span>
            </div>
            <div className="tv-group-rows">
              <div className="tv-group-row tv-group-row-head">
                <span>JOUEUR</span><span>V</span><span>D</span><span>JEUX</span><span>PTS</span>
              </div>
              {p.rows.map((r, i) => (
                <div key={i} className={"tv-group-row " + (r.q ? "q" : "")}>
                  <span className="tv-group-name">
                    <em className="tv-group-rank">{i + 1}</em>
                    {r.player}
                    {r.q && <i className="tv-group-q" style={{ background: accent }}>Q</i>}
                  </span>
                  <span className="tab">{r.v}</span>
                  <span className="tab">{r.d}</span>
                  <span className="tab">{r.jeux}</span>
                  <span className="tab tv-group-pts">{r.pts}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="tv-rotate-foot">
        Aperçu · poules A et B sur 4 — défilement automatique
      </div>
    </div>
  );
}

function TvIdleBracket({ accent }) {
  const b = window.BRACKET;
  return (
    <div className="tv-rotate">
      <h2 className="tv-rotate-title">
        TABLEAU FINAL
        <em style={{ color: accent }}>VERS LA COUPE 2026</em>
      </h2>
      <div className="tv-mini-bracket">
        <div className="tv-mini-col">
          <div className="tv-mini-col-head">QUARTS</div>
          {b.qf.map((m, i) => (
            <div key={m.id} className={"tv-mini-match " + (m.winner ? "done" : "")} style={{ animationDelay: `${i * 60}ms` }}>
              <div className={"tv-mini-slot " + (m.winner === "A" ? "win" : "")}>
                <span className="tv-mini-seed" style={{ background: m.winner === "A" ? accent : undefined, color: m.winner === "A" ? "#001215" : undefined }}>{m.a.seed}</span>
                <span className="tv-mini-name">{m.a.name}</span>
                <span className="tv-mini-score tab">{m.a.score}</span>
              </div>
              <div className={"tv-mini-slot " + (m.winner === "B" ? "win" : "")}>
                <span className="tv-mini-seed">{m.b.seed}</span>
                <span className="tv-mini-name">{m.b.name}</span>
                <span className="tv-mini-score tab">{m.b.score}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="tv-mini-col">
          <div className="tv-mini-col-head">DEMI-FINALES</div>
          <div style={{ height: 30 }} />
          {b.sf.map((m, i) => (
            <div key={m.id} className={"tv-mini-match " + (m.live ? "live " : "") + (m.winner ? "done " : "")} style={{ marginTop: i ? 90 : 0, animationDelay: `${(b.qf.length + i) * 60}ms` }}>
              {m.live && <span className="tv-mini-live" style={{ color: accent }}><i style={{ background: accent }} /> EN DIRECT</span>}
              <div className="tv-mini-slot">
                <span className="tv-mini-seed">{m.a.seed}</span>
                <span className="tv-mini-name">{m.a.name}</span>
                <span className="tv-mini-score tab">{m.a.score}</span>
              </div>
              <div className="tv-mini-slot">
                <span className="tv-mini-seed">{m.b.seed}</span>
                <span className="tv-mini-name">{m.b.name}</span>
                <span className="tv-mini-score tab">{m.b.score}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="tv-mini-col">
          <div className="tv-mini-col-head">FINALE</div>
          <div style={{ height: 130 }} />
          <div className="tv-mini-match final">
            <div className="tv-mini-slot">
              <span className="tv-mini-seed">?</span>
              <span className="tv-mini-name">Vainqueur SF1</span>
            </div>
            <div className="tv-mini-slot">
              <span className="tv-mini-seed">?</span>
              <span className="tv-mini-name">Vainqueur SF2</span>
            </div>
          </div>
        </div>
        <div className="tv-mini-col tv-mini-trophy-col">
          <div className="tv-mini-col-head" style={{ color: accent }}>VAINQUEUR</div>
          <div style={{ height: 100 }} />
          <div className="tv-mini-trophy" style={{ color: accent }}>
            <svg viewBox="0 0 32 32" width="44" height="44"><path d="M6 4h20v6a8 8 0 01-8 8h-4a8 8 0 01-8-8V4zm0 0H2v3a3 3 0 003 3M26 4h4v3a3 3 0 01-3 3M12 18v4M20 18v4M9 26h14v2H9z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
            <div className="tv-mini-trophy-lbl">À DÉSIGNER</div>
            <div className="tv-mini-trophy-sub">Finale 17:00</div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { LoginScreen, ArbitreHome, AdminTournoi, TvIdle });
