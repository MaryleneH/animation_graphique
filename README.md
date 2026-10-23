# animation-graphique

Deux petits kits pour transformer un graphique animé en vidéo MP4 (1920 × 1080, 30 i/s).
La scène (un fichier HTML ou Python) est écrite par un LLM de chat, AI Chat du SSP Cloud
(Onyxia, Insee), qui n'exécute rien ; un script Python lancé en local fait le rendu.

## Le principe commun : chaque image est une fonction du temps

Rien ne « joue » en temps réel. Pour chaque image `i`, le script calcule l'instant
`t = i / fps`, demande à la scène de se dessiner à cet instant précis, photographie le
résultat et l'envoie à FFmpeg. Aucun état n'est conservé d'une image à l'autre : le rendu
est **déterministe**, donc reproductible, et une image donnée se vérifie isolément.

## Quelle version choisir ?

| | `html/` (HTML + GSAP) | `matplotlib/` |
|---|---|---|
| Rendu | Le plus beau : polices web, flous, typographie fine | Correct, sobre, « graphique de data scientist » |
| Ce qu'il faut | Un navigateur pilotable (Chromium via Playwright) | Zéro dépendance exotique : matplotlib + FFmpeg |
| Ce qu'on anime | Une page HTML animée par une timeline GSAP | N'importe quel graphique matplotlib, de la même façon |
| Scène écrite par le LLM | `page.html` | `scene.py` avec `draw(fig, t)` |

## Démarrage rapide

Version HTML :

```bash
pip install -r html/requirements.txt
playwright install chromium
python html/rendu.py html/exemple_graphique.html sortie.mp4
```

Version matplotlib :

```bash
pip install -r matplotlib/requirements.txt
python matplotlib/rendu_mpl.py matplotlib/exemple_barres.py sortie.mp4
python matplotlib/rendu_mpl.py matplotlib/exemple_barres.py brouillon.mp4 --fps 5   # brouillon rapide
```

FFmpeg doit être dans le PATH, ou `pip install imageio-ffmpeg`. Détails dans
[`html/README.md`](html/README.md) et [`matplotlib/README.md`](matplotlib/README.md).

## Faire écrire la scène par AI Chat du SSP Cloud

Chaque version a son prompt-contrat : à coller en début de conversation, puis décrire le
graphique voulu, rendre en brouillon, décrire ce qui cloche, recommencer.

- [`docs/prompt-ai-chat-html.md`](docs/prompt-ai-chat-html.md) — version HTML + GSAP
- [`docs/prompt-ai-chat-matplotlib.md`](docs/prompt-ai-chat-matplotlib.md) — version matplotlib

## Crédits et licence

Inspiré d'[HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen), le framework
open source de rendu vidéo à partir de HTML.

Code sous licence MIT (voir [`LICENSE`](LICENSE)), à l'exception de `html/gsap.min.js`,
distribué sous la licence de GSAP.
