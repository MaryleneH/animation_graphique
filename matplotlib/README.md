# Version matplotlib — des graphiques animés en MP4, sans navigateur

Le plan D : même principe que HyperFrames (« chaque image est une fonction du temps »),
mais avec les outils d'un poste de data scientist — Python, matplotlib, FFmpeg — et aucun
navigateur à piloter, donc aucune autorisation d'automatisation à demander.
AI Chat du SSP Cloud (ou n'importe quel LLM de chat) écrit la scène ; le script fait le reste, en local.

```
matplotlib/
├── rendu_mpl.py         le script de rendu (≈ 120 lignes) : vide la figure, draw(fig, t), pixels → FFmpeg
├── anim.py              la mini-bibliothèque (≈ 140 lignes) : easings, tween, alpha, compteur, mix, mots
├── exemple_barres.py    la scène d'exemple : le graphique en barres animé (données fictives)
└── requirements.txt

docs/prompt-ai-chat-matplotlib.md   le contrat à coller dans AI Chat du SSP Cloud + la boucle de correction
```

## Installation

Les commandes de ce fichier se lancent depuis le dossier `matplotlib/`.

```bash
pip install -r requirements.txt   # matplotlib ; numpy et pillow viennent avec, probablement déjà là
python rendu_mpl.py exemple_barres.py sortie.mp4
```

FFmpeg : dans le PATH, ou `pip install imageio-ffmpeg` (la wheel embarque un binaire),
ou `--gif` pour s'en passer (fichier lourd, qualité moindre — pour dépanner).

Hors ligne, il n'y a rien à télécharger d'autre que les wheels (`matplotlib`, `numpy`, `pillow`,
`contourpy`, `cycler`, `fonttools`, `kiwisolver`, `packaging`, `pyparsing`, `python-dateutil`),
que tout poste avec Python scientifique a déjà.

## Utilisation

```bash
python rendu_mpl.py scene.py sortie.mp4               # 1920x1080, 30 i/s, durée = DUREE de la scène
python rendu_mpl.py scene.py brouillon.mp4 --fps 5    # brouillon rapide (≈ 5 s de calcul)
python rendu_mpl.py scene.py sortie.gif --gif          # sans FFmpeg
```

La scène (`scene.py`) peut être n'importe où : `rendu_mpl.py` ajoute le dossier de la scène
au chemin d'import, en plus du sien ; `from anim import *` trouve donc `anim.py` à côté de la
scène s'il y en a un, sinon celui de `matplotlib/`.

## Le contrat d'une scène

```python
from anim import *

DUREE = 11.0
TAILLE = (1920, 1080)

def draw(fig, t):          # l'image de l'instant t, calculée à partir de t seulement
    fig.patch.set_facecolor("#0b1320")
    h = 34 * tween(t, 5.7, 0.9, ease=expo_out)          # une barre qui pousse de 0 à 34 entre 5,7 et 6,6 s
    n = compteur(t, 5.7, 1.4, 34)                        # son compteur
    ...
```

`rendu_mpl.py` vide la figure avant chaque image : il n'y a aucun état entre deux images,
c'est ce qui rend le rendu reproductible et vérifiable (une image donnée se regarde avec
`--fps 1`, ou en appelant `draw(fig, 6.5)` dans un notebook).

Le contrat complet, à coller dans AI Chat du SSP Cloud, est dans
[`../docs/prompt-ai-chat-matplotlib.md`](../docs/prompt-ai-chat-matplotlib.md).

## Ce qu'on perd, ce qu'on garde

Perdu par rapport au HTML : les flous, les polices web, la finesse typographique, les
transitions « cinéma », les ~450 blocs prêts à l'emploi d'HyperFrames.
Gardé : le cœur — rendu déterministe image par image, mise en scène des données (ordre de
lecture, une série en couleur, une annotation), compteurs, et un modèle de chat qui écrit la scène.
Bonus : on est chez matplotlib, donc n'importe quel graphique que tu sais déjà faire (courbes,
nuages, cartes avec geopandas) s'anime de la même façon.

## Pièges connus

- Les tailles de police sont en points, pas en pixels : utilise `px(28)` (28 px → 20,2 pt à 100 dpi).
- `y` se compte depuis le bas en fraction de figure ; la scène d'exemple a un helper `fy(y_px)` pour penser « depuis le haut ».
- Ne change pas la taille de la figure dans `draw` (le script contrôle : la vidéo a une taille fixe).
- Une police absente est remplacée par la suivante de la liste `rcParams["font.family"]` : garde `DejaVu Sans` en dernier.
- Rendu lent ? ≈ 0,1 s par image en 1080p : 330 images ≈ 30 s, c'est normal ; `--fps 5` pour itérer.
