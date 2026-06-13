// state.jsx — shared tennis match state + tournament data
// Single set to 5 games, tiebreak at 4-4 (format "1 set à 5 jeux, TB à 4")

const POINT_LABELS = ["0", "15", "30", "40"];

function pointLabel(a, b, inTB) {
  if (inTB) return String(a);
  // Deuce / advantage logic when both >= 3
  if (a >= 3 && b >= 3) {
    if (a === b) return "40";
    if (a === b + 1) return "AV";
    if (a === b - 1) return "—";
    // shouldn't happen after game ends
    return String(a);
  }
  return POINT_LABELS[Math.min(a, 3)];
}

const INITIAL_MATCH = {
  category: "Demi-finale — Simple Homme",
  format: { setsToWin: 1, gamesPerSet: 5, tbAt: 4, tbPoints: 7 },
  players: { A: { name: "Doudou", seed: "A1" }, B: { name: "Cyrille", seed: "B1" } },
  serving: "A",          // current server
  initialServer: "A",    // who started the match (for TB serve rotation)
  sets: [],              // completed sets: [{a, b, tb?: [a,b]}]
  curGamesA: 0,
  curGamesB: 0,
  ptsA: 0,
  ptsB: 0,
  inTB: false,
  status: "EN_COURS",    // EN_COURS | TERMINÉ
  winner: null,
  history: [],           // stack of prior states for undo
  lastPoint: null,       // { side, time } for animation
};

function cloneForHistory(m) {
  // Drop history+lastPoint to avoid quadratic growth
  const { history, lastPoint, ...rest } = m;
  return JSON.parse(JSON.stringify(rest));
}

function awardPoint(m, side) {
  if (m.status === "TERMINÉ") return m;
  const next = JSON.parse(JSON.stringify(m));
  next.history = [...m.history, cloneForHistory(m)].slice(-50);
  next.lastPoint = { side, time: Date.now() };

  if (next.inTB) {
    if (side === "A") next.ptsA++; else next.ptsB++;
    const need = next.format.tbPoints;
    const a = next.ptsA, b = next.ptsB;
    // Tiebreak serve switches every 2 points after the first
    const totalPts = a + b;
    if (totalPts > 0) {
      // First server serves 1, then alternate every 2
      const flips = Math.floor((totalPts + 1) / 2);
      next.serving = (flips % 2 === 0) ? next.initialServer : (next.initialServer === "A" ? "B" : "A");
    }
    if ((a >= need || b >= need) && Math.abs(a - b) >= 2) {
      // TB won → set won by leader
      const winner = a > b ? "A" : "B";
      const setRecord = { a: next.curGamesA + (winner === "A" ? 1 : 0),
                          b: next.curGamesB + (winner === "B" ? 1 : 0),
                          tb: [a, b] };
      next.sets.push(setRecord);
      finishMatch(next, winner);
    }
    return next;
  }

  if (side === "A") next.ptsA++; else next.ptsB++;
  // Check game end
  const a = next.ptsA, b = next.ptsB;
  const gameWinner = checkGameWinner(a, b);
  if (gameWinner) {
    if (gameWinner === "A") next.curGamesA++; else next.curGamesB++;
    next.ptsA = 0; next.ptsB = 0;
    // Switch server
    next.serving = next.serving === "A" ? "B" : "A";

    const ga = next.curGamesA, gb = next.curGamesB;
    const need = next.format.gamesPerSet;
    const tbAt = next.format.tbAt;
    // Set win conditions: reach `need` games with 2-game lead (until TB threshold)
    if (ga === tbAt && gb === tbAt) {
      // Enter tiebreak
      next.inTB = true;
    } else if ((ga >= need && ga - gb >= 1) || (gb >= need && gb - ga >= 1)) {
      // Set won
      const winner = ga > gb ? "A" : "B";
      next.sets.push({ a: ga, b: gb });
      finishMatch(next, winner);
    }
  }
  return next;
}

function checkGameWinner(a, b) {
  if (a >= 4 && a - b >= 2) return "A";
  if (b >= 4 && b - a >= 2) return "B";
  return null;
}

function finishMatch(m, winner) {
  // Single-set format → match ends with the set
  m.status = "TERMINÉ";
  m.winner = winner;
  m.curGamesA = 0;
  m.curGamesB = 0;
  m.ptsA = 0;
  m.ptsB = 0;
  m.inTB = false;
}

function undoPoint(m) {
  if (!m.history.length) return m;
  const prev = m.history[m.history.length - 1];
  return { ...prev, history: m.history.slice(0, -1), lastPoint: null };
}

function resetMatch(m) {
  return { ...JSON.parse(JSON.stringify(INITIAL_MATCH)),
           players: m.players, category: m.category };
}

function switchServer(m) {
  if (m.status === "TERMINÉ") return m;
  return { ...m, serving: m.serving === "A" ? "B" : "A",
           history: [...m.history, cloneForHistory(m)].slice(-50) };
}

// ── React hook ──────────────────────────────────────────────────────────────
function useMatch() {
  const [m, setM] = React.useState(INITIAL_MATCH);
  return {
    match: m,
    pointA: () => setM((x) => awardPoint(x, "A")),
    pointB: () => setM((x) => awardPoint(x, "B")),
    undo:   () => setM(undoPoint),
    reset:  () => setM(resetMatch),
    swap:   () => setM(switchServer),
    setPlayers: (A, B) => setM((x) => ({ ...x, players: { A: { ...x.players.A, name: A }, B: { ...x.players.B, name: B } } })),
    setCategory: (c) => setM((x) => ({ ...x, category: c })),
  };
}

// ── Static tournament data ──────────────────────────────────────────────────
const PLAYERS = [
  { id: "p1", first: "Doudou",  last: "Mercier",   lic: "FFT-58210", seed: "A1" },
  { id: "p2", first: "Cyrille", last: "Rougier",   lic: "FFT-44102", seed: "B1" },
  { id: "p3", first: "Maxime",  last: "Vautier",   lic: "FFT-78903", seed: "C1" },
  { id: "p4", first: "Marc",    last: "Delanoue",  lic: "FFT-12055", seed: "D1" },
  { id: "p5", first: "Seb.Lec", last: "Lecomte",   lic: "FFT-93311", seed: "A2" },
  { id: "p6", first: "Seb.La",  last: "Lavigne",   lic: "FFT-26604", seed: "B2" },
  { id: "p7", first: "Ambre",   last: "Bouchard",  lic: "FFT-71820", seed: "C2" },
  { id: "p8", first: "Huguette",last: "Marin",     lic: "FFT-30007", seed: "D2" },
];

const POULES = [
  { id: "A", title: "Poule A", rows: [
    { player: "Doudou",  v: 3, d: 0, jeux: "15-4",  pts: 9, q: true },
    { player: "Seb.Lec", v: 2, d: 1, jeux: "12-9",  pts: 6, q: true },
    { player: "Hugo R.", v: 1, d: 2, jeux: "8-12",  pts: 3, q: false },
    { player: "Léa B.",  v: 0, d: 3, jeux: "4-14",  pts: 0, q: false },
  ], grid: [
    ["—",     "6-4",  "6-2",  "6-1"],
    ["4-6",   "—",    "5-7",  "6-3"],
    ["2-6",   "7-5",  "—",    "3-6"],
    ["1-6",   "3-6",  "6-3",  "—"],
  ]},
  { id: "B", title: "Poule B", rows: [
    { player: "Cyrille", v: 3, d: 0, jeux: "15-6",  pts: 9, q: true },
    { player: "Seb.La",  v: 2, d: 1, jeux: "11-10", pts: 6, q: true },
    { player: "Théo D.", v: 1, d: 2, jeux: "9-12",  pts: 3, q: false },
    { player: "Inès V.", v: 0, d: 3, jeux: "5-12",  pts: 0, q: false },
  ], grid: [
    ["—",     "6-3",  "5-7",  "6-2"],
    ["3-6",   "—",    "6-4",  "6-4"],
    ["7-5",   "4-6",  "—",    "4-6"],
    ["2-6",   "4-6",  "6-4",  "—"],
  ]},
  { id: "C", title: "Poule C", rows: [
    { player: "Maxime",  v: 3, d: 0, jeux: "15-2",  pts: 9, q: true },
    { player: "Ambre",   v: 2, d: 1, jeux: "13-8",  pts: 6, q: true },
    { player: "Tom F.",  v: 1, d: 2, jeux: "7-11",  pts: 3, q: false },
    { player: "Zoé M.",  v: 0, d: 3, jeux: "3-13",  pts: 0, q: false },
  ], grid: [
    ["—",     "6-1",  "6-0",  "6-1"],
    ["1-6",   "—",    "6-3",  "6-1"],
    ["0-6",   "3-6",  "—",    "6-2"],
    ["1-6",   "1-6",  "2-6",  "—"],
  ]},
  { id: "D", title: "Poule D", rows: [
    { player: "Marc",      v: 3, d: 0, jeux: "15-7",  pts: 9, q: true },
    { player: "Huguette",  v: 2, d: 1, jeux: "12-10", pts: 6, q: true },
    { player: "Nora K.",   v: 1, d: 2, jeux: "8-13",  pts: 3, q: false },
    { player: "Eliott S.", v: 0, d: 3, jeux: "6-14",  pts: 0, q: false },
  ], grid: [
    ["—",     "6-4",  "6-2",  "6-3"],
    ["4-6",   "—",    "6-4",  "6-4"],
    ["2-6",   "4-6",  "—",    "6-3"],
    ["3-6",   "4-6",  "3-6",  "—"],
  ]},
];

// Bracket (Quarts → Demi → Finale)
const BRACKET = {
  qf: [
    { id: "QF1", a: { seed: "A1", name: "Doudou",  score: "6-2" }, b: { seed: "D2", name: "Huguette", score: "3-6 4-6" }, winner: "A", time: "10:30" },
    { id: "QF2", a: { seed: "C1", name: "Maxime",  score: "6-4" }, b: { seed: "B2", name: "Seb.La",   score: "4-6 5-7" }, winner: "A", time: "11:00" },
    { id: "QF3", a: { seed: "B1", name: "Cyrille", score: "6-3" }, b: { seed: "D1", name: "Marc",     score: "3-6 6-7" }, winner: "A", time: "11:30" },
    { id: "QF4", a: { seed: "A2", name: "Seb.Lec", score: "6-1" }, b: { seed: "C2", name: "Ambre",    score: "1-6 2-6" }, winner: "A", time: "12:00" },
  ],
  sf: [
    { id: "SF1", a: { seed: "A1", name: "Doudou",  score: "6-4" }, b: { seed: "C1", name: "Maxime",   score: "4-6 3-6" }, winner: "A", time: "14:00", live: true },
    { id: "SF2", a: { seed: "B1", name: "Cyrille", score: "—" },   b: { seed: "A2", name: "Seb.Lec",  score: "—" },       winner: null, time: "15:00" },
  ],
  f: [
    { id: "F",   a: { seed: "?", name: "—" }, b: { seed: "?", name: "—" }, winner: null, time: "17:00" },
  ],
};

const MATCHES_KANBAN = {
  backlog: [
    { id: "m1", a: "Doudou", b: "Marc", type: "Poule A", round: "J2" },
    { id: "m2", a: "Ambre", b: "Zoé M.", type: "Poule C", round: "J3" },
    { id: "m3", a: "Théo D.", b: "Inès V.", type: "Poule B", round: "J3" },
  ],
  queue: [
    { id: "m4", a: "Seb.Lec", b: "Hugo R.", type: "Poule A", round: "J3", court: "Central" },
    { id: "m5", a: "Cyrille", b: "Seb.La", type: "Demi B", round: "SF", featured: true },
  ],
  done: [
    { id: "m6", a: "Doudou", b: "Huguette", type: "QF1", score: "6-2" },
    { id: "m7", a: "Maxime", b: "Seb.La", type: "QF2", score: "6-4" },
    { id: "m8", a: "Marc", b: "Eliott S.", type: "Poule D", score: "6-3" },
  ],
};

// ── Editions & événements (gestion du tournoi) ──────────────────────────────
const EDITIONS = [
  { id: "e2026", name: "Open de Moutilloux 2026", year: 2026, active: true,  start: "25 mai 2026", end: "02 juin 2026", events: 4, players: 48, status: "EN COURS" },
  { id: "e2025", name: "Open de Moutilloux 2025", year: 2025, active: false, start: "27 mai 2025", end: "04 juin 2025", events: 3, players: 42, status: "TERMINÉ" },
  { id: "e2024", name: "Open de Moutilloux 2024", year: 2024, active: false, start: "28 mai 2024", end: "05 juin 2024", events: 3, players: 38, status: "TERMINÉ" },
];

const EVENTS = [
  { id: "ev1", name: "Simple Homme",     mode: "S", category: "Senior", players: 16, status: "Phase finale", color: "#FFC83D", progress: 78 },
  { id: "ev2", name: "Simple Femme",     mode: "S", category: "Senior", players: 12, status: "Phase de poules", color: "#22E27F", progress: 45 },
  { id: "ev3", name: "Double Mixte",     mode: "D", category: "Senior", players: 16, status: "Phase de poules", color: "#00E5EE", progress: 32 },
  { id: "ev4", name: "Simple Homme +45", mode: "S", category: "+45 ans", players: 8, status: "À planifier", color: "#C4B5FD", progress: 0 },
];

// ── Matchs pour l'arbitre (sélection) ──────────────────────────────────────
const ARB_MATCHES = [
  { id: "am1", a: "Doudou", b: "Maxime",  event: "Simple Homme", stage: "Demi-finale", court: "Central", time: "14:00", status: "LIVE", score: "1 set · 4–3", featured: true },
  { id: "am2", a: "Cyrille", b: "Seb.Lec", event: "Simple Homme", stage: "Demi-finale", court: "Court 2", time: "15:00", status: "SCHEDULED" },
  { id: "am3", a: "Ambre / Marc", b: "Léa / Tom", event: "Double Mixte", stage: "Poule A · J3", court: "Court 3", time: "15:30", status: "SCHEDULED" },
  { id: "am4", a: "Huguette", b: "Nora K.", event: "Simple Femme", stage: "Poule B · J3", court: "Court 4", time: "16:00", status: "SCHEDULED" },
  { id: "am5", a: "Seb.La",   b: "Théo D.", event: "Simple Homme +45", stage: "Poule A · J2", court: "Central", time: "16:30", status: "SCHEDULED" },
  { id: "am6", a: "Doudou",   b: "Huguette", event: "Simple Homme", stage: "Quart 1", court: "Central", time: "10:30", status: "FINISHED", score: "6–2 (terminé)" },
];

const COURTS = ["Central", "Court 2", "Court 3", "Court 4", "Terre battue"];

Object.assign(window, {
  INITIAL_MATCH, useMatch, pointLabel,
  PLAYERS, POULES, BRACKET, MATCHES_KANBAN,
  EDITIONS, EVENTS, ARB_MATCHES, COURTS,
});
