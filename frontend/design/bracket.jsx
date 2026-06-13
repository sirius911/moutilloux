// bracket.jsx — TV bracket display (1920×1080), 2 variants
// "lines"    — SVG connection lines, classic bracket
// "floating" — Floating cards with subtle connectors

function Bracket({ variant, accent }) {
  if (variant === "floating") return <BracketFloating accent={accent} />;
  return <BracketLines accent={accent} />;
}

// Layout constants — single source of truth shared between cards and SVG paths.
// Body is 1920×928 (1080 − 96 header − 56 footer). viewBox maps 1:1.
const LB = {
  // Column left edges
  qfX: 80, sfX: 540, fX: 1000, trX: 1420,
  // Card widths
  cardW: 380, finalW: 380, trW: 420,
  // Card heights (measured: regular cards render 120px, final 128px)
  cardH: 120, finalH: 128, trH: 186,
  // Top edges (body-local Y) — chosen so each SF sits at the midpoint of
  // its two QF feeders, the final sits at the midpoint of the SFs, and the
  // trophy mirrors the final.
  qf: [70, 230, 580, 740],   // centers: 130, 290, 640, 800
  sf: [150, 660],            // centers: 210 = mid(130,290) ; 720 = mid(640,800)
  f:  401,                   // center: 465 = mid(210, 720)
  tr: 372,                   // trH=186 → center 465
};
// Card vertical centers
const cy = (top, h) => top + h / 2;

function elbowPath(fromX, fromY, toX, toY) {
  if (fromY === toY) return `M ${fromX} ${fromY} H ${toX}`;
  const midX = fromX + (toX - fromX) / 2;
  return `M ${fromX} ${fromY} H ${midX} V ${toY} H ${toX}`;
}

function BracketLines({ accent }) {
  const b = window.BRACKET;
  const liveSf = b.sf.findIndex((s) => s.live);

  // Pre-compute line paths from constants
  const qfToSf = b.qf.map((_, i) => {
    const sfIdx = Math.floor(i / 2);
    return {
      d: elbowPath(LB.qfX + LB.cardW, cy(LB.qf[i], LB.cardH),
                   LB.sfX, cy(LB.sf[sfIdx], LB.cardH)),
      live: sfIdx === liveSf,
    };
  });
  const sfToF = b.sf.map((_, i) => ({
    d: elbowPath(LB.sfX + LB.cardW, cy(LB.sf[i], LB.cardH),
                 LB.fX, cy(LB.f, LB.finalH)),
    live: i === liveSf,
  }));
  const fToTr = {
    d: elbowPath(LB.fX + LB.finalW, cy(LB.f, LB.finalH),
                 LB.trX, cy(LB.tr, LB.trH)),
  };

  return (
    <div className="brk-screen">
      <div className="brk-bg" />
      <header className="brk-header">
        <div className="brk-header-left">
          <div className="tv-tournament-mark" style={{ color: accent }}>
            <svg viewBox="0 0 24 24" width="32" height="32">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.4" />
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.4"/>
            </svg>
          </div>
          <div>
            <div className="brk-title">TABLEAU FINAL</div>
            <div className="brk-sub">Simple Homme · Phase à élimination directe</div>
          </div>
        </div>
        <div className="brk-stage-labels">
          <span>QUARTS DE FINALE</span>
          <span>DEMI-FINALES</span>
          <span>FINALE</span>
          <span style={{ color: accent }}>VAINQUEUR</span>
        </div>
      </header>

      <div className="brk-body brk-body-lines">
        {/* Background guide rails — vertical dotted lines aligned to columns */}
        <svg className="brk-rails" viewBox="0 0 1920 928" preserveAspectRatio="none" aria-hidden="true">
          {[LB.qfX, LB.sfX, LB.fX, LB.trX].map((x, i) => (
            <line key={i} x1={x + (i === 3 ? LB.trW : LB.cardW) / 2} x2={x + (i === 3 ? LB.trW : LB.cardW) / 2}
                  y1="60" y2="868" stroke="rgba(255,255,255,0.04)" strokeWidth="1" strokeDasharray="2 6" />
          ))}
        </svg>

        <svg className="brk-lines" viewBox="0 0 1920 928" preserveAspectRatio="none" aria-hidden="true">
          {qfToSf.map((l, i) => (
            <path key={"qfsf" + i} d={l.d} className="brk-line" data-live={l.live ? "true" : undefined} />
          ))}
          {sfToF.map((l, i) => (
            <path key={"sff" + i} d={l.d} className="brk-line" data-live={l.live ? "true" : undefined} />
          ))}
          <path d={fToTr.d} className="brk-line" />

          {/* Joint dots at column meeting points for that broadcast feel */}
          {[
            ...b.qf.map((_, i) => ({ x: LB.qfX + LB.cardW, y: cy(LB.qf[i], LB.cardH) })),
            ...b.sf.map((_, i) => ({ x: LB.sfX, y: cy(LB.sf[i], LB.cardH) })),
            ...b.sf.map((_, i) => ({ x: LB.sfX + LB.cardW, y: cy(LB.sf[i], LB.cardH) })),
            { x: LB.fX, y: cy(LB.f, LB.finalH) },
            { x: LB.fX + LB.finalW, y: cy(LB.f, LB.finalH) },
            { x: LB.trX, y: cy(LB.tr, LB.trH) },
          ].map((p, i) => (
            <circle key={"j" + i} cx={p.x} cy={p.y} r="2.5" className="brk-joint" />
          ))}
        </svg>

        {b.qf.map((m, i) => (
          <BracketMatch key={m.id} m={m} accent={accent}
            style={{ left: LB.qfX, top: LB.qf[i], width: LB.cardW }} />
        ))}
        {b.sf.map((m, i) => (
          <BracketMatch key={m.id} m={m} accent={accent}
            style={{ left: LB.sfX, top: LB.sf[i], width: LB.cardW }} />
        ))}
        <BracketMatch m={b.f[0]} accent={accent} final
          style={{ left: LB.fX, top: LB.f, width: LB.finalW }} />

        <div className="brk-winner" style={{ left: LB.trX, top: LB.tr, width: LB.trW }}>
          <div className="brk-winner-trophy" style={{ color: accent }}>
            <svg viewBox="0 0 32 32" width="48" height="48"><path d="M6 4h20v6a8 8 0 01-8 8h-4a8 8 0 01-8-8V4zm0 0H2v3a3 3 0 003 3M26 4h4v3a3 3 0 01-3 3M12 18v4M20 18v4M9 26h14v2H9z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
          </div>
          <div className="brk-winner-lbl">VAINQUEUR</div>
          <div className="brk-winner-name">À DÉSIGNER</div>
          <div className="brk-winner-cup">COUPE MOUTILLOUX 2026</div>
        </div>
      </div>

      <footer className="brk-footer">
        <span><i className="brk-foot-dot live" /> EN DIRECT · SF1 — Doudou&nbsp;vs&nbsp;Maxime</span>
        <span><i className="brk-foot-dot soon" /> SF2 à 15:00 · Cyrille&nbsp;vs&nbsp;Seb.Lec</span>
        <span><i className="brk-foot-dot final" /> Finale 17:00</span>
      </footer>
    </div>
  );
}

function BracketMatch({ m, accent, style, final }) {
  return (
    <div className={"brk-match " + (m.live ? "live " : "") + (final ? "final " : "")} style={style}>
      {m.live && <i className="brk-match-live"><span /> EN DIRECT</i>}
      <div className="brk-match-time">{m.time}</div>
      <div className={"brk-slot " + (m.winner === "A" ? "win" : "")}>
        <span className="brk-seed" style={{ background: accent }}>{m.a.seed}</span>
        <span className="brk-name">{m.a.name}</span>
        <span className="brk-score tab">{m.a.score}</span>
      </div>
      <div className={"brk-slot " + (m.winner === "B" ? "win" : "")}>
        <span className="brk-seed">{m.b.seed}</span>
        <span className="brk-name">{m.b.name}</span>
        <span className="brk-score tab">{m.b.score}</span>
      </div>
    </div>
  );
}

// ── Variant 2: floating cards ──────────────────────────────────────────────
function BracketFloating({ accent }) {
  const b = window.BRACKET;
  return (
    <div className="brk-screen brk-float">
      <div className="brk-bg" />
      <header className="brk-header">
        <div className="brk-header-left">
          <div className="tv-tournament-mark" style={{ color: accent }}>
            <svg viewBox="0 0 24 24" width="32" height="32">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.4" />
              <path d="M2 9c5 2.5 15 2.5 20 0M2 15c5-2.5 15-2.5 20 0" fill="none" stroke="currentColor" strokeWidth="1.4"/>
            </svg>
          </div>
          <div>
            <div className="brk-title">TABLEAU FINAL</div>
            <div className="brk-sub">Cards flottantes · Élimination directe</div>
          </div>
        </div>
        <div className="brk-stage-labels">
          <span>QF</span>
          <span>SF</span>
          <span>F</span>
          <span style={{ color: accent }}>★</span>
        </div>
      </header>

      <div className="brk-float-body">
        <div className="brk-float-col">
          <div className="brk-float-stage">QUARTS</div>
          {b.qf.map((m) => (
            <BracketFloatCard key={m.id} m={m} accent={accent} />
          ))}
        </div>
        <BracketConnector accent={accent} />
        <div className="brk-float-col">
          <div className="brk-float-stage">DEMI-FINALES</div>
          <div style={{ height: 80 }} />
          {b.sf.map((m) => (
            <React.Fragment key={m.id}>
              <BracketFloatCard m={m} accent={accent} big />
              <div style={{ height: 220 }} />
            </React.Fragment>
          ))}
        </div>
        <BracketConnector accent={accent} />
        <div className="brk-float-col">
          <div className="brk-float-stage">FINALE</div>
          <div style={{ height: 280 }} />
          <BracketFloatCard m={b.f[0]} accent={accent} big />
        </div>
        <div className="brk-float-col winner-col">
          <div className="brk-float-stage" style={{ color: accent }}>VAINQUEUR</div>
          <div style={{ height: 240 }} />
          <div className="brk-float-trophy" style={{ "--accent": accent }}>
            <svg viewBox="0 0 32 32" width="56" height="56"><path d="M6 4h20v6a8 8 0 01-8 8h-4a8 8 0 01-8-8V4zm0 0H2v3a3 3 0 003 3M26 4h4v3a3 3 0 01-3 3M12 18v4M20 18v4M9 26h14v2H9z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
            <div className="brk-float-trophy-lbl">À DÉSIGNER</div>
            <div className="brk-float-trophy-sub">Finale à 17:00</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BracketFloatCard({ m, accent, big }) {
  return (
    <div className={"brk-float-card " + (m.live ? "live " : "") + (big ? "big " : "")}>
      {m.live && <span className="brk-float-live"><i /> LIVE</span>}
      <div className="brk-float-time">{m.time}&nbsp;·&nbsp;Central</div>
      <div className={"brk-float-slot " + (m.winner === "A" ? "win" : "")}>
        <span className="brk-float-seed" style={{ background: accent }}>{m.a.seed}</span>
        <span className="brk-float-name">{m.a.name}</span>
        <span className="brk-float-score tab">{m.a.score}</span>
      </div>
      <div className={"brk-float-slot " + (m.winner === "B" ? "win" : "")}>
        <span className="brk-float-seed">{m.b.seed}</span>
        <span className="brk-float-name">{m.b.name}</span>
        <span className="brk-float-score tab">{m.b.score}</span>
      </div>
    </div>
  );
}

function BracketConnector({ accent }) {
  return (
    <div className="brk-connector">
      <svg viewBox="0 0 60 760" preserveAspectRatio="none">
        <path d="M 0 100 Q 30 100 30 380 Q 30 100 60 100" stroke={accent} strokeWidth="1" fill="none" opacity="0.4" />
        <path d="M 0 280 Q 30 280 30 380 Q 30 280 60 280" stroke="rgba(255,255,255,0.2)" strokeWidth="1" fill="none" />
        <path d="M 0 480 Q 30 480 30 380 Q 30 480 60 480" stroke="rgba(255,255,255,0.2)" strokeWidth="1" fill="none" />
        <path d="M 0 660 Q 30 660 30 380 Q 30 660 60 660" stroke="rgba(255,255,255,0.2)" strokeWidth="1" fill="none" />
      </svg>
    </div>
  );
}

Object.assign(window, { Bracket });
