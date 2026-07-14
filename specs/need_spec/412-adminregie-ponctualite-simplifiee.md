---
issue: 412
titre: "AdminRegie : teinte de ponctualité — algorithme simplifié non reflété dans la spec"
---

# Besoin de spec — teinte de ponctualité en régie mobile

## Constat

`specs/screens/admin-regie-mobile.md:35-36` décrit la teinte de ponctualité de
la liste régie mobile comme suivant les « règles de [[planning]] » (renvoi
explicite vers `specs/technical/planning.md` § « Indicateur de ponctualité »).

Cette section normative de `planning.md` (lignes 176-190) définit un
algorithme à **3 couleurs** (rouge / orange / vert), une **tolérance unique de
5 min**, et une règle explicite pour les matchs `LIVE` (orange si démarré en
retard ou match qui s'éternise, vert si démarré à l'heure).

`frontend/app/src/views/admin/AdminRegie.vue::punctualityClass` (lignes
167-181) implémente une version **volontairement simplifiée** :
- 2 couleurs seulement (`punct-warn`/`punct-late`, pas de vert) ;
- tolérance à deux paliers (0 min → orange, 15 min → rouge) au lieu de la
  tolérance unique de 5 min ;
- aucune teinte pour un match `LIVE` (retour `null` immédiat).

Le code documente lui-même cette divergence comme assumée
(commentaire « version simplifiée assumée (plan #340 § 3) », renvoyant à
`backlog/plan/340-adminregie-ecran-complet.md:142-149`, où la décision a
initialement été prise) — mais le texte de `admin-regie-mobile.md` n'a jamais
été mis à jour en conséquence, et continue de promettre les règles complètes
de `planning.md`.

**Impact fonctionnel actuel : nul.** Le match `LIVE` est épinglé à part
(exclu de la liste où s'applique `punctualityClass`), donc l'absence de teinte
`LIVE` ne se voit jamais aujourd'hui. La divergence est purement documentaire
dans l'état actuel de l'écran — mais deviendrait un vrai bug si un match
`LIVE` réapparaissait un jour dans la liste défilante.

## Décision à prendre (arbitrage humain — hors mandat des agents automatisés)

Deux options, à trancher par un humain (les agents `reviewer`/spec-review
sont en lecture seule sur le **contenu** des specs — seul le champ YAML
`fichiers:` est modifiable automatiquement) :

**A. Documenter la simplification** — modifier `admin-regie-mobile.md:35-36`
pour décrire l'algorithme réellement implémenté (2 couleurs, tolérance à deux
paliers, pas de teinte pour `LIVE`) au lieu de renvoyer vers les règles
complètes de `[[planning]]`.

**B. Aligner le code sur la spec** — réécrire `punctualityClass` pour
suivre exactement l'algorithme de `planning.md` (tolérance 5 min, 3 couleurs,
règle `LIVE`), quitte à ce que ce cas ne se manifeste jamais dans l'état actuel
de l'écran (match `LIVE` toujours épinglé à part).

## Origine

Relevé pour la première fois en session #183 (protocole SESSION_ENGINE,
spec review), reconduit sans action aux sessions #184 et #185 (« note non
ticketée », hors mandat automatique), puis à nouveau en session #186 — cette
fois ticketé car il s'agit du seul verdict ⚠️ restant bloquant la clôture du
sprint 45 (condition « spec review ✅ Conforme sur toutes les specs »).
