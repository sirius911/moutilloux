# Handoff : Moutilloux — App de gestion de tournoi de tennis

## Vue d'ensemble

Application web de gestion de tournoi de tennis en temps réel, articulée autour de **deux comptes nominatifs** + un accès public.

| Accès | Authentification | Device | Mode | Rôle |
|---|---|---|---|---|
| **Organisateur** | Compte fixe | PC (1440×900) | Light | Admin panel — joueurs, poules, matchs, tableau final, gestion de tournoi |
| **Arbitre** | Compte fixe | iPad portrait (834×1112) | Dark | Liste des matchs + saisie des points en direct |
| **Public** (TV, Poules, Tableau) | Aucune — accès libre | TV / écran grand format (1920×1080) | Dark | Scoreboard live, classement des poules, tableau final |

> Il n'y a que **2 comptes utilisateurs réels** : l'organisateur et l'arbitre. L'arbitre désigné du match utilise une tablette dédiée déjà connectée ; l'organisateur accède à l'administration depuis un PC. Tout le reste (TV, Poules, Tableau final) est **public** et accessible sans authentification depuis n'importe quel écran sur le réseau local.

Les écrans publics consomment le **même état de match** que celui mis à jour par l'Arbitre — un point ajouté côté tablette doit apparaître instantanément sur le scoreboard TV (via WebSocket / SSE / polling court selon l'archi backend choisie).

---

## À propos des fichiers de design

Les fichiers livrés (`design/*.html`, `*.css`, `*.jsx`) sont des **références de design** — un prototype HTML/React/Babel **présentationnel** qui sert de cahier des charges visuel et comportemental. Ce n'est **pas du code à copier-coller en production**.

L'objectif est de **recréer ces écrans dans l'environnement cible de l'application** (Next.js + Tailwind, Vue + Pinia, SwiftUI, Flutter, etc.), en respectant les conventions du codebase existant. Si aucun environnement n'est encore en place, choisir une stack moderne adaptée (suggestion : **React + Vite + TypeScript** pour la web app, **Zustand** ou **Redux Toolkit** pour l'état, **CSS Modules** ou **vanilla-extract** ou **Tailwind** au choix, plus un layer temps réel — **Socket.io** ou **Supabase Realtime**).

Les fichiers CSS livrés utilisent des **CSS custom properties** (variables) sans framework. Tu peux soit reprendre les tokens dans un fichier `tokens.css` global, soit les porter dans un design system (Tailwind config, theme provider, etc.).

## Fidélité

**Hi-fi.** Tous les écrans sont des maquettes pixel-perfect avec couleurs finales, typographie, espacements et interactions définitifs. Le développeur doit recréer l'UI à l'identique en utilisant les libs et patterns du codebase cible.

---

## Stack technique (recommandations)

| Couche | Reco |
|---|---|
| Front | React 18+ / Vue 3 / Svelte 5 |
| Routing | Routes par rôle. **Accès authentifié** : `/admin/*` (organisateur), `/arbitre`, `/arbitre/:matchId`. **Accès public** : `/tv/live`, `/tv/poules`, `/tv/bracket`, `/login`. |
| État local | Zustand / Pinia / Svelte stores |
| État temps réel | WebSocket via Socket.io ou Supabase Realtime. Source de vérité côté serveur ; clients abonnés au flux d'événements de match. |
| Persistance | Postgres (relationnel — bracket, poules, joueurs) |
| Auth | **2 comptes seed-és en base** : `organisateur` + `arbitre`. Magic link, mot de passe ou PIN court suffit. Pas de signup, pas de récupération self-service (admin réinitialise manuellement). |
| Drag & drop (admin) | `dnd-kit` (React) ou équivalent |
| Animations | CSS transitions pour scores, Framer Motion / Auto-animate pour les transitions de liste |

---

## Modèle de données

### Entités principales

```ts
// Tournoi
type Tournament = {
  id: string;
  name: string;        // "Open de Moutilloux"
  edition: string;     // "2026"
  startDate: Date;
  endDate: Date;
};

// Épreuve (au sein d'un tournoi)
type Event = {
  id: string;
  tournamentId: string;
  name: string;        // "Simple Homme"
  category: string;    // "Senior"
  format: MatchFormat; // 1 set à 5 jeux, TB à 4
  players: Player[];   // 16 par défaut
  poules: Poule[];     // 4 par défaut
  bracket: Bracket;
};

// Joueur
type Player = {
  id: string;
  firstName: string;
  lastName: string;
  license: string;     // ex: "FFT-58210"
  seed?: string;       // ex: "A1", "B2" — tête de série
  pouleId?: string;
};

// Poule (groupe de qualifs)
type Poule = {
  id: string;          // "A", "B", "C", "D"
  playerIds: string[]; // ~4 joueurs
  matches: PouleMatch[];
};

// Match (générique)
type Match = {
  id: string;
  eventId: string;
  type: 'poule' | 'qf' | 'sf' | 'f';
  playerAId: string;
  playerBId: string;
  servingPlayerId: string;
  initialServerPlayerId: string;
  format: MatchFormat;
  sets: SetResult[];   // sets terminés
  currentSet: {
    gamesA: number;
    gamesB: number;
    pointsA: number;   // 0/1/2/3/4+ (logic dans state.jsx)
    pointsB: number;
    inTiebreak: boolean;
  };
  status: 'scheduled' | 'in_progress' | 'completed';
  winnerId?: string;
  startedAt?: Date;
  completedAt?: Date;
  court?: string;      // "Central"
  featured?: boolean;  // mis en avant sur le scoreboard TV
  history: MatchEvent[]; // pour undo
};

type MatchFormat = {
  setsToWin: number;     // 1
  gamesPerSet: number;   // 5
  tiebreakAt: number;    // 4 (4-4 → tiebreak)
  tiebreakPoints: number;// 7
};

type SetResult = {
  a: number;             // games joueur A
  b: number;             // games joueur B
  tiebreak?: [number, number]; // si décidé au TB
};

// Bracket final
type Bracket = {
  qf: Match[];           // 4 quarts
  sf: Match[];           // 2 demis
  final: Match;          // 1 finale
  winner?: Player;
};
```

### Logique de score tennis

La logique complète est dans `design/state.jsx` (helpers `awardPoint`, `checkGameWinner`, `pointLabel`). À porter côté serveur (source de vérité) :

- Points dans un jeu : 0 → 15 → 30 → 40 → jeu (si autre ≤ 30). Sinon **deuce** (40-40) → **avantage** (AV) → jeu si on regagne, retour à 40-40 si on perd.
- Jeu remporté : `+1 game`. Switch de serveur.
- Set remporté : atteindre `gamesPerSet` (5) avec 2 jeux d'écart. **Si 4-4 → tiebreak.**
- Tiebreak : premier à `tiebreakPoints` (7) avec 2 points d'écart. Service alterne tous les 2 points après le premier.
- Match terminé : `setsToWin` (1) atteint.

L'arbitre doit pouvoir :
- Ajouter un point à A ou B (`POST /matches/:id/points` avec `{ side: 'A' | 'B' }`)
- Annuler le dernier point (`POST /matches/:id/undo`) — historique max 50 entrées
- Changer manuellement le serveur (`PATCH /matches/:id/serving`)
- Terminer (`POST /matches/:id/complete`) ou réinitialiser (`POST /matches/:id/reset`) — **avec confirmation modale obligatoire**

---

## Design tokens

### Couleurs (dark theme par défaut)

```css
/* Surfaces — toutes en nuances bleutées presque pures pour cohérence broadcast */
--bg-0: #050608;          /* deepest, scoreboard backdrop */
--bg-1: #0A0C11;          /* page background */
--bg-2: #11141B;          /* card / panel */
--bg-3: #181C25;          /* raised */
--bg-4: #232834;          /* hover / active */

/* Lignes */
--line-1: rgba(255,255,255,0.06);
--line-2: rgba(255,255,255,0.10);
--line-3: rgba(255,255,255,0.18);

/* Encre (texte) */
--ink-0: #FFFFFF;
--ink-1: rgba(255,255,255,0.86);
--ink-2: rgba(255,255,255,0.62);
--ink-3: rgba(255,255,255,0.40);
--ink-4: rgba(255,255,255,0.22);

/* Accent — JAUNE/OR retenu pour ce projet */
--accent:      #FFC83D;
--accent-2:    #D6A621;
--accent-soft: rgba(255,200,61,0.18);   /* fonds, bordures */
--accent-glow: rgba(255,200,61,0.45);   /* halos, drop-shadows */

/* Sémantiques */
--danger:      #FF3052;
--danger-soft: rgba(255,48,82,0.14);
--gold:        #FFC83D;
--success:     #22E27F;

/* Balle de service (jaune fluo tennis) */
--ball-yellow: #E8F35A;
```

### Light theme (admin panel uniquement)

Le panel admin utilise `.light-scope` qui override les variables :

```css
--bg-1: #F6F7F9;
--bg-2: #FFFFFF;
--bg-3: #F0F2F5;
--bg-4: #E5E8ED;
--line-1: rgba(15,20,30,0.06);
--line-2: rgba(15,20,30,0.10);
--line-3: rgba(15,20,30,0.18);
--ink-0: #0B0F17;
--ink-1: rgba(11,15,23,0.92);
--ink-2: rgba(11,15,23,0.66);
--ink-3: rgba(11,15,23,0.46);
--ink-4: rgba(11,15,23,0.24);
```

### Typographie

- **Famille UI** : `Inter, system-ui, sans-serif` (police choisie par le client).
- **Tabular numerals** obligatoire sur tous les scores : `font-variant-numeric: tabular-nums` ou utility `.tab`.
- **Mono** (badges, métadonnées, codes licence) : `ui-monospace, "SF Mono", Menlo, Consolas, monospace`.

#### Échelles types par contexte

| Contexte | Taille | Weight | Tracking |
|---|---|---|---|
| Logo / titre TV | 22px | 800 | 0.20em |
| Sous-titre TV | 12px | 400 | 0.18em |
| Score points (scoreboard classic) | 64px | 800 | -0.02em |
| Score jeux (scoreboard classic) | 60px | 700 | normal |
| Nom joueur (scoreboard classic) | 36px | 800 | 0.02em |
| Score points (arbitre split) | 100px | 800 | -0.04em |
| Nom joueur (arbitre) | 28-36px | 700 | -0.01em |
| Label section (h3 admin) | 14px | 600 | -0.005em |
| Label all-caps (uppercase eyebrow) | 10-11px | 600-700 | 0.16-0.22em |
| Body admin | 13px | 400-500 | normal |

### Espacement

Aucune échelle stricte — multiples de 4 (4, 8, 12, 14, 16, 18, 20, 24, 28, 32, 44, 56, 64). Les paddings de card courants : 14-18px (mobile/dense), 20-28px (régulier), 32px (héro).

### Rayons

```css
--r-xs: 4px;    /* badges seed, tags */
--r-sm: 8px;    /* inputs, chips */
--r-md: 12px;   /* cards petites, boutons larges */
--r-lg: 18px;   /* cards principales */
--r-xl: 24px;   /* zones de tap géantes, modales */
```

### Ombres

```css
--shadow-1: 0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35);
--shadow-2: 0 1px 0 rgba(255,255,255,0.06) inset, 0 20px 60px rgba(0,0,0,0.5);
--glow: 0 0 0 1px var(--accent-soft), 0 0 24px var(--accent-glow);
```

---

## Écrans

L'application comporte **9 écrans** au total :

| # | Écran | Cible | Accès | Description |
|---|---|---|---|---|
| 1 | **Login** | PC 1440×900 (light) | Public | Sélection du rôle + mot de passe + lien public "En direct" |
| 2 | **Scoreboard TV — Live** | 1920×1080 (dark) | Public | Affichage du match en cours, panneau "à préparer" |
| 3 | **Scoreboard TV — Attente** | 1920×1080 (dark) | Public | Carrousel auto entre 4 slides + bandeau "Prochain match" persistant |
| 4 | **Poules TV** | 1920×1080 (dark) | Public | Classement des 4 poules avec rotation auto |
| 5 | **Tableau final TV** | 1920×1080 (dark) | Public | Bracket QF → SF → F → Vainqueur |
| 6 | **Arbitre · sélection** | iPad 834×1112 (dark) | Auth arbitre | Liste des matchs Live / À venir / Terminés |
| 7 | **Arbitre · saisie** | iPad 834×1112 (dark) | Auth arbitre | Score en direct, 2 zones de tap géantes, undo, swap, finish |
| 8 | **Admin** | PC 1440×900 (light) | Auth organisateur | 5 onglets : Joueurs, Poules, Matchs, Tableau final, Tournoi |
| 9 | **Admin · modales** | PC 1440×900 (light) | Auth organisateur | 6 modales + 1 slide-out d'édition de match |

### 1. Login (1440×900, light)

**Cible :** Page d'entrée. Affichée sur PC organisateur et iPad arbitre. Identique sauf scaling.

**Layout :**
- Card centrée 1080×660 en grille `1fr / 360px` : panneau formulaire + panneau décoratif sombre.
- **Panneau gauche** : logo tournoi + titre "Connexion" + 2 cartes de rôle côte à côte (**Organisateur** / **Arbitre**, chacune avec icône, label, sub-texte, radio de sélection). Le formulaire mot de passe en dessous est **désactivé tant qu'aucun rôle n'est sélectionné** (opacity 0.4, pointer-events none) et s'active dès que l'utilisateur clique sur une carte (email pré-rempli affiché en mono, CTA "Se connecter en tant que [rôle]").
- **Bouton "En direct"** (toujours actif, en bas de la card) : point rouge pulsant + label "En direct" + sub "accès libre · TV, poules, tableau final". Mène directement à `/tv/live` sans authentification.
- **Panneau droit** (dark sur fond light) : logo halo + citation décorative + 3 stats (joueurs, épreuves, matchs prévus) + footer "Serveur en ligne · raspberrypi.local · v1.4.2".

**Comportement :**
- Sélection du rôle → bouton CTA actif + autofocus sur le champ mot de passe.
- Soumission → POST `/auth/login` → redirect selon rôle : `admin → /admin/joueurs`, `arbitre → /arbitre`.
- "En direct" → redirect `/tv/live` (route publique).

### 2. Scoreboard TV — Live (1920×1080)

**Cible :** Écran 1920×1080 fullscreen, affiché en bord de court. Lisibilité à 5-10 m.

**Layout (variante "Classic" retenue) :**

- **Backdrop** : photo de court de tennis en perspective + overlay sombre dégradé. **Photo non fournie** → placeholder dégradé vert foncé avec lignes de court SVG en perspective.
- **Coin haut-gauche** : logo tournoi + "OPEN DE MOUTILLOUX" / "ÉDITION 2026".
- **Coin haut-droit (sous le titre)** : **panneau "À PRÉPARER"** (cf. ci-dessous).
- **Bandeau bas** (≈ 220px de haut, fond noir 96% opacité) :
  - Ligne titre : 🔴 EN DIRECT · catégorie · format
  - Grille 1fr / 2px / 1fr : pour chaque joueur, barre verticale d'accent, drapeau, balle de service (si serveur), nom + seed, sets gagnés, games courants, points courants (chiffre énorme).
  - Pied : COURT · DURÉE · ACES · % 1RE · AU SERVICE

**Panneau "À PRÉPARER" (PrepPanel) :**

Carte flottante en haut à droite (360×auto), fond `rgba(8,12,16,0.78)` blur, barre verticale d'accent à gauche :
- Header : label "À PRÉPARER · 15:00" en accent + stage "Demi-finale 2"
- 2 mini-avatars (initiales colorées) + 2 noms en grand + "vs" entre les deux
- Footer : court + appel "Présentez-vous au juge-arbitre" avec dot pulsant

**Variantes scoreboard non retenues :** `glass`, `editorial` (gardées dans le code de design pour référence, à ignorer).

### 3. Scoreboard TV — En attente / Carrousel auto

**Cible :** Affiché quand aucun match n'est en direct (le champ `featured` n'existe pas ou est `null`). Tournoi en pause, intersession, etc.

**Layout :**

- **Header fixe** (en haut) : logo + nom tournoi + horloge.
- **Zone centrale** (carrousel auto, rotation **6 secondes par slide**, crossfade) :
  1. **Hero "En attente"** : balle animée + label "EN ATTENTE DU PROCHAIN MATCH" + countdown "Reprise dans 12'" + carte de stats globales (terrains ouverts, matchs joués, prochaine phase).
  2. **Derniers résultats** : 5 dernières rencontres (heure, stage, joueurs avec seeds, score, court) avec animation stagger d'entrée.
  3. **Classement des poules** : aperçu de 2 poules avec colonnes V/D/Jeux/Pts + badges Q sur les qualifiés.
  4. **Tableau final** : mini-bracket QF → SF → F → Vainqueur avec animation flottante du trophée.
- **Footer fixe** :
  - **Bandeau "Prochain match" persistant** (à gauche, sur les 4 slides) : label + heure + stage + côté A (seed accent + nom) + "vs" + côté B (seed gris + nom) + court.
  - **Pager** (à droite) : 4 barres horizontales, la barre active s'étire en accent.

**Comportement :**

- L'état "en attente" est déclenché par l'absence de match featured (ou champ `tournamentState === 'idle'`).
- Rotation auto via `setInterval(6000)`. À mettre en pause si l'utilisateur survole (pas de souris en mode TV, mais utile en dev).
- Crossfade : opacity 0 ↔ 1 + translateY 16px ↔ 0, 700ms ease.

### 4. Poules TV (1920×1080)

**Cible :** 1920×1080. Rotation automatique entre les 4 groupes toutes les 4 secondes (indicateur visuel en haut à droite).

**Layout :**

- Header 96px : logo + "PHASE DE POULES / Simple Homme · 16 joueurs · 4 groupes" | indicateur de rotation (4 barres, celle active en accent).
- Grille 2×2 de cards.
- Chaque card poule :
  - En-tête : grand caractère ("A", "B", "C", "D") en accent + "Poule X".
  - Body : grille `1.6fr / 1fr` :
    - **Tableau standings** : Joueur | V | D | Jeux | Pts. Les 2 qualifiés ont fond accent-soft + badge "Q" + nom en blanc bold.
    - **Grille croisée 5×5** : matrice des résultats entre joueurs.
- Footer : légende Q + horodatage.

### 5. Tableau final TV (1920×1080)

**Cible :** 1920×1080. Bracket knockout (Quarts → Demi → Finale → Vainqueur).

**Variante retenue : "Lignes"** — connecteurs SVG.

**Architecture critique :** le positionnement des cards et des chemins SVG sont pilotés par **un objet de constantes unique** (cf. `bracket.jsx` → `const LB`). Tout est centré mathématiquement : SF1 au midpoint(QF1, QF2), F au midpoint(SF1, SF2), trophée aligné à F.

```js
const LB = {
  qfX: 80, sfX: 540, fX: 1000, trX: 1420,    // left edges
  cardW: 380, finalW: 380, trW: 420,
  cardH: 120, finalH: 128, trH: 186,
  qf: [70, 230, 580, 740],                    // top de chaque QF
  sf: [150, 660],                              // midpoints des QF
  f:  401, tr: 372,                            // midpoint des SF
};
```

Body 1920×928. SVG en `viewBox="0 0 1920 928"` `preserveAspectRatio="none"`.

**Connecteurs** : forme en "U couché" (elbow) via :

```js
function elbowPath(fromX, fromY, toX, toY) {
  if (fromY === toY) return `M ${fromX} ${fromY} H ${toX}`;
  const midX = fromX + (toX - fromX) / 2;
  return `M ${fromX} ${fromY} H ${midX} V ${toY} H ${toX}`;
}
```

**Style** : `stroke: rgba(255,255,255,0.22)`, `stroke-width: 2`, `vector-effect: non-scaling-stroke`. Le chemin "live" est en accent avec dasharray + animation `dashFlow`.

**Card vainqueur** : gradient + halo + trophée + "À DÉSIGNER" tant que la finale n'est pas jouée.

### 6. Arbitre · Sélection du match (iPad 834×1112)

**Cible :** Première page après login arbitre. Liste de tous les matchs assignés (LIVE + SCHEDULED + récents FINISHED).

**Layout :**

- Header : "Bonjour Pierre," + sous-texte "Vous êtes l'arbitre désigné · N match en cours" + bouton logout (icône en haut à droite).
- Onglets pill : Tous · En direct (avec dot rouge pulsant si > 0) · À venir · Terminés.
- Liste verticale de **cards de match** (tap-friendly, grandes) :
  - Stripe verticale colorée à gauche (accent si LIVE, gris si SCHEDULED, transparent si FINISHED).
  - Header : pill statut (EN DIRECT rouge / PRÉVU gris) + heure en grand + court en bout.
  - Players : "JOUEUR_A vs JOUEUR_B" en gros (26px bold).
  - Footer (border-top dashed) : épreuve + stage + score si LIVE + label CTA en accent ("Reprendre" / "Démarrer" / "Voir" selon statut) avec flèche.
- Footer : indicateur "Synchronisé · 15:42:08" avec dot vert.

**Comportement :**

- Tap sur une card → navigate `/arbitre/:matchId` → écran de saisie.
- Polling toutes les 5s pour refresh la liste.
- Le match en LIVE est toujours en haut, suivi des SCHEDULED par heure croissante, puis FINISHED.

### 7. Arbitre · Saisie du score (iPad 834×1112)

**Cible :** Interface tactile pour le référent du match.

**Layout (variante "Split" retenue) :**

- **Header** (96px) : bouton retour | catégorie + format | badge statut.
- **Bloc score** (280px) : grille 1fr / 320px / 1fr :
  - Gauche/Droite : "JOUEUR A/B" + nom + meta (SETS x | JEUX y | balle service)
  - Centre : "POINT" + chiffres énormes (100px), accent à gauche, blanc à droite, séparateur ·.
- **Zones de tap** : 2 boutons full-height ("+ POINT" géant + "TAP ICI"). Bouton A en accent, bouton B en blanc. Flash brightness sur tap.
- **Footer d'actions** : Annuler dernier point | Changer serveur | Terminer (rouge) | Réinitialiser (rouge ghost).

**Confirmations destructives :** Modale plein écran à fond flouté, icône triangle danger rouge, boutons "Annuler" / "Confirmer".

**Comportement :**

- Tap sur "+ POINT A" → POST → mise à jour optimiste + broadcast WebSocket.
- Undo : pop historique (max 50 entrées).
- Match terminé → désactive Points (opacity 0.4).

### 8. Admin Panel (PC, light) — 5 onglets

**Sidebar :**

- Logo accent 36px + "MOUTILLOUX / Open · Édition 2026"
- Bloc "Épreuve active" : dropdown "Simple Homme · Cat. A"
- Nav (5 items) : **Joueurs · Poules · Matchs · Tableau final · Tournoi**. Item actif fond accent.
- Bas : Voir résultats ↗ | Changer d'épreuve | **Déconnexion** (rouge).

**Header de page :** breadcrumb + H1 + sous-titre + actions droite (bouton "Sauvegardé" + CTA primary varie par page).

#### 8.a Joueurs

- Toolbar : recherche + chips ("Tous · 16" | "Têtes de série · 8" | "Sans poule · 0").
- Table : Checkbox | Joueur (avatar + nom + meta) | Licence FFT | Catégorie | Poule (pill accent) | Tête de série (pill mono) | Actions (Éditer, Retirer avec confirmation).
- CTA primary : "+ Ajouter un joueur" → ouvre **AddPlayerModal**.
- Action secondaire : "Créer une équipe" (mode Double) → ouvre **CreateTeamModal**.

#### 8.b Poules

- Grille `280px / 1fr / 1fr` × 2 rangées.
- Colonne 1 (full hauteur) : "Non assignés".
- 4 cards "Poule A/B/C/D" avec liste de pills draggables (avatar + nom + Q + ✕).
- CTA primary : "Remplir automatiquement" → ouvre **AutoFillModal**.

#### 8.c Matchs

- Kanban 3 colonnes : **Backlog** (gris) | **File d'attente** (accent) | **Terminés** (vert).
- Card match : type + noms + meta (Score, Court) + Éditer / ★ Mettre en avant + grip.
- CTA primary : "Générer les matchs de poule" → ouvre **GenerateMatchesModal**.
- Tap "Éditer" sur une card → ouvre **EditMatchPanel** (slide-out droit).

#### 8.d Tableau final

- Grille `1fr / 300px` : bracket admin compact à gauche + liste "Qualifiés disponibles" draggable à droite.
- Drag d'un qualifié vers un slot QF assigne le joueur.

#### 8.e Tournoi (NOUVEAU)

- **Card "Édition active"** : nom + dates + 4 stats (joueurs, épreuves, matchs joués, courts ouverts) + meta (lieu, directeur, juge-arbitre, sauvegarde locale).
- **Card "Épreuves de l'édition"** : grille 2 colonnes de cards d'événement. Chaque card a un code couleur, badge S/D, nom, catégorie, # joueurs, statut, barre de progression, et actions (Joueurs / Poules / Matchs / Activer).
- **Card "Historique des éditions"** : table des éditions passées avec dates, # épreuves, # joueurs, statut, lien "Voir".
- CTA secondary : "+ Nouvelle édition" / "+ Nouvelle épreuve".

### 9. Admin · Modales et slide-out

Toutes les modales sont rendues **à l'intérieur du scope `.adm.light-scope`** (fond flouté `rgba(11,15,23,0.45)` + blur 6px). Click sur le backdrop ferme. Échap aussi (à implémenter).

#### AddPlayerModal / EditPlayerModal

- Taille `lg` (820px). 3 sections :
  - **Identité** : prénom, nom, date de naissance, genre (Segmented Homme/Femme/Autre).
  - **Contact** : email, téléphone.
  - **Compétition** : licence FFT, classement (select), épreuves à inscrire (chips multi-select), tête de série (toggle + select TS1-4).
- Footer : Annuler · Enregistrer comme brouillon · Ajouter & inscrire (CTA primary).

#### CreateTeamModal (Double Mixte)

- Taille `md`. Composition (2 slots joueur avec picker — chaque slot affiche un avatar et un bouton "Choisir") + Identification (nom équipe optionnel + tête de série).

#### AutoFillModal

- Taille `md`. Format des poules (Segmented 3/4/5 joueurs), méthode (Segmented Snake/Aléatoire), options (séparer têtes de série, éviter même club), **prévisualisation des poules générées** (pills) + warning si matchs existants seront regénérés.

#### GenerateMatchesModal

- Taille `md`. Format de match (sets, jeux par set, points TB, court par défaut) + **tableau de répartition** (Poule × Joueurs × Matchs × Estimation durée) avec ligne total.

#### ConfirmModal

- Taille `sm`. Icône warning, titre, body, boutons Annuler · Confirmer (danger en rouge si destructif).

#### EditMatchPanel (slide-out droit, 560px)

- Slide-in de la droite (translateX 40 → 0 + opacity).
- Header : breadcrumb (épreuve · stage) + titre "PlayerA vs PlayerB" + tags (LIVE / court / heure / ★ MIS EN AVANT).
- 4 onglets : **Score · Format · Planning · Historique**.
  - **Score** : grille éditable (sets, set 1, jeu en cours, point) par joueur + toggle tiebreak + sélecteur de vainqueur.
  - **Format** : sets à gagner, jeux par set, tie-break à, points TB, service initial.
  - **Planning** : court, heure prévue, statut (Prévu/Live/Terminé/Annulé), ordre dans la file + toggle "Mettre en avant".
  - **Historique** : log mono des actions (timestamp, qui, quoi).
- Footer : Supprimer (rouge ghost) · Annuler · Enregistrer (CTA primary).

---

## Interactions globales & flux

### Temps réel

Tous les écrans **TV** doivent s'abonner au stream du match featured (le match "mis en avant" depuis l'admin Kanban ou par défaut le match en cours sur le court central). Quand l'arbitre marque un point :

1. UI arbitre : mise à jour optimiste immédiate.
2. POST `/matches/:id/points` { side }.
3. Server applique la logique (`awardPoint` portée côté serveur), met à jour le match, persiste.
4. Broadcast WebSocket à `match:${id}` channel.
5. Scoreboard TV (et autres listeners) reçoivent l'événement et mettent à jour leur state.
6. Animation : highlight transient côté gagnant, mise à jour fluide des numbers (transition CSS sur transform/opacity).

### Animations

| Élément | Effet | Détail |
|---|---|---|
| Balle de service | flotte verticalement | `translateY` ±3px, 1.8s ease-in-out infinite |
| Dot LIVE 🔴 | pulse | opacity 1 → 0.5, 1.5s ease-in-out infinite |
| Connecteur SVG live | flux pointillé | `stroke-dasharray: 6 4` + `dashFlow` 1.2s linear infinite |
| Bouton Point tap | scale | `transform: scale(0.985)` au :active |
| Zone tap arbitre | brightness flash | `filter: brightness(1.3)` 500ms ease-out après tap |
| Highlight scoreboard | gradient fade | `background: linear-gradient(90deg, accent-soft, transparent 60%)` transition 200ms |
| Card poule active (rotation) | accent ring | `box-shadow: 0 0 0 1px accent-soft, 0 0 40px rgba(accent, 0.08)` transition 400ms |

### Responsive

Les écrans **TV** sont fixés à 1920×1080 et **scalés** (CSS `transform: scale()`) pour fit la fenêtre tout en gardant les proportions. Pas de breakpoints.

L'**arbitre** est fixé à 834×1112 (portrait iPad).

L'**admin** est fixé à 1440×900 mais peut être rendu responsive plus tard (sidebar collapsible en dessous de 1100px par ex.).

---

## Assets

- **Icônes** : SVG inline minimaux (logo balle de tennis, trophée, undo, swap, eye, etc.). Pas de lib externe — facile à remplacer par lucide-react / heroicons.
- **Drapeaux** : placeholder CSS (3 bandes bleu/blanc/rouge pour le FR). À remplacer par une lib type `circle-flags` ou des SVG officiels.
- **Photo de court (scoreboard backdrop)** : **non fournie**. Placeholder dégradé + lignes de court SVG en perspective. À remplacer par une vraie photo HD ou un rendu 3D.
- **Avatars joueurs** : pastilles de couleur avec initiales. À remplacer par photos quand dispo.
- **Logo Moutilloux** : SVG inline générique (balle de tennis stylisée). À remplacer par le logo officiel du tournoi.

---

## Notes pour l'implémentation

1. **Source de vérité côté serveur** pour la logique de score. Ne JAMAIS faire confiance au client — l'arbitre peut envoyer un "point A", mais c'est le serveur qui calcule l'état résultant.
2. **Idempotence des actions** : chaque point ajouté doit avoir un ID unique (pour permettre l'undo et éviter les doublons en cas de retry réseau).
3. **Optimistic updates côté arbitre** : appliquer le point immédiatement, rollback si le serveur refuse.
4. **Auth** : l'arbitre doit s'authentifier (PIN court suffit) ; les TV sont publiques (URL stable par court/match).
5. **PWA / mode offline arbitre** : queue locale d'événements à syncer dès le retour réseau (essentiel pour les courts mal couverts).
6. **Tests prioritaires** : unit tests sur la logique de score (deuce, advantage, tiebreak, match point) — c'est le code business le plus critique.

---

## Fichiers livrés

| Fichier | Contenu |
|---|---|
| `design/Moutilloux.html` | Point d'entrée, navigation entre écrans, panneau de tweaks |
| `design/tokens.css` | Toutes les variables CSS (couleurs, typo, radii, ombres) |
| `design/app.css` | Styles du shell (top nav, stage scaler) |
| `design/state.jsx` | Hook `useMatch` + logique de score tennis + fixtures (joueurs, poules, bracket, éditions, événements, matchs arbitre, courts) |
| `design/nav.jsx` | Top nav (7 écrans) + scaler `StageFrame` pour les écrans à taille fixe |
| `design/scoreboard.jsx` + `.css` | 3 variantes scoreboard TV (Classic retenue) + **PrepPanel** ("À préparer") |
| `design/arbitre.jsx` + `.css` | 2 variantes arbitre iPad (Split retenue) + modale de confirmation |
| `design/poules.jsx` + `spectator.css` | Écran poules TV avec rotation auto |
| `design/bracket.jsx` + `spectator.css` | 2 variantes bracket (Lignes retenue) |
| `design/admin.jsx` + `.css` | Admin panel light : 5 onglets (Joueurs · Poules · Matchs · Tableau · **Tournoi**) |
| `design/modals.jsx` + `.css` | 5 modales admin + slide-out d'édition match (Score · Format · Planning · Historique) |
| `design/extras.jsx` + `.css` | **Login**, **Arbitre Home**, **Admin Tournoi**, **TV Idle Carousel** |
| `design/tweaks-panel.jsx` | Panneau de tweaks (à NE PAS porter — outil de design uniquement) |

**Tu peux ignorer** `tweaks-panel.jsx` et tout le code lié aux tweaks dans `Moutilloux.html` — c'est un outil de design pour explorer les variantes, pas une feature à shipper.

**Variantes non retenues** (présentes dans le code pour référence, à ignorer) :
- Scoreboard : `glass`, `editorial`
- Arbitre : `columns`
- Bracket : `floating`

---

## Stack du prototype de design (pour info)

- HTML statique + React 18 via UMD + Babel Standalone (transpile à la volée — **ne JAMAIS faire ça en prod**).
- CSS natif avec custom properties.
- Pas de bundler, pas de build step — uniquement pour itérer rapidement le design.

Tu remplaceras tout ça par une vraie stack (Vue 3 + Vite + Pinia déjà en place côté `app/`) dans le projet final.

---

## Changelog par rapport au premier handoff

- **Comptes simplifiés** : 2 comptes seed-és (organisateur + arbitre) au lieu de 3 rôles. Les vues TV/Poules/Tableau sont publiques (sans login).
- **Nouvel onglet admin "Tournoi"** : gestion des éditions et épreuves.
- **5 modales admin** + 1 slide-out d'édition de match (Score / Format / Planning / Historique).
- **Login** retravaillé : 2 cartes de rôle + bouton public "En direct".
- **TV en attente** devient un **carrousel auto** (Hero → Résultats → Poules → Tableau) avec bandeau "Prochain match" persistant en bas.
- **Scoreboard live** : ajout du **panneau "À préparer"** (joueurs suivants à appeler au juge-arbitre).
- **Arbitre home** : liste filtrable des matchs (Tous / En direct / À venir / Terminés).
