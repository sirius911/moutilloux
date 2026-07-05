# Générateur d’affiches IA pour les matchs

Ce script permet de générer automatiquement une ou plusieurs affiches de match de tennis à partir des photos des joueurs.

Il utilise l’API OpenAI Images pour créer une affiche stylisée, dans un esprit jeu de combat / affiche de catch / arcade, avec les joueurs représentés à partir de leurs photos.

Le script peut gérer :

* un match simple : 2 joueurs ;
* un double : 4 joueurs ;
* les prénoms des joueurs ;
* le sexe de chaque joueur ;
* une attitude ou un adjectif pour chaque joueur ;
* plusieurs images générées pour le même match ;
* un dossier de sortie ;
* un chemin public retourné pour l’affichage dans le site.

---

## Emplacement du script

Le script est placé dans le dossier `scripts/` du projet Django.

---

## Installation des dépendances

Depuis l’environnement virtuel du projet, `openai` et `pillow` sont déjà
installés via le `requirements.txt` racine. Le script ajoute deux
dépendances CLI-only (`requests`, `python-dotenv`), isolées dans
`scripts/requirements.txt` :

```bash
pip install -r requirements.txt
pip install -r scripts/requirements.txt
```

---

## Clé API OpenAI

Le script utilise une clé API OpenAI.

Elle doit être placée dans un fichier `.env` à la racine du projet, au même niveau que `manage.py`.

Exemple :

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

Le fichier `.env` ne doit jamais être envoyé sur GitHub.

Vérifier que le fichier `.gitignore` contient bien :

```gitignore
.env
```

---

## Dossier de sortie

Les affiches générées peuvent être enregistrées dans :

```text
media/generated_match_posters/
```

Créer le dossier si nécessaire :

```bash
mkdir -p media/generated_match_posters
```

Si on ne veut pas versionner les images générées, ajouter dans `.gitignore` :

```gitignore
media/generated_match_posters/
```

---

## Utilisation pour un match simple

Exemple avec deux joueurs :

```bash
python scripts/generate_match_poster.py \
  --images media/players/TT.jpg media/players/clorin.jpg \
  --names Thérèse Cyrille \
  --sexes femme homme \
  --adjectives 'charmeuse et joueuse' 'agressif' \
  --n 2 \
  --out media/generated_match_posters \
  --public-prefix /media/generated_match_posters \
  --size 1536x1024
```

Dans cet exemple :

* `TT.jpg` correspond à Thérèse ;
* `clorin.jpg` correspond à Cyrille ;
* 2 affiches seront générées ;
* les images seront enregistrées dans `media/generated_match_posters/` ;
* le script retournera des chemins utilisables dans le site, comme `/media/generated_match_posters/...`.

---

## Utilisation pour un double

Pour un match en double, il faut fournir 4 images.

Les deux premières images correspondent à l’équipe 1.
Les deux suivantes correspondent à l’équipe adverse.

```bash
python scripts/generate_match_poster.py \
  --images \
    media/players/joueur1.jpg \
    media/players/joueur2.jpg \
    media/players/joueur3.jpg \
    media/players/joueur4.jpg \
  --names Marc Maxime Fabrice Michou \
  --sexes homme homme homme femme \
  --adjectives 'déterminé' 'rapide' 'furieux' 'malicieuse' \
  --n 2 \
  --out media/generated_match_posters \
  --public-prefix /media/generated_match_posters \
  --size 1536x1024
```

Correspondance :

```text
Image 1 = joueur 1 de l’équipe 1
Image 2 = joueur 2 de l’équipe 1
Image 3 = joueur 1 de l’équipe adverse
Image 4 = joueur 2 de l’équipe adverse
```

---

## Paramètres disponibles

| Paramètre         | Obligatoire | Description                                                                         |
| ----------------- | ----------: | ----------------------------------------------------------------------------------- |
| `--images`        |         Oui | Liste de 2 ou 4 images des joueurs.                                                 |
| `--names`         |         Oui | Prénoms des joueurs, dans le même ordre que les images.                             |
| `--sexes`         |         Oui | Sexe de chaque joueur : `homme`, `femme`, etc.                                      |
| `--adjectives`    |         Oui | Attitude ou adjectif pour chaque joueur.                                            |
| `--n`             |         Non | Nombre d’images à générer. Par défaut : `1`.                                        |
| `--out`           |         Oui | Dossier dans lequel enregistrer les affiches générées.                              |
| `--public-prefix` |         Non | Préfixe public retourné pour le site, par exemple `/media/generated_match_posters`. |
| `--base-dir`      |         Non | Répertoire de base pour les chemins relatifs.                                       |
| `--model`         |         Non | Modèle OpenAI Images utilisé.                                                       |
| `--size`          |         Non | Taille de l’image générée. Recommandé : `1536x1024`.                                |
| `--quality`       |         Non | Qualité : `low`, `medium`, `high` ou `auto`.                                        |

---

## Format conseillé pour le live

Pour l’affichage dans le live, le format conseillé est :

```text
1536x1024
```

C’est une image horizontale, plus adaptée à l’affichage avec un score en direct.

Le prompt du script demande à l’IA de garder une zone sombre et dégagée dans le bas de l’image pour pouvoir afficher le score par-dessus sans cacher les joueurs.

Le score ne doit pas être généré par l’IA.
Il doit être ajouté par le site en HTML/CSS.

---

## Exemple de retour du script

Après génération, le script retourne un JSON :

```json
{
  "images": [
    "/media/generated_match_posters/match_poster_20260610_121711_1_1_574cb051.png",
    "/media/generated_match_posters/match_poster_20260610_121711_1_2_e30c7307.png"
  ]
}
```

Ces références peuvent ensuite être utilisées dans le site pour afficher l’image.

---

## Exemple d’utilisation dans Django

Le script peut d’abord être utilisé en ligne de commande.

Plus tard, il pourra être intégré directement dans Django, par exemple dans :

```text
live/posters.py
```

Pour l’instant, l’usage recommandé est de le tester depuis le terminal.

---

## Adjectifs recommandés

Les adjectifs sont utilisés pour guider l’attitude visuelle des joueurs.

Exemples :

```text
agressif
furieux
déterminé
redoutable
concentré
menaçant
charmeuse
malicieuse
glamour
confiante
sûre d’elle
flamboyante
joueuse
magnétique
```

Pour les adjectifs composés de plusieurs mots, il faut utiliser des guillemets ou des apostrophes dans la commande :

```bash
--adjectives 'glamour et sûre d’elle' 'en colère'
```

---

## Adjectifs à éviter

Certains mots peuvent être bloqués par le système de sécurité de l’API Images, surtout lorsqu’il s’agit de personnes réelles.

À éviter :

```text
sexy
très sexy
sensuelle
provocante
désirable
attirante
```

À la place, préférer :

```text
glamour
charmeuse
sûre d’elle
magnétique
joueuse
rayonnante
élégante
```

Exemple :

```bash
--adjectives 'glamour et sûre d’elle' 'furieux'
```

---

## Utilisation d’images locales

Les images peuvent être passées avec un chemin local :

```bash
--images media/players/TT.jpg media/players/clorin.jpg
```

Le script accepte les formats courants :

```text
.jpg
.jpeg
.png
.webp
```

---

## Utilisation d’images distantes

Le script peut aussi recevoir des URLs d’images si elles sont accessibles publiquement :

```bash
--images https://monsite.fr/media/players/TT.jpg https://monsite.fr/media/players/clorin.jpg
```

Dans ce cas, le script télécharge temporairement les images avant de les envoyer à l’API.

---

## Messages d’avancement

Le script affiche des messages pendant son exécution :

```text
Envoi de la demande à OpenAI pour 2 image(s)...
Réponse reçue. Enregistrement des images...
Image enregistrée : media/generated_match_posters/...
```

La génération peut prendre un certain temps.
Tant que le script n’a pas reçu la réponse complète de l’API, il est normal que le dossier de sortie reste vide.

---

## Erreurs fréquentes

### Clé API absente

Erreur possible :

```text
Erreur : la variable d'environnement OPENAI_API_KEY n'est pas définie.
```

Solution : vérifier que le fichier `.env` existe et contient :

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

### Image introuvable

Erreur possible :

```text
Image introuvable : media/players/...
```

Solution : vérifier le chemin et le nom du fichier.

---

### Trop d’images demandées

Le script peut générer plusieurs images.
Si un nombre important est demandé, il fera plusieurs appels API automatiquement.

Pour les tests, commencer avec :

```bash
--n 1
```

ou :

```bash
--n 2
```

---

## Exemple complet recommandé

```bash
python scripts/generate_match_poster.py \
  --images media/players/TT.jpg media/players/clorin.jpg \
  --names Thérèse Cyrille \
  --sexes femme homme \
  --adjectives 'charmeuse et joueuse' 'agressif' \
  --n 2 \
  --out media/generated_match_posters \
  --public-prefix /media/generated_match_posters \
  --size 1536x1024
```

---

## Notes importantes

* Ne jamais mettre la clé API OpenAI dans le code.
* Ne jamais envoyer le fichier `.env` sur GitHub.
* Le score doit être ajouté par le site, pas généré dans l’image.
* Les adjectifs doivent guider l’attitude des joueurs, mais ne doivent pas apparaître comme du texte sur l’affiche.
* Le rendu exact peut varier d’une génération à l’autre.
* Il est conseillé de générer plusieurs propositions et de choisir la meilleure.
