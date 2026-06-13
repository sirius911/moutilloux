// modals.jsx — Admin modals + match edit slide-out
// All overlays live inside .light-scope (.adm wrapper)

// ── Shared modal shell ──────────────────────────────────────────────────────
function ModalShell({ title, subtitle, onClose, children, footer, size = "md", icon }) {
  return (
    <div className="mdl-bg" onMouseDown={onClose}>
      <div className={"mdl mdl-" + size} onMouseDown={(e) => e.stopPropagation()}>
        <header className="mdl-head">
          {icon && <div className="mdl-icon">{icon}</div>}
          <div className="mdl-head-text">
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button className="mdl-close" aria-label="Fermer" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
          </button>
        </header>
        <div className="mdl-body">{children}</div>
        {footer && <footer className="mdl-foot">{footer}</footer>}
      </div>
    </div>
  );
}

// ── Form primitives ─────────────────────────────────────────────────────────
function Field({ label, required, hint, children, span = 1 }) {
  return (
    <label className={"fld fld-span-" + span}>
      <span className="fld-lbl">{label}{required && <em>*</em>}</span>
      {children}
      {hint && <span className="fld-hint">{hint}</span>}
    </label>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div className="seg" role="radiogroup">
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          className={"seg-opt " + (value === o.value ? "on" : "")}
          onClick={() => onChange(o.value)}
        >
          {o.icon && <span className="seg-ic">{o.icon}</span>}
          {o.label}
        </button>
      ))}
    </div>
  );
}

// ── 1) Ajouter un joueur ────────────────────────────────────────────────────
function AddPlayerModal({ accent, onClose, editing }) {
  const [gender, setGender] = React.useState(editing?.gender || "M");
  const [seed, setSeed] = React.useState(editing ? true : false);
  return (
    <ModalShell
      title={editing ? "Modifier le joueur" : "Ajouter un joueur"}
      subtitle={editing ? `${editing.first} ${editing.last} · Licence ${editing.lic}` : "Le joueur sera créé puis inscrit à l'épreuve active (Simple Homme)."}
      onClose={onClose}
      size="lg"
      icon={
        <svg viewBox="0 0 24 24" width="20" height="20">
          <circle cx="10" cy="8" r="4" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <path d="M2 21c0-4 4-7 8-7s8 3 8 7M18 8v6M15 11h6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
        </svg>
      }
      footer={
        <>
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className="adm-btn" onClick={onClose}>Enregistrer comme brouillon</button>
          <button className="adm-btn primary" style={{ background: accent }}>
            {editing ? "Sauvegarder" : "Ajouter & inscrire"}
          </button>
        </>
      }
    >
      <div className="mdl-section">
        <h4>Identité</h4>
        <div className="fld-grid">
          <Field label="Prénom" required><input className="inp" defaultValue={editing?.first || ""} placeholder="Prénom" /></Field>
          <Field label="Nom" required><input className="inp" defaultValue={editing?.last || ""} placeholder="Nom de famille" /></Field>
          <Field label="Date de naissance">
            <input className="inp" type="date" defaultValue="1992-05-14" />
          </Field>
          <Field label="Genre" required>
            <Segmented value={gender} onChange={setGender} options={[
              { value: "M", label: "Homme" },
              { value: "F", label: "Femme" },
              { value: "O", label: "Autre" },
            ]} />
          </Field>
        </div>
      </div>

      <div className="mdl-section">
        <h4>Contact</h4>
        <div className="fld-grid">
          <Field label="Email" hint="Pour les notifications de planning"><input className="inp" type="email" placeholder="prenom@exemple.fr" defaultValue={editing ? "doudou.mercier@example.fr" : ""} /></Field>
          <Field label="Téléphone"><input className="inp" type="tel" placeholder="06 12 34 56 78" defaultValue={editing ? "06 18 22 04 17" : ""} /></Field>
        </div>
      </div>

      <div className="mdl-section">
        <h4>Compétition</h4>
        <div className="fld-grid">
          <Field label="N° licence FFT" required>
            <input className="inp adm-mono" placeholder="FFT-XXXXX" defaultValue={editing?.lic || ""} />
          </Field>
          <Field label="Classement FFT">
            <select className="inp">
              <option>Non classé</option>
              <option>40 → 30/5</option>
              <option>30/4 → 30/2</option>
              <option>30/1 → 15/5</option>
              <option>15/4 → Promo</option>
            </select>
          </Field>
          <Field label="Épreuves à inscrire" span={2}>
            <div className="chk-row">
              <label className="chk on"><input type="checkbox" defaultChecked /> Simple Homme</label>
              <label className="chk"><input type="checkbox" /> Double Mixte</label>
              <label className="chk"><input type="checkbox" /> Simple Homme +45</label>
            </div>
          </Field>
          <Field label="Tête de série" span={2}>
            <div className="row-mix">
              <label className="sw">
                <input type="checkbox" checked={seed} onChange={(e) => setSeed(e.target.checked)} />
                <i style={{ "--accent": accent }} />
                <span>Désigner comme tête de série</span>
              </label>
              {seed && (
                <select className="inp inp-sm">
                  <option>TS 1</option><option>TS 2</option><option>TS 3</option><option>TS 4</option>
                </select>
              )}
            </div>
          </Field>
        </div>
      </div>
    </ModalShell>
  );
}

// ── 2) Créer une équipe (Double) ────────────────────────────────────────────
function CreateTeamModal({ accent, onClose }) {
  return (
    <ModalShell
      title="Créer une équipe"
      subtitle="Mode Double Mixte · sélectionnez deux joueurs déjà inscrits"
      onClose={onClose}
      size="md"
      icon={
        <svg viewBox="0 0 24 24" width="20" height="20">
          <circle cx="8" cy="8" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <circle cx="16" cy="9" r="3" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <path d="M2 20c0-3 3-5 6-5s6 2 6 5M14 20c0-2 2-4 5-4s3 2 3 4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
        </svg>
      }
      footer={
        <>
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className="adm-btn primary" style={{ background: accent }}>Créer l'équipe</button>
        </>
      }
    >
      <div className="mdl-section">
        <h4>Composition</h4>
        <div className="team-build">
          <div className="team-slot">
            <span className="team-slot-lbl">Joueur 1 · Homme</span>
            <div className="team-picker">
              <div className="adm-avatar" style={{ background: "#FFE48A" }}>DM</div>
              <div>
                <div className="adm-player-name">Doudou Mercier</div>
                <div className="adm-player-meta">A1 · Senior · 30/2</div>
              </div>
              <button className="adm-btn">Changer</button>
            </div>
          </div>
          <div className="team-and" style={{ color: accent }}>+</div>
          <div className="team-slot">
            <span className="team-slot-lbl">Joueur 2 · Femme</span>
            <div className="team-picker dashed">
              <div className="adm-avatar adm-avatar-empty">??</div>
              <div className="adm-player-meta">Sélectionnez une joueuse féminine</div>
              <button className="adm-btn primary" style={{ background: accent, marginLeft: "auto" }}>Choisir</button>
            </div>
          </div>
        </div>
      </div>

      <div className="mdl-section">
        <h4>Identification</h4>
        <div className="fld-grid">
          <Field label="Nom d'équipe" hint="Optionnel — affiché sur la TV et l'arbitre"><input className="inp" placeholder="ex. Les Foudres" /></Field>
          <Field label="Tête de série">
            <select className="inp">
              <option>Non</option>
              <option>TS 1</option><option>TS 2</option><option>TS 3</option><option>TS 4</option>
            </select>
          </Field>
        </div>
      </div>
    </ModalShell>
  );
}

// ── 3) Auto-remplir les poules ──────────────────────────────────────────────
function AutoFillModal({ accent, onClose }) {
  const [size, setSize] = React.useState(4);
  const [method, setMethod] = React.useState("snake");
  const total = 16;
  const groups = Math.ceil(total / size);
  return (
    <ModalShell
      title="Remplir les poules automatiquement"
      subtitle="L'algorithme répartit les joueurs en équilibrant les têtes de série."
      onClose={onClose}
      size="md"
      icon={
        <svg viewBox="0 0 24 24" width="20" height="20">
          <rect x="3" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <rect x="13" y="3" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <rect x="3" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <rect x="13" y="13" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6"/>
        </svg>
      }
      footer={
        <>
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className="adm-btn primary" style={{ background: accent }}>
            Générer {groups} poules de {size}
          </button>
        </>
      }
    >
      <div className="mdl-section">
        <h4>Format des poules</h4>
        <div className="fld-grid">
          <Field label="Joueurs par poule">
            <Segmented value={size} onChange={setSize} options={[
              { value: 3, label: "3 joueurs" },
              { value: 4, label: "4 joueurs" },
              { value: 5, label: "5 joueurs" },
            ]} />
          </Field>
          <Field label="Méthode de répartition">
            <Segmented value={method} onChange={setMethod} options={[
              { value: "snake", label: "Snake (équilibrée)" },
              { value: "random", label: "Aléatoire" },
            ]} />
          </Field>
          <Field label="Options" span={2}>
            <label className="sw"><input type="checkbox" defaultChecked /><i style={{ "--accent": accent }} /><span>Séparer les têtes de série dans des poules différentes</span></label>
            <label className="sw"><input type="checkbox" /><i style={{ "--accent": accent }} /><span>Éviter de regrouper des joueurs du même club</span></label>
          </Field>
        </div>
      </div>

      <div className="mdl-section">
        <h4>Prévisualisation</h4>
        <div className="preview-pills">
          {Array.from({ length: groups }).map((_, i) => (
            <div key={i} className="preview-pill">
              <span className="adm-poule-letter" style={{ background: accent }}>{"ABCDE"[i]}</span>
              <span>Poule {"ABCDE"[i]}</span>
              <em className="adm-card-count">{i < groups - 1 || total % size === 0 ? size : total % size} joueurs</em>
            </div>
          ))}
        </div>
        <div className="mdl-warn">
          <svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 2L1 21h22L12 2zm0 6v6m0 3v.5" fill="none" stroke="currentColor" strokeWidth="1.8"/></svg>
          <span>Les matchs de poule existants seront <b>annulés et regénérés</b> si vous confirmez.</span>
        </div>
      </div>
    </ModalShell>
  );
}

// ── 4) Générer les matchs de poule ──────────────────────────────────────────
function GenerateMatchesModal({ accent, onClose }) {
  const rows = window.POULES.map((p) => ({ id: p.id, n: p.rows.length, matchs: (p.rows.length * (p.rows.length - 1)) / 2 }));
  const total = rows.reduce((s, r) => s + r.matchs, 0);
  return (
    <ModalShell
      title="Générer les matchs de poule"
      subtitle="Round-robin complet pour chaque poule."
      onClose={onClose}
      size="md"
      icon={
        <svg viewBox="0 0 24 24" width="20" height="20">
          <rect x="3" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <rect x="10" y="4" width="5" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          <rect x="17" y="4" width="4" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.6"/>
        </svg>
      }
      footer={
        <>
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className="adm-btn primary" style={{ background: accent }}>Générer {total} matchs</button>
        </>
      }
    >
      <div className="mdl-section">
        <h4>Format de match</h4>
        <div className="fld-grid">
          <Field label="Nombre de sets">
            <Segmented value={1} onChange={() => {}} options={[
              { value: 1, label: "1 set" },
              { value: 3, label: "Au meilleur des 3" },
            ]} />
          </Field>
          <Field label="Jeux pour gagner">
            <select className="inp"><option>5 jeux (avec TB à 4)</option><option>6 jeux (avec TB à 6)</option><option>4 jeux (rapide)</option></select>
          </Field>
          <Field label="Points de tie-break">
            <select className="inp"><option>7 points</option><option>10 points</option></select>
          </Field>
          <Field label="Court par défaut">
            <select className="inp">{window.COURTS.map((c) => <option key={c}>{c}</option>)}</select>
          </Field>
        </div>
      </div>

      <div className="mdl-section">
        <h4>Répartition à générer</h4>
        <div className="gen-table">
          <div className="gen-row gen-row-head">
            <span>Poule</span><span>Joueurs</span><span>Matchs</span><span>Estimation</span>
          </div>
          {rows.map((r) => (
            <div key={r.id} className="gen-row">
              <span><span className="adm-poule-letter" style={{ background: accent }}>{r.id}</span> Poule {r.id}</span>
              <span className="tab">{r.n}</span>
              <span className="tab">{r.matchs}</span>
              <span className="adm-mono">~{r.matchs * 45} min</span>
            </div>
          ))}
          <div className="gen-row gen-row-total">
            <span><b>Total</b></span>
            <span className="tab"><b>{rows.reduce((s, r) => s + r.n, 0)}</b></span>
            <span className="tab"><b>{total}</b></span>
            <span className="adm-mono"><b>~{Math.round((total * 45) / 60)} h</b></span>
          </div>
        </div>
      </div>
    </ModalShell>
  );
}

// ── 5) Confirmation (retirer joueur) ────────────────────────────────────────
function ConfirmModal({ title, body, danger, confirmLabel, onConfirm, onClose }) {
  return (
    <div className="mdl-bg" onMouseDown={onClose}>
      <div className="mdl mdl-sm mdl-confirm" onMouseDown={(e) => e.stopPropagation()}>
        <div className={"mdl-confirm-ic " + (danger ? "danger" : "")}>
          <svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 2L1 21h22L12 2zm0 6v6m0 3v.5" fill="none" stroke="currentColor" strokeWidth="1.8"/></svg>
        </div>
        <h3>{title}</h3>
        <p>{body}</p>
        <div className="mdl-confirm-row">
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className={"adm-btn " + (danger ? "danger" : "primary")} onClick={onConfirm || onClose}>
            {confirmLabel || "Confirmer"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 6) Slide-out d'édition de match ─────────────────────────────────────────
function EditMatchPanel({ accent, onClose, match }) {
  const [tab, setTab] = React.useState("score");
  const m = match || {
    a: "Doudou", b: "Maxime", aSeed: "A1", bSeed: "C1",
    event: "Simple Homme", stage: "Demi-finale 1",
    court: "Central", time: "14:00", status: "LIVE", featured: true,
  };

  return (
    <div className="slide-bg" onMouseDown={onClose}>
      <aside className="slide" onMouseDown={(e) => e.stopPropagation()}>
        <header className="slide-head">
          <div>
            <div className="slide-crumb">{m.event} · {m.stage}</div>
            <h2>{m.a} <em>vs</em> {m.b}</h2>
            <div className="slide-tags">
              <span className={"slide-tag " + (m.status === "LIVE" ? "live" : "")}>
                <i /> {m.status === "LIVE" ? "EN DIRECT" : m.status === "FINISHED" ? "TERMINÉ" : "PRÉVU"}
              </span>
              <span className="slide-tag">{m.court}</span>
              <span className="slide-tag">{m.time}</span>
              {m.featured && <span className="slide-tag star" style={{ color: accent, borderColor: accent }}>★ MIS EN AVANT</span>}
            </div>
          </div>
          <button className="mdl-close" aria-label="Fermer" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
          </button>
        </header>

        <nav className="slide-tabs">
          {[
            { id: "score",    label: "Score" },
            { id: "format",   label: "Format" },
            { id: "planning", label: "Planning" },
            { id: "history",  label: "Historique" },
          ].map((t) => (
            <button key={t.id} className={"slide-tab " + (tab === t.id ? "on" : "")} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        <div className="slide-body">
          {tab === "score" && <EditScore m={m} accent={accent} />}
          {tab === "format" && <EditFormat m={m} accent={accent} />}
          {tab === "planning" && <EditPlanning m={m} accent={accent} />}
          {tab === "history" && <EditHistory m={m} accent={accent} />}
        </div>

        <footer className="slide-foot">
          <button className="adm-btn danger ghost">
            <svg viewBox="0 0 24 24" width="14" height="14"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
            Supprimer
          </button>
          <span className="slide-foot-spacer" />
          <button className="adm-btn" onClick={onClose}>Annuler</button>
          <button className="adm-btn primary" style={{ background: accent }} onClick={onClose}>Enregistrer</button>
        </footer>
      </aside>
    </div>
  );
}

function EditScore({ m, accent }) {
  return (
    <>
      <div className="slide-section">
        <h4>Score actuel <span className="slide-section-sub">éditable manuellement en cas d'erreur arbitre</span></h4>
        <div className="score-grid">
          <div className="score-grid-head">
            <span></span>
            <span>SETS</span>
            <span>SET 1</span>
            <span>JEU EN COURS</span>
            <span>POINT</span>
          </div>
          {["a", "b"].map((side) => (
            <div key={side} className="score-grid-row">
              <span className="score-grid-name">
                {side === "a" ? <i className="srv" style={{ background: accent }} /> : <i className="srv srv-off" />}
                {side === "a" ? m.a : m.b}
                <em className="adm-pill-ghost">[{side === "a" ? m.aSeed : m.bSeed}]</em>
              </span>
              <input className="inp inp-num tab" defaultValue={side === "a" ? "0" : "0"} />
              <input className="inp inp-num tab" defaultValue={side === "a" ? "4" : "3"} />
              <input className="inp inp-num tab" defaultValue={side === "a" ? "0" : "0"} />
              <input className="inp inp-num tab" defaultValue={side === "a" ? "30" : "40"} />
            </div>
          ))}
        </div>
        <label className="sw" style={{ marginTop: 14 }}>
          <input type="checkbox" /><i style={{ "--accent": accent }} />
          <span>Tie-break activé</span>
        </label>
      </div>

      <div className="slide-section">
        <h4>Vainqueur</h4>
        <Segmented value="none" onChange={() => {}} options={[
          { value: "none", label: "À déterminer" },
          { value: "a",    label: m.a },
          { value: "b",    label: m.b },
          { value: "abandon", label: "Abandon" },
        ]} />
      </div>
    </>
  );
}

function EditFormat({ m, accent }) {
  return (
    <div className="slide-section">
      <h4>Format du match</h4>
      <div className="fld-grid">
        <Field label="Sets à gagner">
          <Segmented value={1} onChange={() => {}} options={[
            { value: 1, label: "1 set" },
            { value: 2, label: "Best of 3" },
            { value: 3, label: "Best of 5" },
          ]} />
        </Field>
        <Field label="Jeux par set">
          <select className="inp" defaultValue="5">
            <option value="4">4 jeux</option>
            <option value="5">5 jeux (TB à 4)</option>
            <option value="6">6 jeux (TB à 6)</option>
          </select>
        </Field>
        <Field label="Tie-break à">
          <input className="inp tab" defaultValue="4" />
        </Field>
        <Field label="Points de tie-break">
          <select className="inp"><option>7 points</option><option>10 points</option></select>
        </Field>
        <Field label="Service initial" span={2}>
          <Segmented value="A" onChange={() => {}} options={[
            { value: "A", label: m.a },
            { value: "B", label: m.b },
            { value: "rand", label: "Tirage au sort" },
          ]} />
        </Field>
      </div>
    </div>
  );
}

function EditPlanning({ m, accent }) {
  return (
    <>
      <div className="slide-section">
        <h4>Planning</h4>
        <div className="fld-grid">
          <Field label="Court">
            <select className="inp" defaultValue={m.court}>
              {window.COURTS.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Heure prévue">
            <input className="inp tab" type="time" defaultValue={m.time} />
          </Field>
          <Field label="Statut">
            <Segmented value={m.status === "LIVE" ? "live" : "scheduled"} onChange={() => {}} options={[
              { value: "scheduled", label: "Prévu" },
              { value: "live",      label: "En direct" },
              { value: "finished",  label: "Terminé" },
              { value: "canceled",  label: "Annulé" },
            ]} />
          </Field>
          <Field label="Ordre dans la file" span={2}>
            <div className="row-mix">
              <input className="inp inp-sm tab" defaultValue="1" style={{ width: 80 }} />
              <span className="fld-hint">Le match #1 passe en direct sur la TV</span>
            </div>
          </Field>
        </div>
      </div>
      <div className="slide-section">
        <h4>Mise en avant</h4>
        <label className="sw"><input type="checkbox" defaultChecked={m.featured} /><i style={{ "--accent": accent }} /><span>Afficher ce match sur le scoreboard TV</span></label>
        <p className="slide-hint">Un seul match peut être mis en avant à la fois. Si vous activez ce match, celui qui est actuellement à l'antenne sera retiré.</p>
      </div>
    </>
  );
}

function EditHistory({ m, accent }) {
  const log = [
    { t: "14:42:08", who: "Arbitre · Pierre", what: "Point B · 30–40" },
    { t: "14:41:51", who: "Arbitre · Pierre", what: "Point A · 30–30" },
    { t: "14:41:20", who: "Arbitre · Pierre", what: "Changement de serveur" },
    { t: "14:40:55", who: "Arbitre · Pierre", what: "Jeu terminé · 4–3" },
    { t: "14:31:00", who: "Admin · Marie",   what: "Match démarré" },
    { t: "13:55:12", who: "Admin · Marie",   what: "Court modifié : Court 2 → Central" },
    { t: "10:02:34", who: "Système",         what: "Match créé (round-robin)" },
  ];
  return (
    <div className="slide-section">
      <h4>Activité</h4>
      <div className="log">
        {log.map((l, i) => (
          <div key={i} className="log-row">
            <span className="log-time adm-mono">{l.t}</span>
            <span className="log-who">{l.who}</span>
            <span className="log-what">{l.what}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  ModalShell, Field, Segmented,
  AddPlayerModal, CreateTeamModal, AutoFillModal, GenerateMatchesModal,
  ConfirmModal, EditMatchPanel,
});
