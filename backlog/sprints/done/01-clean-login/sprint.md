---
sprint: 01
nom: Clean Login
specs:
  - specs/screens/login.md
modules:
  - login
  - auth
tickets-tag: sprint-01
branche: sprint/01-clean-login
branche-parent: main
log: backlog/sprints/01-clean-login/log.md
---

# Sprint 01 — Clean Login

**Objectif :** Aligner le code de la page login et du système d'authentification
sur les specs déclarées. Page utilisable, sécurisée, et conforme aux comportements attendus.

## Définition de terminé

- Spec review sur `specs/screens/login.md` → verdict `✅ Conforme`
- Aucun ticket `[sprint-01]` restant dans `backlog/backlog.md`

## Specs ciblées

- [`specs/screens/login.md`](../../../specs/screens/login.md)
  → fichiers : `LoginView.vue`, `stores/auth.ts`, `router/index.ts`, `live/api_views.py`

## Tickets du sprint

Tous les tickets tagués `[sprint-01]` dans `backlog/backlog.md` :

| # | Titre | Sévérité |
|---|-------|----------|
| 019 | useApi : redirection 401 non gérée → pas de renvoi vers le login | 🟠 |
| 023 | Router : garde `isReferee` + prop `matchId: string` → `number` | 🟡 |
| 032 | LoginView : `:disabled` du bouton submit ne vérifie pas le mot de passe | 🟠 |
| 033 | LoginView : pas de distinction erreur identifiants / erreur réseau | 🟠 |
| 034 | LoginView + Router : "retour après login" non implémenté | 🟠 |
| 035 | Router : utilisateur déjà connecté non redirigé depuis /login | 🟠 |
| 036 | LoginView : message d'erreur identifiants tronqué | 🟡 |
| 037 | LoginView : aside affiche l'année au lieu du nom de l'édition | 🟡 |
