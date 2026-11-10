# Version HTML + GSAP — des graphiques animés en MP4, sans framework

La version minimale du principe d'HyperFrames : une page HTML dont l'état est une fonction du
temps, un navigateur headless qui la photographie image par image, FFmpeg qui encode.
AI Chat du SSP Cloud (ou n'importe quel LLM de chat) écrit la page ; le script fait le reste,
en local, sans aucune requête réseau.

```
html/
├── rendu.py                 le script de rendu (≈ 120 lignes, Playwright + FFmpeg)
├── exemple_graphique.html   un graphique en barres animé, autonome (données fictives)
├── gsap.min.js              GSAP 3.15, copié en local (aucun CDN) — voir « Licence » plus bas
└── requirements.txt

docs/prompt-ai-chat-html.md  le contrat à coller dans AI Chat du SSP Cloud + la boucle de correction
```

## Installation

Les commandes de ce fichier se lancent depuis le dossier `html/`.

### Poste connecté à Internet

```bash
pip install -r requirements.txt     # playwright (+ imageio-ffmpeg si pas de ffmpeg)
playwright install chromium         # télécharge le Chromium de Playwright (~150 Mo)
python rendu.py exemple_graphique.html sortie.mp4
```

### Poste hors ligne (Intradef)

Ce qu'il faut faire passer : les wheels `playwright`, `greenlet`, `pyee` (et `imageio-ffmpeg`
si FFmpeg n'est pas installé — sa wheel embarque un binaire) — ou un miroir PyPI interne s'il existe.
Aucun téléchargement de navigateur n'est nécessaire si un Chrome ou un Edge est déjà sur le poste :

```bash
python rendu.py page.html sortie.mp4 --channel msedge
python rendu.py page.html sortie.mp4 --executable-path "C:/Program Files/Google/Chrome/Application/chrome.exe"
```

Tout reste sur le poste : la page est ouverte en `file://`, GSAP est local, rien n'est envoyé nulle part.

## Utilisation

```bash
python rendu.py page.html sortie.mp4                 # 1920x1080, 30 i/s, durée = window.__duration
python rendu.py page.html brouillon.mp4 --fps 5      # brouillon rapide pour vérifier le déroulé
python rendu.py page.html sortie.mp4 --width 1080 --height 1920   # vertical (la page doit être conçue pour)
```

La page charge `<script src="gsap.min.js">` en chemin relatif : place-la dans `html/`, à côté
de `gsap.min.js` (ou copie `gsap.min.js` à côté d'elle).

Le contrat de la page tient en deux lignes (voir
[`../docs/prompt-ai-chat-html.md`](../docs/prompt-ai-chat-html.md) pour les règles d'écriture) :

```js
window.__duration = 11;               // secondes
window.renderAt = (t) => tl.seek(t, false);  // met la page dans l'état de l'instant t (false : exécute les onUpdate)
```

GSAP est pratique mais pas obligatoire : `renderAt(t)` peut être n'importe quelle fonction qui
positionne les éléments à partir de `t` (styles, attributs, `<canvas>`).

## Ce qu'on perd par rapport à HyperFrames, ce qu'on garde

Perdu : le linter et les contrôles automatiques (mise en page, contraste, lisibilité, image 0 vide…),
le studio d'édition, les ~450 blocs prêts à l'emploi, le son.
Gardé : le cœur du mécanisme — rendu déterministe, image par image, donc reproductible et vérifiable —
et la possibilité de faire écrire la page par un modèle de chat qui ne sait rien exécuter.

## Pièges connus

- `page.evaluate` sérialise ce que la fonction renvoie. `tl.seek(t)` renvoie la timeline GSAP entière
  (un graphe circulaire avec tous les éléments du DOM) : le script appelle donc `renderAt` dans un bloc
  `{ … }` sans `return`. Si tu modifies le script, garde ça — sinon le rendu « gèle » à la première image.
- Une police absente du poste est remplacée : prévoir un `font-family` avec repli (`"Segoe UI", Arial, sans-serif`).
- Une tween `fromTo` sans `immediateRender: true` peut laisser l'élément visible avant son heure.
- `--fps 5` rend 6 fois plus vite : toujours vérifier le déroulé en brouillon avant le rendu final.
- Rendu lent ? C'est la capture PNG (≈ 0,1 s/image en 1080p) : 330 images ≈ 30–60 s, c'est normal.

## Licence

`gsap.min.js` est GSAP 3.15, copié tel quel depuis le paquet npm `gsap`. Il est distribué
sous la licence de GSAP ([gsap.com/standard-license](https://gsap.com/standard-license)),
**pas** sous MIT. Le reste du dépôt est sous licence MIT (voir [`../LICENSE`](../LICENSE)).
