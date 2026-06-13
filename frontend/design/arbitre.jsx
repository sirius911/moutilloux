// arbitre.jsx — iPad referee interface (834×1112 portrait)
// 2 variants: "columns" (3-col classic) and "split" (giant score + huge tap zones)

function ArbitreHeader({ m, onClose }) {
  return (
    <div className="arb-header">
      <button className="arb-close" aria-label="Quitter">
        <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d="M14 6l-8 6 8 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      <div className="arb-header-main">
        <div className="arb-header-cat">{m.category}</div>
        <div className="arb-header-format">Poule · 1 set à 5 jeux · TB à 4 · Central</div>
      </div>
      <div className={"arb-status " + (m.status === "EN_COURS" ? "live" : "done")}>
        <i />
        {m.status === "EN_COURS" ? (m.inTB ? "JEU DÉCISIF" : "EN COURS") : "TERMINÉ"}
      </div>
    </div>
  );
}

function ArbitreSecondaryActions({ onUndo, onSwap, onEnd, onReset, canUndo }) {
  return (
    <div className="arb-actions">
      <button className="arb-act" disabled={!canUndo} onClick={onUndo}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path d="M9 14l-5-5 5-5M4 9h11a5 5 0 010 10h-3" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Annuler dernier point
      </button>
      <button className="arb-act" onClick={onSwap}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path d="M3 7h13l-3-3M21 17H8l3 3" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Changer serveur
      </button>
      <button className="arb-act danger" onClick={onEnd}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <rect x="6" y="6" width="12" height="12" rx="1" fill="currentColor"/>
        </svg>
        Terminer le match
      </button>
      <button className="arb-act danger ghost" onClick={onReset}>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path d="M4 4v6h6M20 20a8 8 0 10-3-7.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Réinitialiser
      </button>
    </div>
  );
}

// ── Confirmation modal for destructive actions ──────────────────────────────
function ConfirmModal({ title, body, danger, onConfirm, onCancel }) {
  return (
    <div className="arb-modal-bg" onClick={onCancel}>
      <div className="arb-modal" onClick={(e) => e.stopPropagation()}>
        <div className="arb-modal-icon">
          <svg viewBox="0 0 24 24" width="32" height="32"><path d="M12 2L1 21h22L12 2zm0 6v6m0 3v.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
        </div>
        <h3>{title}</h3>
        <p>{body}</p>
        <div className="arb-modal-row">
          <button className="arb-modal-btn" onClick={onCancel}>Annuler</button>
          <button className={"arb-modal-btn primary " + (danger ? "danger" : "")} onClick={onConfirm}>Confirmer</button>
        </div>
      </div>
    </div>
  );
}

// ── Variant A: 3-column layout ──────────────────────────────────────────────
function ArbitreColumns({ m, ctrl, accent }) {
  const [confirm, setConfirm] = React.useState(null);
  const lp = m.lastPoint;
  return (
    <div className="arb-screen">
      <ArbitreHeader m={m} />

      <div className="arb-cols">
        <PlayerCol m={m} side="A" accent={accent} onPoint={ctrl.pointA} lastPoint={lp} />
        <div className="arb-center">
          <div className="arb-center-pts">
            <div className="arb-center-pts-lbl">POINT EN COURS</div>
            <div className="arb-center-pts-row">
              <div className="arb-center-pts-val tab" style={{ color: accent }}>
                {window.pointLabel(m.ptsA, m.ptsB, m.inTB)}
              </div>
              <div className="arb-center-pts-dash">·</div>
              <div className="arb-center-pts-val tab">
                {window.pointLabel(m.ptsB, m.ptsA, m.inTB)}
              </div>
            </div>
            {m.inTB && <div className="arb-center-tb">JEU DÉCISIF</div>}
          </div>

          <div className="arb-center-meta">
            <div className="arb-center-meta-row">
              <span>Jeux</span>
              <b className="tab">{m.curGamesA} — {m.curGamesB}</b>
            </div>
            <div className="arb-center-meta-row">
              <span>Sets</span>
              <b className="tab">{m.sets[0]?.a ?? 0} — {m.sets[0]?.b ?? 0}</b>
            </div>
            <div className="arb-center-meta-row">
              <span>Service</span>
              <b>{m.serving === "A" ? m.players.A.name : m.players.B.name}</b>
            </div>
          </div>

          <button className="arb-swap-btn" onClick={ctrl.swap}>
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M3 7h13l-3-3M21 17H8l3 3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Changer le serveur
          </button>
        </div>
        <PlayerCol m={m} side="B" accent={accent} onPoint={ctrl.pointB} lastPoint={lp} />
      </div>

      <ArbitreSecondaryActions
        canUndo={m.history.length > 0}
        onUndo={ctrl.undo}
        onSwap={ctrl.swap}
        onEnd={() => setConfirm({ kind: "end" })}
        onReset={() => setConfirm({ kind: "reset" })}
      />

      {confirm?.kind === "end" && (
        <ConfirmModal
          title="Terminer le match ?"
          body="Cette action validera le score actuel et clôturera le match. Elle ne peut pas être annulée."
          danger
          onConfirm={() => { setConfirm(null); /* end intentionally not destructive of state */ }}
          onCancel={() => setConfirm(null)}
        />
      )}
      {confirm?.kind === "reset" && (
        <ConfirmModal
          title="Réinitialiser le match ?"
          body="Tous les points, jeux et sets seront remis à zéro."
          danger
          onConfirm={() => { ctrl.reset(); setConfirm(null); }}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

function PlayerCol({ m, side, accent, onPoint, lastPoint }) {
  const p = m.players[side];
  const games = side === "A" ? m.curGamesA : m.curGamesB;
  const sets = m.sets[0] ? (side === "A" ? m.sets[0].a : m.sets[0].b) : 0;
  const isServing = m.serving === side;
  const justScored = lastPoint?.side === side && (Date.now() - lastPoint.time < 800);
  return (
    <div className={"arb-col " + (justScored ? "scored" : "")} data-side={side}>
      <div className="arb-col-head">
        {isServing && <i className="arb-col-serve"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="10" fill="#E8F35A"/></svg></i>}
        <div className="arb-col-name">{p.name}</div>
        <div className="arb-col-seed">[{p.seed}]</div>
      </div>
      <div className="arb-col-stats">
        <div className="arb-col-stat">
          <span>JEUX</span>
          <b className="tab">{games}</b>
        </div>
        <div className="arb-col-stat">
          <span>SETS</span>
          <b className="tab">{sets}</b>
        </div>
      </div>
      <button
        className="arb-point-btn"
        style={{ "--accent": accent }}
        disabled={m.status === "TERMINÉ"}
        onClick={onPoint}
      >
        <span className="arb-point-plus">+</span>
        <span className="arb-point-lbl">POINT {side}</span>
      </button>
    </div>
  );
}

// ── Variant B: split with giant centered score ──────────────────────────────
function ArbitreSplit({ m, ctrl, accent }) {
  const [confirm, setConfirm] = React.useState(null);
  const lp = m.lastPoint;
  const justA = lp?.side === "A" && (Date.now() - lp.time < 800);
  const justB = lp?.side === "B" && (Date.now() - lp.time < 800);
  return (
    <div className="arb-screen">
      <ArbitreHeader m={m} />

      <div className="arb-split-score">
        <div className="arb-split-side">
          <div className="arb-split-side-lbl">JOUEUR A</div>
          <div className="arb-split-side-name">{m.players.A.name}</div>
          <div className="arb-split-side-meta">
            <span>SETS <b className="tab">{m.sets[0]?.a ?? 0}</b></span>
            <span>JEUX <b className="tab">{m.curGamesA}</b></span>
            {m.serving === "A" && <i className="arb-split-serve"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="10" fill="#E8F35A"/></svg> Service</i>}
          </div>
        </div>
        <div className="arb-split-center">
          <div className="arb-split-center-lbl">{m.inTB ? "JEU DÉCISIF" : "POINT"}</div>
          <div className="arb-split-center-pts">
            <span className="tab" style={{ color: accent }}>{window.pointLabel(m.ptsA, m.ptsB, m.inTB)}</span>
            <em>·</em>
            <span className="tab">{window.pointLabel(m.ptsB, m.ptsA, m.inTB)}</span>
          </div>
        </div>
        <div className="arb-split-side right">
          <div className="arb-split-side-lbl">JOUEUR B</div>
          <div className="arb-split-side-name">{m.players.B.name}</div>
          <div className="arb-split-side-meta">
            <span>SETS <b className="tab">{m.sets[0]?.b ?? 0}</b></span>
            <span>JEUX <b className="tab">{m.curGamesB}</b></span>
            {m.serving === "B" && <i className="arb-split-serve"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="10" fill="#E8F35A"/></svg> Service</i>}
          </div>
        </div>
      </div>

      <div className="arb-split-zones">
        <button className={"arb-split-zone left " + (justA ? "scored" : "")}
                style={{ "--accent": accent }}
                disabled={m.status === "TERMINÉ"}
                onClick={ctrl.pointA}>
          <span className="arb-split-zone-name">{m.players.A.name}</span>
          <span className="arb-split-zone-plus">＋ POINT</span>
          <span className="arb-split-zone-tap">TAP ICI</span>
        </button>
        <button className={"arb-split-zone right " + (justB ? "scored" : "")}
                style={{ "--accent": accent }}
                disabled={m.status === "TERMINÉ"}
                onClick={ctrl.pointB}>
          <span className="arb-split-zone-name">{m.players.B.name}</span>
          <span className="arb-split-zone-plus">＋ POINT</span>
          <span className="arb-split-zone-tap">TAP ICI</span>
        </button>
      </div>

      <ArbitreSecondaryActions
        canUndo={m.history.length > 0}
        onUndo={ctrl.undo}
        onSwap={ctrl.swap}
        onEnd={() => setConfirm({ kind: "end" })}
        onReset={() => setConfirm({ kind: "reset" })}
      />

      {confirm?.kind === "end" && (
        <ConfirmModal
          title="Terminer le match ?"
          body="Cette action validera le score actuel et clôturera le match."
          danger
          onConfirm={() => setConfirm(null)}
          onCancel={() => setConfirm(null)}
        />
      )}
      {confirm?.kind === "reset" && (
        <ConfirmModal
          title="Réinitialiser le match ?"
          body="Tous les points, jeux et sets seront remis à zéro."
          danger
          onConfirm={() => { ctrl.reset(); setConfirm(null); }}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

function Arbitre({ match, ctrl, variant, accent }) {
  if (variant === "split") return <ArbitreSplit m={match} ctrl={ctrl} accent={accent} />;
  return <ArbitreColumns m={match} ctrl={ctrl} accent={accent} />;
}

Object.assign(window, { Arbitre });
