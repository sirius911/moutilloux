---
name: project-github-issues
description: Backlog migré vers GitHub Issues sirius911/moutilloux — structure labels/milestones/numéros
metadata:
  type: project
---

Le backlog Markdown a été migré vers GitHub Issues le 2026-06-17.

**Labels actifs :** majeure, mineure, sprint-02, sprint-03, sprint-04, à-reprendre, en-attente, dérive, infra

**Milestones :**
- #1 Sprint 02 — Admin Tournoi (closed)
- #2 Sprint 03 — Admin Shell (open, sprint courant)
- #3 Sprint 04 — Admin Panel Map (open)

**Issues :** #1–#2 pré-existantes ; #3–#27 ouvertes (tickets actifs) ; #28–#62 fermées (historique sprint-02)

**Fichiers backlog versionnés sur main :** SESSION_ENGINE.md, BACKLOG_ENGINE.md, sprints/, logs/
**Non versionné :** backlog/plan/ (gitignore)

**Why:** Centraliser le suivi dans GitHub pour que les routines cloud puissent lire l'état via l'API.
**How to apply:** Les tickets ouverts sont dans GitHub Issues. Pour créer un nouveau ticket, utiliser `gh issue create --repo sirius911/moutilloux`. Ne plus créer de fichiers NNN-*.md.
