// admin.jsx — Admin panel for organizers (PC 1440×900, light theme)
// Sidebar + Joueurs | Poules | Matchs | Tableau final

function AdminPanel({ accent, modal, onModal, initialPage }) {
  const [page, setPage] = React.useState(initialPage || "joueurs");
  React.useEffect(() => { if (initialPage) setPage(initialPage); }, [initialPage]);

  return (
    <div className="adm light-scope">
      <AdminSidebar current={page} onNav={setPage} accent={accent} />
      <main className="adm-main">
        <AdminHeader page={page} accent={accent} onModal={onModal} />
        <div className="adm-content">
          {page === "joueurs"  && <AdminJoueurs accent={accent} onModal={onModal} />}
          {page === "poules"   && <AdminPoules accent={accent} onModal={onModal} />}
          {page === "matchs"   && <AdminMatchs accent={accent} onModal={onModal} />}
          {page === "tableau"  && <AdminTableau accent={accent} />}
          {page === "tournoi"  && <AdminTournoi accent={accent} />}
        </div>
      </main>

      {modal === "addPlayer"   && <AddPlayerModal     accent={accent} onClose={() => onModal(null)} />}
      {modal === "editPlayer"  && <AddPlayerModal     accent={accent} onClose={() => onModal(null)} editing={window.PLAYERS[0]} />}
      {modal === "createTeam"  && <CreateTeamModal    accent={accent} onClose={() => onModal(null)} />}
      {modal === "autoFill"    && <AutoFillModal      accent={accent} onClose={() => onModal(null)} />}
      {modal === "generate"    && <GenerateMatchesModal accent={accent} onClose={() => onModal(null)} />}
      {modal === "confirm"     && <ConfirmModal title="Retirer Doudou Mercier de l'épreuve ?" body="Le joueur sera désinscrit de l'épreuve Simple Homme. Son historique de matchs est conservé." danger confirmLabel="Retirer" onClose={() => onModal(null)} />}
      {modal === "editMatch"   && <EditMatchPanel    accent={accent} onClose={() => onModal(null)} />}
    </div>
  );
}

function AdminSidebar({ current, onNav, accent }) {
  const nav = [
    { id: "joueurs", label: "Joueurs", count: 16, icon: (
      <svg viewBox="0 0 24 24" width="16" height="16"><path d="M9 11a4 4 0 100-8 4 4 0 000 8zm0 2c-4 0-7 2-7 5v2h14v-2c0-3-3-5-7-5zM17 11a3 3 0 100-6 3 3 0 000 6zm5 7c0-2.2-2-4-4-4-.7 0-1.4.2-2 .5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
    )},
    { id: "poules", label: "Poules", count: 4, icon: (
      <svg viewBox="0 0 24 24" width="16" height="16"><rect x="3" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/><rect x="13" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/><rect x="3" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/><rect x="13" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
    )},
    { id: "matchs", label: "Matchs", count: 12, icon: (
      <svg viewBox="0 0 24 24" width="16" height="16"><rect x="3" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/><rect x="10" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/><rect x="17" y="4" width="4" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
    )},
    { id: "tableau", label: "Tableau final", count: 7, icon: (
      <svg viewBox="0 0 24 24" width="16" height="16"><path d="M3 6h6M3 18h6M9 6v12M15 12h6M15 12L9 6M15 12L9 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
    )},
    { id: "tournoi", label: "Tournoi", count: 4, icon: (
      <svg viewBox="0 0 24 24" width="16" height="16"><path d="M6 4h12v4a6 6 0 01-12 0V4zM6 4H3v2a2 2 0 002 2M18 4h3v2a2 2 0 01-2 2M10 14v3M14 14v3M8 20h8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
    )},
  ];
  return (
    <aside className="adm-side">
      <div className="adm-side-brand">
        <div className="adm-side-mark" style={{ background: accent }}>
          <svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.6"/><path d="M3.5 8.2c5 2.4 12 2.4 17 0M3.5 15.8c5-2.4 12-2.4 17 0" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
        </div>
        <div>
          <div className="adm-side-name">MOUTILLOUX</div>
          <div className="adm-side-sub">Open · Édition 2026</div>
        </div>
      </div>

      <div className="adm-side-context">
        <div className="adm-side-context-lbl">Épreuve active</div>
        <button className="adm-side-context-btn">
          <span>Simple Homme · Cat. A</span>
          <svg viewBox="0 0 16 16" width="12" height="12"><path d="M3 6l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      </div>

      <nav className="adm-side-nav">
        {nav.map((n) => (
          <button key={n.id} className={"adm-side-nav-item " + (current === n.id ? "on" : "")}
                  onClick={() => onNav(n.id)}
                  style={current === n.id ? { "--accent": accent } : {}}>
            {n.icon}
            <span>{n.label}</span>
            <em className="tab">{n.count}</em>
          </button>
        ))}
      </nav>

      <div className="adm-side-bottom">
        <button className="adm-side-link">
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" strokeWidth="1.6"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
          Voir les résultats <span className="adm-side-link-arrow">↗</span>
        </button>
        <button className="adm-side-link">
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M3 12h12m0 0l-4-4m4 4l-4 4M19 4v16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Changer d'épreuve
        </button>
        <button className="adm-side-link adm-side-link-out">
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3M10 17l5-5-5-5M3 12h12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Déconnexion
        </button>
      </div>
    </aside>
  );
}

function AdminHeader({ page, accent, onModal }) {
  const titles = {
    joueurs: ["Joueurs", "16 joueurs inscrits dans l'épreuve Simple Homme"],
    poules:  ["Poules", "4 groupes · 16 joueurs · 2 qualifiés par groupe"],
    matchs:  ["Matchs", "Backlog, file d'attente et matchs terminés"],
    tableau: ["Tableau final", "8 places · à remplir depuis la liste des qualifiés"],
    tournoi: ["Tournoi", "Édition active, épreuves et historique"],
  };
  const [t, sub] = titles[page] || ["", ""];
  const primaryAction = {
    joueurs: { label: "+ Ajouter un joueur",      modal: "addPlayer" },
    poules:  { label: "Remplir automatiquement",  modal: "autoFill" },
    matchs:  { label: "Générer les matchs de poule", modal: "generate" },
    tableau: { label: "Créer le tableau",         modal: null },
    tournoi: { label: "+ Nouvelle édition",       modal: null },
  }[page];

  return (
    <header className="adm-head">
      <div>
        <div className="adm-head-crumb">Tournoi · Simple Homme</div>
        <h1>{t}</h1>
        <div className="adm-head-sub">{sub}</div>
      </div>
      <div className="adm-head-actions">
        {page === "joueurs" && (
          <button className="adm-btn" onClick={() => onModal && onModal("createTeam")}>
            <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="8" cy="8" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.6"/><circle cx="16" cy="9" r="3" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
            Créer une équipe
          </button>
        )}
        <button className="adm-btn">
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M3 14l4 4L21 4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Sauvegardé
        </button>
        <button className="adm-btn primary" style={{ background: accent }}
                onClick={() => onModal && primaryAction.modal && onModal(primaryAction.modal)}>
          {primaryAction.label}
        </button>
      </div>
    </header>
  );
}

// ── Page: Joueurs ──────────────────────────────────────────────────────────
function AdminJoueurs({ accent, onModal }) {
  return (
    <div className="adm-card">
      <div className="adm-card-toolbar">
        <div className="adm-search">
          <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.6"/><path d="M21 21l-5-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
          <input placeholder="Rechercher un joueur, une licence…" />
        </div>
        <div className="adm-filter-chips">
          <button className="adm-chip on">Tous · 16</button>
          <button className="adm-chip">Têtes de série · 8</button>
          <button className="adm-chip">Inscrits sans poule · 0</button>
        </div>
      </div>
      <table className="adm-table">
        <thead>
          <tr>
            <th className="adm-th-check"><input type="checkbox" /></th>
            <th>Joueur</th>
            <th>Licence FFT</th>
            <th>Catégorie</th>
            <th>Poule</th>
            <th>Tête de série</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {window.PLAYERS.map((p, i) => (
            <tr key={p.id}>
              <td><input type="checkbox" /></td>
              <td>
                <div className="adm-player">
                  <div className="adm-avatar" style={{ background: ["#FFE48A", "#A7E8E2", "#F2B0B0", "#C4B5FD"][i % 4] }}>
                    {p.first[0]}{p.last[0]}
                  </div>
                  <div>
                    <div className="adm-player-name">{p.first} {p.last}</div>
                    <div className="adm-player-meta">Senior · Droitier</div>
                  </div>
                </div>
              </td>
              <td className="tab adm-mono">{p.lic}</td>
              <td>Simple Homme</td>
              <td>
                <span className="adm-pill" style={{ background: accent, color: "#001215" }}>Poule {p.seed[0]}</span>
              </td>
              <td>
                <span className="adm-pill adm-pill-ghost">{p.seed}</span>
              </td>
              <td>
                <div style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                  <button className="adm-row-act" aria-label="Éditer" onClick={() => onModal && onModal("editPlayer")} style={{ color: "var(--ink-3)" }}>
                    <svg viewBox="0 0 24 24" width="14" height="14"><path d="M4 20h4l10-10-4-4L4 16v4zM14 6l4 4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
                  </button>
                  <button className="adm-row-act" aria-label="Retirer" onClick={() => onModal && onModal("confirm")}>
                    <svg viewBox="0 0 24 24" width="14" height="14"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Page: Poules (drag & drop) ──────────────────────────────────────────────
function AdminPoules({ accent, onModal }) {
  return (
    <div className="adm-poules-grid">
      <div className="adm-card">
        <div className="adm-card-head">
          <h3>Non assignés</h3>
          <em className="adm-card-count">0 joueurs</em>
        </div>
        <div className="adm-dropzone empty">
          <svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
          <span>Tous les joueurs sont placés</span>
        </div>
      </div>
      {["A", "B", "C", "D"].map((letter, idx) => (
        <div key={letter} className="adm-card">
          <div className="adm-card-head">
            <h3>
              <span className="adm-poule-letter" style={{ background: accent }}>{letter}</span>
              Poule {letter}
            </h3>
            <em className="adm-card-count">4 joueurs · 6 matchs</em>
          </div>
          <div className="adm-dropzone">
            {window.POULES[idx].rows.map((r) => (
              <div key={r.player} className="adm-pill-row">
                <span className="adm-grip">⋮⋮</span>
                <div className="adm-avatar small" style={{ background: ["#FFE48A","#A7E8E2","#F2B0B0","#C4B5FD"][idx] }}>
                  {r.player.slice(0,2)}
                </div>
                <span className="adm-pill-row-name">{r.player}</span>
                {r.q && <em className="adm-pill-q" style={{ background: accent, color: "#001215" }}>Q</em>}
                <button className="adm-pill-row-x" aria-label="Retirer">✕</button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Page: Matchs Kanban ────────────────────────────────────────────────────
function AdminMatchs({ accent, onModal }) {
  const cols = [
    { id: "backlog", label: "Backlog", items: window.MATCHES_KANBAN.backlog, tint: "var(--ink-3)" },
    { id: "queue",   label: "File d'attente", items: window.MATCHES_KANBAN.queue, tint: accent },
    { id: "done",    label: "Terminés", items: window.MATCHES_KANBAN.done, tint: "var(--success)" },
  ];
  return (
    <div className="adm-kanban">
      {cols.map((c) => (
        <div key={c.id} className="adm-kanban-col">
          <div className="adm-kanban-head">
            <i className="adm-kanban-dot" style={{ background: c.tint }} />
            <span>{c.label}</span>
            <em className="adm-card-count">{c.items.length}</em>
          </div>
          <div className="adm-kanban-body">
            {c.items.map((m) => (
              <div key={m.id} className={"adm-kanban-card " + (m.featured ? "featured" : "")}>
                {m.featured && <span className="adm-kanban-star" style={{ color: accent }}>★ MIS EN AVANT</span>}
                <div className="adm-kanban-type">{m.type}</div>
                <div className="adm-kanban-players">
                  <span>{m.a}</span>
                  <em>vs</em>
                  <span>{m.b}</span>
                </div>
                <div className="adm-kanban-meta">
                  {m.score && <span>Score : <b>{m.score}</b></span>}
                  {m.court && <span>Court : <b>{m.court}</b></span>}
                  {m.round && !m.score && <span>{m.round}</span>}
                </div>
                <div className="adm-kanban-row">
                  <button className="adm-kanban-btn" onClick={() => onModal && onModal("editMatch")}>Éditer</button>
                  {!m.featured && c.id === "queue" && <button className="adm-kanban-btn primary" style={{ borderColor: accent, color: accent }}>★ Mettre en avant</button>}
                  <span className="adm-grip" style={{ marginLeft: "auto" }}>⋮⋮</span>
                </div>
              </div>
            ))}
            <button className="adm-kanban-add">+ Ajouter un match</button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Page: Tableau final ────────────────────────────────────────────────────
function AdminTableau({ accent }) {
  return (
    <div className="adm-tableau-grid">
      <div className="adm-tableau-bracket">
        <div className="adm-tableau-head">
          <span>Quarts</span>
          <span>Demi</span>
          <span>Finale</span>
        </div>
        <div className="adm-tableau-svg">
          {window.BRACKET.qf.map((m, i) => (
            <div key={m.id} className="adm-tableau-slot qf" style={{ top: i * 90 + 10 }}>
              <span className="adm-tableau-seed" style={{ background: accent }}>{m.a.seed}</span>
              <span>{m.a.name}</span>
              <em className="adm-tableau-vs">vs</em>
              <span className="adm-tableau-seed">{m.b.seed}</span>
              <span>{m.b.name}</span>
            </div>
          ))}
          {window.BRACKET.sf.map((m, i) => (
            <div key={m.id} className="adm-tableau-slot sf" style={{ top: i * 180 + 70 }}>
              <span className="adm-tableau-seed" style={{ background: accent }}>{m.a.seed}</span>
              <span>{m.a.name}</span>
              <em className="adm-tableau-vs">vs</em>
              <span className="adm-tableau-seed">{m.b.name === "Seb.Lec" ? "?" : m.b.seed}</span>
              <span>{m.b.name === "Seb.Lec" ? "À DÉSIGNER" : m.b.name}</span>
            </div>
          ))}
          <div className="adm-tableau-slot f">
            <span className="adm-tableau-empty">Vainqueur SF1</span>
            <em className="adm-tableau-vs">vs</em>
            <span className="adm-tableau-empty">Vainqueur SF2</span>
          </div>
        </div>
      </div>

      <div className="adm-tableau-side">
        <div className="adm-card">
          <div className="adm-card-head"><h3>Qualifiés disponibles</h3><em className="adm-card-count">8</em></div>
          <div className="adm-q-list">
            {window.PLAYERS.map((p) => (
              <div key={p.id} className="adm-q-item">
                <span className="adm-q-seed" style={{ background: accent }}>{p.seed}</span>
                <span>{p.first} {p.last}</span>
                <span className="adm-grip">⋮⋮</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { AdminPanel });
