# Need Spec — Besoins de specs en attente

Ce dossier contient les besoins de specs identifiés lors du développement,
qui n'ont pas encore été rédigés.

Chaque fichier ici correspond à un ticket `⏸️ En attente` dans `backlog/backlog.md`.
Le ticket restera bloqué tant que la spec n'est pas rédigée.

---

## Process pour débloquer un ticket en attente

1. Lire le fichier `need_spec/NNN-titre.md` pour comprendre le besoin
2. Rédiger la spec correspondante dans `specs/screens/`, `specs/transverse/` ou `specs/technical/`
3. Ajouter la spec à `specs/INDEX.md`
4. Dans `backlog/backlog.md`, retirer le statut `⏸️ En attente` du ticket concerné et lui attribuer la bonne sévérité (🔴 / 🟠 / 🟡)
5. Supprimer le fichier `need_spec/NNN-titre.md`

Le ticket sera alors éligible à la prochaine session du backlog engine.

---

## Format d'un fichier need_spec

```markdown
# Need Spec — NNN : Titre

**Découvert lors du ticket :** [numéro du ticket source]
**Date :** YYYY-MM-DD

## Besoin

[Décrire ce qui manque comme spec : quel écran, quel comportement,
quelle règle n'est pas spécifiée et bloque ou risque de bloquer le développement]

## Pourquoi c'est bloquant

[Expliquer pourquoi on ne peut pas implémenter correctement sans cette spec]
```
