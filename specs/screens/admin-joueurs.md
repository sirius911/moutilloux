---
type: screen
module: admin/joueurs
fichiers:
  - frontend/app/src/views/admin/AdminPlayers.vue
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - core/models.py
---

# Spec fonctionnelle — Écran Joueurs (registre)

## Rôle de l'écran

L'écran Joueurs (`/admin/players`) est le **registre global** des personnes
physiques : l'annuaire de tous les joueurs connus du club, indépendant des
éditions et des épreuves. C'est ici qu'une fiche joueur est créée et corrigée.

Le registre ne gère **pas** les inscriptions : rattacher un joueur à une épreuve
se fait dans l'écran Inscriptions. Il n'y a pas de notion de classement ni de
tête de série sur une fiche joueur.

---

## Éléments d'interface

### En-tête de page

- Fil d'ariane « Tournoi », titre « Joueurs », sous-titre « N joueurs dans le
  registre ».
- Action principale : **« + Ajouter un joueur »** → modale Fiche joueur en
  création.

### Barre d'outils

- Champ de recherche, filtrage instantané (sans soumission) sur le **nom
  complet** et le **numéro de licence**, insensible à la casse.

### Table du registre

| Colonne | Contenu |
|---|---|
| Joueur | Avatar à initiales (couleur stable dérivée du nom) + nom complet |
| Licence | Numéro de licence (police monospace) ou « — » |
| Genre | Homme / Femme / Autre, ou « — » si non renseigné |
| Né(e) en | Année de naissance ou « — » |
| Actions | **Éditer** → modale Fiche joueur en édition |

- Tri par défaut : ordre alphabétique nom puis prénom.
- Ligne d'état vide quand la recherche ne trouve rien : « Aucun joueur trouvé ».
- État vide du registre (aucun joueur) : invite à ajouter le premier joueur.

Il n'y a **pas** d'action de suppression de fiche : une fiche joueur, une fois
créée, est conservée (elle peut être référencée par des inscriptions et des
matchs passés).

---

## Modale Fiche joueur (création / édition)

Titre « Ajouter un joueur » ou « Modifier le joueur » (sous-titre : nom complet
en édition, sinon « Le joueur sera ajouté au registre. »).

**Section Identité**

| Champ | Règle |
|---|---|
| Prénom | Requis |
| Nom | Requis |
| Genre | Homme / Femme / Autre (segmenté) ; optionnel |
| Année de naissance | Optionnelle (année seule, pas de date complète) |

**Section Contact**

| Champ | Règle |
|---|---|
| Email | Optionnel, format email vérifié par le serveur |
| Téléphone | Optionnel |

**Section Compétition**

| Champ | Règle |
|---|---|
| N° de licence | Optionnel, texte libre (police monospace) |

**Comportement**
- Le bouton d'enregistrement est désactivé tant que prénom ou nom sont vides,
  et pendant la soumission (anti double-clic).
- En **édition**, les champs non modifiés sont préservés : enregistrer sans
  toucher au téléphone ne l'efface pas.
- À la réussite : la modale se ferme et la table se rafraîchit ; en création, le
  nouveau joueur apparaît à sa place alphabétique.
- La création ajoute le joueur **au registre uniquement** — elle ne déclenche
  aucune inscription à une épreuve.

---

## Gestion des erreurs

- Erreur de validation serveur (ex. email invalide) : le message s'affiche dans
  la modale, par champ quand le serveur le détaille, et la saisie est conservée.
- Erreur réseau/serveur : message générique dans la modale, bouton réactivé pour
  réessayer.

## Données

- Le registre est chargé au montage de l'écran et rechargé après chaque
  création/édition réussie. Pas de polling.
- L'écran est indépendant de l'épreuve active : changer d'épreuve dans la
  sidebar ne modifie pas son contenu.
