// ─── Entités de base ───────────────────────────────────────────────────────

export interface Player {
  id: number
  firstName: string
  lastName: string
  fullName: string
  gender: 'M' | 'F' | 'O'
  birthYear: number | null
  licenseNumber: string
  email: string
  phone: string
}

export interface Entry {
  id: number
  displayName: string         // nom affiché (joueur ou équipe)
  player: Player | null       // null pour les doubles
  teamName?: string           // doubles
  seedHint: number | null
  groupId: number | null
  groupName: string | null    // "A", "B", etc.
  withdrawn?: boolean
}

// ─── Tournoi ────────────────────────────────────────────────────────────────

export type CategoryMode = 'S' | 'D'
export type EventStatus = 'INSCRIPTION' | 'EN_COURS' | 'TERMINEE'

export interface Edition {
  id: number
  name: string
  year: number
  isActive: boolean
  startDt: string | null      // ISO 8601 (ou null)
  endDt: string | null
  eventsCount: number         // nb d'épreuves de l'édition
  // Agrégats sprint-02 (toutes épreuves de l'édition)
  distinctPlayersCount: number
  matchesFinished: number
  matchesTotal: number
  defaultMatchDurationMin: number
}

export interface Event {
  id: number
  editionId: number
  name: string                // "Simple Homme" (= nom de la catégorie)
  categoryMode: CategoryMode
  // ── Config (Phase 9) ──
  categoryId: number
  groupSizeDefault: number    // 3 | 4
  qualifiedPerGroup: number   // 1 | 2
  notes: string
  // ── Indicateurs d'état ──
  status: EventStatus
  entriesCount: number
  hasGroups: boolean
  hasBracket: boolean
  hasBracketStarted: boolean
  hasThirdPlace: boolean
}

// ─── Référentiels de configuration (Phase 9) ────────────────────────────────

export interface Category {
  id: number
  name: string
  mode: CategoryMode
  eventsCount: number         // nb d'épreuves qui l'utilisent (toutes éditions)
}

export interface Court {
  id: number
  name: string
  matchCount: number          // nb de matchs rattachés
}

// ─── Groupes / Standings ────────────────────────────────────────────────────

export interface StandingRow {
  entryId: number
  rank: number
  name: string               // display name du joueur/équipe
  wins: number
  losses: number
  gamesRatio: string         // "12/8"
  points: number
  qualified: boolean
  withdrawn?: boolean
}

export interface GridCell {
  score: string | null       // "6-4" ou null (diagonale)
}

export interface Group {
  id: number
  name: string               // "A", "B", "C", "D"
  standings: StandingRow[]
  grid: GridCell[][]         // matrice n×n
}

// ─── Match ──────────────────────────────────────────────────────────────────

export type MatchStage = 'GROUP' | 'QF' | 'SF' | 'F' | 'P3'
export type MatchStatus = 'SCHEDULED' | 'LIVE' | 'FINISHED' | 'CANCELED'
export type MatchSide = 'A' | 'B'

export interface SetResult {
  a: number
  b: number
  tb?: [number, number]
}

export interface Match {
  id: number
  eventId: number
  stage: MatchStage
  stageLabel: string         // "Quart de finale"
  formatLabel: string        // "1 set à 5 · TB à 4", "BO3 · TB à 4", "Manuel"
  status: MatchStatus
  court: string | null
  orderIndex: number | null
  isFeatured: boolean
  bracketSlot: string | null // "QF1", "SF2", "F1"

  // Participants
  sideA: Entry | null
  sideB: Entry | null
  sideALabel: string | null  // "A1", "D2"
  sideBLabel: string | null

  // Score
  server: MatchSide
  matchFormat: string        // "GROUP_SET5_TB_4_4" | "QF_SET5_TB_5_5" | "NORMAL_1SET" | "BO3" | "MANUAL"
  bestOf: number
  gamesToWin: number
  tbAt: number
  tbPointsToWin: number
  tbWinByTwo: boolean
  decidingSetMode: string      // "FULL_SET" | "SUPER_TB"
  decidingTbPointsToWin: number
  setsA: number
  setsB: number
  gamesA: number
  gamesB: number
  pointsA: number
  pointsB: number
  tbActive: boolean
  tbPointsA: number
  tbPointsB: number
  setScores: SetResult[]
  winnerSide: MatchSide | null
  isWalkover?: boolean

  // Points affichage tennis (retournés par le backend)
  displayPointA: string     // "0", "15", "30", "40", "AV"
  displayPointB: string

  // Planning
  scheduledTime: string | null
  startedAt: string | null
  finishedAt: string | null
  updatedAt: string

  // Clock (durée en cours)
  clock?: string            // "42mn"

  // Affiche (sprint 24)
  posterUrl: string | null
}

// ─── Bracket ────────────────────────────────────────────────────────────────

export interface BracketSlot {
  slot: string             // "QF1", "QF2", "SF1", "F1"
  stage: MatchStage
  match: Match | null
}

export interface Bracket {
  qf: BracketSlot[]        // 4 slots
  sf: BracketSlot[]        // 2 slots
  f: BracketSlot[]         // 1 slot
  p3: BracketSlot[]        // 1 slot (petite finale)
}

// ─── Kanban ─────────────────────────────────────────────────────────────────

export interface KanbanData {
  backlog: Match[]          // SCHEDULED sans orderIndex
  queue: Match[]            // SCHEDULED avec orderIndex (ordonné)
  finished: Match[]         // FINISHED
}

// ─── Calendrier ──────────────────────────────────────────────────────────────

export interface PlayDay {
  id: number
  editionId: number
  date: string              // "YYYY-MM-DD"
  startTime: string         // "HH:MM"
  targetEndTime: string     // "HH:MM"
}

export interface Break {
  id: number
  playDayId: number
  orderIndex: number
  durationMin: number
  label: string
}

export interface CalendarDay extends PlayDay {
  breaks: Break[]
  matches: Match[]
}

export interface CalendarData {
  playDays: CalendarDay[]
  unscheduled: Match[]      // SCHEDULED, GROUP, sans order_index
  canceled: Match[]         // CANCELED, GROUP — retirés de leur journée
}

// ─── TV — état chaud (polling /api/tv/state/) ──────────────────────────────

export interface TvStakeStanding {
  entryId: number
  rank: number
  name: string
  wins: number
  losses: number
  points: number
  qualified: boolean
}

export type TvStake =
  | { kind: 'group'; groupName: string; eventName: string; standings: TvStakeStanding[] }
  | { kind: 'bracket'; eventName: string; bracket: Bracket }

export interface TvState {
  editionYear: number | null
  now: string               // "15h42"
  hero: Match | null
  next: Match | null
  stake: TvStake | null
}

// ─── TV — contenu froid du carousel (polling /api/tv/idle/) ───────────────

export interface TvStats {
  matchesFinished: number
  matchesTotal: number
  entriesCount: number
  eventsCount: number
}

export interface TvEventGroup {
  id: number
  name: string
  standings: TvStakeStanding[]
}

export interface TvEvent {
  id: number
  name: string
  groups: TvEventGroup[]
  bracket: Bracket | null
}

export type TvProgrammeDay = 'today' | 'tomorrow' | 'finished'

export interface TvProgramme {
  day: TvProgrammeDay
  playDay: PlayDay | null
  upcoming: Match[]          // N ≤ 6, à partir du next
}

export interface TvAnnouncement {
  id: number
  message: string
}

export interface TvIdleData {
  stats: TvStats | null
  recentResults: Match[]
  events: TvEvent[]
  programme: TvProgramme
  announcements: TvAnnouncement[]
}

// ─── Annonces TV — CRUD admin (sprint 22/23) ────────────────────────────────

export interface Announcement {
  id: number
  editionId: number
  message: string
  isActive: boolean
}
