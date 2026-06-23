---
type: overview
module: admin-panel
fichiers:
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/router/index.ts
  - frontend/design/admin.jsx
  - frontend/design/extras.jsx
  - live/api_views.py
  - live/admin_views.py
---

# Cartographie — Panel d'administration

> Carte de référence des écrans du panel admin : sommaire des specs d'écran
> (`specs/screens/`) et journal des décisions structurantes prises lors de leur
> rédaction. Le comportement attendu de chaque écran vit dans sa spec — ce
> document n'en est que l'index.

## Vue d'ensemble

L'espace admin (`/admin/*`, garde `requiresAuth` + `requiresAdmin`) est une SPA à
sidebar fixe ([AdminLayout.vue](../frontend/app/src/views/admin/AdminLayout.vue)) et
6 écrans. Principe directeur : **chaque chose se crée à l'endroit où on en a
besoin** (pas de référentiel à préparer en amont). Le chemin critique d'un
tournoi traverse 3 écrans :

```
Tournoi (édition + épreuves, catégorie inline) → Inscriptions → Poules
                                → puis Matchs → Tableau final
```

Joueurs (registre) est hors chemin critique : écran de maintenance des fiches,
le registre se peuple au fil des inscriptions.

Deux notions de contexte, à ne pas confondre (vocabulaire fixé par les specs) :
- **Édition active** : globale, persistée en base (`TournamentEdition.is_active`) —
  on l'**Active** depuis l'écran Tournoi.
- **Épreuve active** : sélection d'écran locale (sélecteur sidebar) — on la
  **Sélectionne** ; elle pilote Inscriptions / Poules / Matchs / Tableau final.

| # | Écran | Route | Réf design | Spec |
|---|-------|-------|------------|------|
| 0 | Shell admin (sidebar) | `/admin` (layout) | `admin.jsx → AdminSidebar` | ✅ [admin-shell.md](./screens/admin-shell.md) |
| 1 | Tournoi | `/admin/tournoi` (défaut) | `extras.jsx → AdminTournoi` | ✅ [admin-tournoi.md](./screens/admin-tournoi.md) |
| 2 | Joueurs (registre) | `/admin/players` | `admin.jsx → AdminJoueurs` (partiel) | ✅ [admin-joueurs.md](./screens/admin-joueurs.md) |
| 3 | Inscriptions | `/admin/inscriptions` | — (dérivé d'AdminJoueurs) | ✅ [admin-inscriptions.md](./screens/admin-inscriptions.md) |
| 4 | Poules | `/admin/groups` | `admin.jsx → AdminPoules` | ✅ [admin-poules.md](./screens/admin-poules.md) |
| 5 | Matchs | `/admin/matches` | `admin.jsx → AdminMatchs` | ✅ [admin-matchs.md](./screens/admin-matchs.md) |
| 6 | Tableau final | `/admin/bracket` | `admin.jsx → AdminTableau` | ✅ [admin-tableau-final.md](./screens/admin-tableau-final.md) |

Modales couvertes par les specs de leur écran hôte : Fiche joueur (Joueurs),
Équipe (Inscriptions), Remplissage auto (Poules), Génération + panneau d'édition
de match (Matchs), création de tableau (Tableau final), Édition + Épreuve avec
création de catégorie inline (Tournoi), et la modale de confirmation commune
(pattern `ConfirmModal` du design).

## User stories par écran (résumé)

- **Shell** — naviguer entre les 6 écrans, voir l'édition active, ouvrir la TV
  publique, se déconnecter.
- **Tournoi** — voir l'état de l'édition active (stats agrégées), gérer les
  éditions (créer / éditer / activer / supprimer si vide) et les épreuves
  (créer avec catégorie inline / éditer / supprimer avec garde-fous),
  sélectionner une épreuve.
- **Joueurs** — chercher dans le registre global, créer et corriger des fiches
  (identité, contact). Pas de suppression de fiche.
- **Inscriptions** — inscrire des joueurs à l'épreuve active (unitaire et en
  masse, mode Simple), créer des équipes (mode Double), retirer une inscription
  (bloquée si engagée dans un match).
- **Poules** — remplir automatiquement (3|4, ordre/aléatoire), ajuster par
  glisser-déposer, écran verrouillé dès que les matchs de poule existent.
- **Matchs** — générer le round-robin (action principale de CET écran),
  ordonnancer la file au glisser-déposer, éditer un match (score correctif,
  format verrouillé si LIVE, planning), mettre en avant (→ LIVE + antenne TV).
- **Tableau final** — créer le tableau (choix de l'étape de départ), assigner /
  vider les places depuis les qualifiés, poser les étiquettes de provenance,
  suivre la progression automatique des gagnants.

## Décisions structurantes (journal)

Écarts design ↔ produit tranchés lors de la rédaction des specs :

1. **Registre ≠ inscriptions.** Le mock fusionnait tout dans « Joueurs » ; l'app
   les sépare en deux écrans. La sidebar a 7 entrées au lieu de 5. Entériné.
2. **« Générer les matchs » vit sur l'écran Matchs** (action principale), comme
   dans le design — pas sur Poules (ticket backlog 040).
3. **Têtes de série et classement FFT : hors périmètre.** Le design les montre
   (AddPlayer, CreateTeam, AutoFill « snake ») mais les contrats de phase les
   excluent (« pas de seed », « pas de paramètre TS »). Seul subsiste
   l'affichage du `seed_hint` existant (étiquettes de provenance A1, D2…).
4. **Pas de création/suppression manuelle de match.** Les matchs naissent par
   génération round-robin ou création du tableau ; le « + Ajouter un match » et
   le « Supprimer » du mock EditMatchPanel ne sont pas retenus.
5. **Pas d'onglet « Historique » dans le panneau d'édition de match** : aucun
   journal d'activité n'est modélisé côté backend. À re-spécifier si un audit
   log voit le jour.
6. **Pas d'option « Abandon » comme vainqueur** : `winner_side` ∈ A/B/null. Un
   abandon se traite en désignant le vainqueur (+ statut Terminé).
7. **Métadonnées d'édition non modélisées (lieu, directeur, juge-arbitre,
   sauvegarde) : retirées** de l'écran Tournoi. Les stats de la carte Édition
   active sont des agrégats d'édition (ticket 039).
8. **Création manuelle de poule : non exposée à l'UI.** Le remplissage
   automatique crée les poules ; l'endpoint `groups/create` reste disponible
   côté API sans bouton dédié.
9. **Éditions et épreuves se gèrent dans Tournoi.** (Initialement : « Configuration
   n'a que Catégories et Courts » — caduc depuis la décision 11.)
10. **Kanban Matchs** : le match EN DIRECT s'affiche en tête de File d'attente ;
    les matchs ANNULÉS apparaissent dans Terminés avec badge (ticket 043).
11. **L'écran Configuration est supprimé** (sidebar à 6 entrées). Principe
    directeur entériné : chaque chose se crée à l'endroit où on en a besoin,
    pas dans un référentiel en amont. Sa spec est retirée ; les règles
    survivantes sont reprises par [admin-tournoi](./screens/admin-tournoi.md).
12. **Mono-court garanti** (terrain unique dans une propriété privée — hypothèse
    produit ferme). Plus de CRUD Courts : un court unique seedé en base
    (migration/fixture), attribution triviale à l'entrée en file. La logique
    « Central » (renommage, avertissements, suppression bloquée) disparaît.
    L'affichage du court sur les cartes de match est à réévaluer lors de la
    revue de l'écran Matchs (l'information ne discrimine plus rien).
13. **Catégories : création inline uniquement**, depuis la modale Épreuve
    (écran Tournoi). Renommage et suppression relégués à l'admin Django (filet
    de sécurité). Règle serveur conservée : mode figé dès qu'une inscription
    existe.
14. **Activation d'édition automatique si aucune active** : la première édition
    créée devient active ; les suivantes naissent en préparation et s'activent
    depuis l'historique. La case « Activer immédiatement » disparaît.
16. **Sélecteur d'épreuve relocalisé en en-tête de page** : la liste déroulante
    des épreuves quitte la sidebar et est portée par chacun des quatre écrans
    dépendants (Inscriptions, Poules, Matchs, Tableau final). La sidebar ne montre
    pas l'épreuve courante (option épurée). L'état reste global et partagé :
    changer l'épreuve sur un écran le met à jour pour tous les autres.
15. **Licence joueur : supprimée** (tournoi amateur — information sans usage dans
    ce contexte). Retirée de la fiche joueur et de la table du registre.

## API de référence (état : tout est exposé)

Toutes les mutations admin sont des endpoints JSON `/api/` câblés dans
`live/urls.py` (y compris bracket : `POST /api/events/<id>/bracket/assign|clear/`).
Lectures : `/api/editions/`, `/api/players/`, `/api/events/<id>/players|groups|
matches|bracket/`, `/api/categories/`, `/api/courts/`, `/api/matches/<id>/`.
Le détail requête/réponse vit dans `roadmap/phase-*.md` et dans le code
(`api_views.py`, source de vérité).

Conséquence des décisions 11-13 : les endpoints de CRUD courts et de
gestion de catégories (hors création) restent en place côté API mais ne sont
plus consommés par l'UI ; leur retrait éventuel se décidera lors de la revue
des écrans suivants.

## Transverses à extraire (specs/transverse/, prochaines specs)

- **Erreurs API** : affichage des erreurs JSON (`{error}`, `{fields}`), cas 401
  (backlog 019), conventions de bandeau/modale.
- **Polling** : quels écrans pollent et à quelle cadence (admin Matchs/Tableau,
  arbitre, TV) ; pause onglet caché (backlog 020).
- **Modales** : conventions communes (ModalShell, Échap — backlog 028,
  anti double-soumission, modale de confirmation).
