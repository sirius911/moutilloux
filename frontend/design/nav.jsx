// nav.jsx — top navigation between the 5 interfaces, with stage scaler

const SCREENS = [
  { id: "scoreboard", label: "Live TV",   target: "1920×1080", w: 1920, h: 1080, bg: "#050608" },
  { id: "arbitre-home", label: "Arbitre · liste", target: "iPad 834×1112", w: 834,  h: 1112, bg: "#0A0C11" },
  { id: "arbitre",    label: "Arbitre · score",   target: "iPad 834×1112", w: 834,  h: 1112, bg: "#0A0C11" },
  { id: "poules",     label: "Poules TV", target: "1920×1080", w: 1920, h: 1080, bg: "#050608" },
  { id: "bracket",    label: "Tableau TV",   target: "1920×1080", w: 1920, h: 1080, bg: "#050608" },
  { id: "admin",      label: "Admin",     target: "PC 1440×900", w: 1440, h: 900,  bg: "#F6F7F9" },
  { id: "login",      label: "Login",     target: "1440×900", w: 1440, h: 900,  bg: "#F6F7F9" },
];

// Fit a target (w×h) into the available stage area, keeping aspect.
function useStageScale(stageRef, targetW, targetH) {
  const [scale, setScale] = React.useState(1);
  React.useEffect(() => {
    const compute = () => {
      const el = stageRef.current;
      if (!el) return;
      const { width, height } = el.getBoundingClientRect();
      const pad = 20;
      const sx = (width - pad * 2) / targetW;
      const sy = (height - pad * 2) / targetH;
      setScale(Math.min(sx, sy));
    };
    compute();
    const ro = new ResizeObserver(compute);
    if (stageRef.current) ro.observe(stageRef.current);
    window.addEventListener("resize", compute);
    return () => { ro.disconnect(); window.removeEventListener("resize", compute); };
  }, [stageRef, targetW, targetH]);
  return scale;
}

function NavBar({ current, onChange, status, demoOn, onToggleDemo, accent }) {
  return (
    <div className="nav">
      <div className="nav-left">
        <div className="nav-logo" style={{ "--accent": accent }}>
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M3.5 8.2c5 2.4 12 2.4 17 0M3.5 15.8c5-2.4 12-2.4 17 0" fill="none" stroke="currentColor" strokeWidth="1.6"/>
          </svg>
          <div>
            <div className="nav-logo-name">MOUTILLOUX</div>
            <div className="nav-logo-sub">Open · Édition 2026</div>
          </div>
        </div>
      </div>
      <div className="nav-tabs" role="tablist">
        {SCREENS.map((s) => (
          <button
            key={s.id}
            role="tab"
            aria-selected={current === s.id}
            data-active={current === s.id}
            onClick={() => onChange(s.id)}
            className="nav-tab"
          >
            <span className="nav-tab-label">{s.label}</span>
            <span className="nav-tab-target">{s.target}</span>
          </button>
        ))}
      </div>
      <div className="nav-right">
        <div className="nav-status">
          <i className="nav-dot" style={{ background: status === "EN_COURS" ? "var(--success)" : "var(--ink-3)" }} />
          <span>{status === "EN_COURS" ? "Match en cours" : "Match terminé"}</span>
        </div>
        <button className={"nav-demo " + (demoOn ? "on" : "")} onClick={onToggleDemo}>
          <svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M4 3l9 5-9 5z" fill="currentColor" />
          </svg>
          {demoOn ? "Démo auto" : "Lancer la démo"}
        </button>
      </div>
    </div>
  );
}

function StageFrame({ screen, children }) {
  const stageRef = React.useRef(null);
  const scale = useStageScale(stageRef, screen.w, screen.h);
  return (
    <div ref={stageRef} className="stage" style={{ background: "#000" }}>
      <div className="stage-inner" style={{
        width: screen.w, height: screen.h,
        transform: `translate(-50%, -50%) scale(${scale})`,
        background: screen.bg,
      }}>
        {children}
      </div>
      <div className="stage-badge">
        <span>{screen.label}</span>
        <em>{screen.target}</em>
      </div>
    </div>
  );
}

Object.assign(window, { SCREENS, NavBar, StageFrame, useStageScale });
