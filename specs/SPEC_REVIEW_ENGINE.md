# SPEC REVIEW ENGINE — Moutilloux

> **Comment déclencher :** ce fichier est lu automatiquement par le BACKLOG_ENGINE quand
> le backlog est vide. Il peut aussi être déclenché manuellement en collant le prompt de
> la section 5 dans un nouveau chat.

---

## 1. Contexte du projet

**Moutilloux** est une application Django de gestion de tournoi de tennis.
- Backend : Django (moteur de score, classements, bracket, rôle Arbitre)
- Frontend : SPA Vue 3 + Vite + TypeScript + Pinia + Vue Router
- Racine du projet : `/Users/maximelorin/Desktop/dev/moutilloux/`
- Specs : `specs/INDEX.md` → référence toutes les specs actives

**Règle d'or :** les specs décrivent ce qui **doit** être. Le code décrit ce qui **est**.
La review mesure l'écart.

---

## 2. Structure des fichiers

```
specs/
├── INDEX.md                    ← liste toutes les specs actives
├── SPEC_REVIEW_ENGINE.md       ← ce fichier
├── screens/                    ← specs par écran
├── transverse/                 ← specs globales (auth, polling, erreurs…)
├── technical/                  ← modèles de données, contrats API
└── logs/
    └── review_YYYY-MM-DD_N.md  ← log de chaque session de review
```

---

## 3. Protocole d'exécution

### Étape 0 — Lecture de l'index

Lire `specs/INDEX.md` et identifier toutes les specs au statut `✅ Actif`.

### Étape 1 — Review parallèle

Lancer **un agent reviewer par spec active**, en parallèle.

Chaque agent :
1. Lit la spec cible
2. Lit les fichiers listés dans le champ `fichiers:` de l'en-tête YAML
3. Compare spec ↔ code point par point
4. Rend un verdict global : `✅ Conforme` / `⚠️ Dérive mineure` / `❌ Dérive bloquante`
5. Liste chaque dérive avec :
   - Ce que dit la spec
   - Ce que fait le code actuellement
   - Sévérité : 🔴 critique / 🟠 majeure / 🟡 mineure

> Un agent de review de spec ne modifie aucun fichier. Il rapporte uniquement.

### Étape 2 — Génération des tickets

Pour chaque dérive `⚠️` ou `❌` :
- Créer un ticket dans `backlog/backlog.md` (même format que le backlog engine)
- Le ticket doit préciser :
  - La spec source (`specs/screens/login.md` par ex.)
  - Les fichiers à lire avant d'agir (repris du champ `fichiers:` de la spec)
  - La dérive exacte constatée

Si aucune dérive → passer directement à l'étape 3.

### Étape 3 — Décision de boucle

**Si des tickets ont été créés :**
- Activer `moutilloux-backlog-engine` via `update_scheduled_task` avec `enabled: true`
- Désactiver `moutilloux-spec-review` via `update_scheduled_task` avec `enabled: false`
- Le backlog engine prendra le relais à sa prochaine échéance (toutes les 6h à partir de 3h)

**Si aucun ticket (tout est conforme) :**
- Désactiver `moutilloux-spec-review` via `update_scheduled_task` avec `enabled: false`
- Vérifier que `moutilloux-backlog-engine` est bien désactivé
- Écrire dans le log : _"Toutes les specs sont conformes — cycle qualité terminé."_

### Étape 4 — Log de session

Créer `specs/logs/review_YYYY-MM-DD_N.md` (N = numéro de session du jour).

```markdown
# Review specs YYYY-MM-DD — N°X

**Specs reviewées :** N
**Dérives trouvées :** N
**Tickets créés :** N

## Résultats par spec

| Spec | Verdict | Dérives |
|------|---------|---------|
| screens/login | ✅ / ⚠️ / ❌ | description |

## Tickets créés
| # | Titre | Sévérité | Spec source |
|---|-------|----------|-------------|

## Décision de boucle
[Backlog engine activé / Cycle terminé]
```

---

## 4. Règles strictes

- Un agent reviewer ne modifie aucun fichier du projet — lecture seule
- Toute dérive, même mineure, doit être documentée (ticket ou note dans le log)
- Une spec manquante pour un écran existant = dérive à signaler dans le log (pas de ticket)
- Ne pas créer de tickets pour des anomalies hors-specs (les specs définissent le périmètre)

---

## 5. Démarrage rapide (prompt à coller en nouveau chat)

```
Lis le fichier `/Users/maximelorin/Desktop/dev/moutilloux/specs/SPEC_REVIEW_ENGINE.md`
et exécute le protocole de review complet (étapes 0 à 4).
```

---

## 6. État de la dernière session

> Mis à jour automatiquement par l'agent en fin de session.

**Dernière session :** 2026-06-12 — N°1
**Specs reviewées :** 1 (screens/login)
**Tickets générés :** 7 (031–037)
**Statut :** Tickets créés — backlog engine actif
