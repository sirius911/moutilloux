# Specs — Index

> Source de vérité des comportements attendus de l'application Moutilloux.
> Chaque spec décrit **ce qui doit être**, pas ce qui est aujourd'hui.
> Maintenu manuellement ou via agent de maintenance (déclenché par le BACKLOG_ENGINE).

---

## Comment lire une spec

Chaque fichier de spec contient un en-tête YAML :

```yaml
---
type: screen | transverse | technical
module: nom-du-module
fichiers:
  - chemin/vers/fichier1
  - chemin/vers/fichier2
---
```

Le champ `fichiers` liste les fichiers source à lire avant toute action sur ce module
(planification, implémentation, review de spec).

---

## Cartographies (`specs/`)

Documents de synthèse qui recensent les écrans d'un espace et leurs user stories,
et servent de sommaire à la rédaction des specs d'écran.

| Module | Fichier | Statut |
|--------|---------|--------|
| admin-panel | [admin-panel-map.md](./admin-panel-map.md) | ✅ Actif |

---

## Specs d'écran (`specs/screens/`)

Décrivent le comportement attendu d'un écran spécifique : éléments d'interface,
flux utilisateur, redirections, gestion des erreurs.

| Module | Fichier | Statut |
|--------|---------|--------|
| login | [screens/login.md](./screens/login.md) | ✅ Actif |
| admin/shell | [screens/admin-shell.md](./screens/admin-shell.md) | ✅ Actif |
| admin/tournoi | [screens/admin-tournoi.md](./screens/admin-tournoi.md) | ✅ Actif |
| admin/joueurs | [screens/admin-joueurs.md](./screens/admin-joueurs.md) | ✅ Actif |
| admin/inscriptions | [screens/admin-inscriptions.md](./screens/admin-inscriptions.md) | ✅ Actif |
| admin/poules | [screens/admin-poules.md](./screens/admin-poules.md) | ✅ Actif |
| admin/matchs | [screens/admin-matchs.md](./screens/admin-matchs.md) | ✅ Actif |
| admin/tableau-final | [screens/admin-tableau-final.md](./screens/admin-tableau-final.md) | ✅ Actif |
| tv/programme | [screens/tv-programme.md](./screens/tv-programme.md) | ✅ Actif |

> L'écran Configuration a été supprimé (décisions 11-12 du journal de
> [admin-panel-map](./admin-panel-map.md)) : catégories créées inline dans la
> modale Épreuve, court unique seedé en base.

---

## Specs transverses (`specs/transverse/`)

Décrivent des règles globales qui s'appliquent à plusieurs écrans ou composants.

| Module | Fichier | Statut |
|--------|---------|--------|
| — | — | À créer |

*Exemples à prévoir : auth (guards, session, logout), polling (intervalles, pause onglet caché), gestion des erreurs API.*

---

## Specs techniques (`specs/technical/`)

Décrivent les modèles de données, contrats d'API, structures de stores.

| Module | Fichier | Statut |
|--------|---------|--------|
| planning | [technical/planning.md](./technical/planning.md) | ✅ Actif |
| routing | [technical/routing-context.md](./technical/routing-context.md) | ✅ Actif |

*Exemples à prévoir : match (structure `_pack_match`), event/edition, entry.*

---

## Ajouter une spec

1. Créer le fichier dans le bon sous-dossier (`screens/`, `transverse/`, `technical/`)
2. Inclure l'en-tête YAML avec `type`, `module`, `fichiers`
3. Ajouter une ligne dans la table correspondante dans ce fichier
4. Si la spec couvre un module déjà dans le backlog, mettre à jour les tickets concernés
