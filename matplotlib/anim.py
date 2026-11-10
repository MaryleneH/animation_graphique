"""
anim.py — le strict nécessaire pour animer avec matplotlib de façon déterministe.

Principe : la scène fournit draw(fig, t). Aucune « lecture » : pour chaque image,
rendu_mpl.py vide la figure, appelle draw(fig, t) et photographie le résultat.
Tout ce qui bouge est donc calculé à partir de t par les fonctions ci-dessous.

    from anim import *

    y = tween(t, debut=1.0, duree=0.5, a=0, b=100, ease=expo_out)   # 0 avant 1 s, 100 après 1,5 s
    c = mix("#4f8df7", "#ff8a3d", tween(t, 7.5, 0.4))                # couleur interpolée
    n = compteur(t, 5.7, 1.4, 34)                                     # entier qui monte de 0 à 34
    a = alpha(t, debut=4.0, duree=0.2)                                # opacité 0 → 1
"""

from __future__ import annotations

import math

import matplotlib.colors as mcolors

# ---------------------------------------------------------------------------
# Easings : p ∈ [0, 1] → [0, 1]. Mêmes noms que GSAP, mêmes courbes.
# ---------------------------------------------------------------------------


def linear(p: float) -> float:
    return p


def power2_out(p: float) -> float:
    return 1 - (1 - p) ** 2


def power3_out(p: float) -> float:
    return 1 - (1 - p) ** 3


def power4_out(p: float) -> float:
    return 1 - (1 - p) ** 4


def expo_out(p: float) -> float:
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def power2_in(p: float) -> float:
    return p * p


def power3_in(p: float) -> float:
    return p ** 3


def power2_inout(p: float) -> float:
    return 2 * p * p if p < 0.5 else 1 - (-2 * p + 2) ** 2 / 2


def back_out(p: float, s: float = 1.4) -> float:
    """Dépasse légèrement puis revient (ressort amorti) : pour une position ou une taille, jamais une opacité."""
    p -= 1
    return 1 + p * p * ((s + 1) * p + s)


# ---------------------------------------------------------------------------
# Tweens : la valeur d'une propriété à l'instant t.
# ---------------------------------------------------------------------------


def progress(t: float, debut: float, duree: float) -> float:
    """Avancement brut de 0 à 1 entre debut et debut + duree (borné)."""
    if duree <= 0:
        return 1.0 if t >= debut else 0.0
    return min(1.0, max(0.0, (t - debut) / duree))


def tween(t: float, debut: float, duree: float, a: float = 0.0, b: float = 1.0, ease=power2_out) -> float:
    """Valeur qui va de a à b entre debut et debut + duree, avec l'easing donné. a avant, b après."""
    return a + (b - a) * ease(progress(t, debut, duree))


def alpha(t: float, debut: float, duree: float = 0.2, ease=power3_out) -> float:
    """Opacité 0 → 1 (une arrivée)."""
    return tween(t, debut, duree, 0.0, 1.0, ease)


def sortie(t: float, debut: float, duree: float = 0.13, ease=power3_in) -> float:
    """Opacité 1 → 0 (une sortie, plus courte qu'une arrivée)."""
    return tween(t, debut, duree, 1.0, 0.0, ease)


def compteur(t: float, debut: float, duree: float, valeur: float, ease=power2_out) -> int:
    """Compteur entier qui monte de 0 à valeur (arrondi, même règle partout)."""
    return int(round(tween(t, debut, duree, 0.0, valeur, ease)))


def mix(c1, c2, p: float):
    """Couleur interpolée entre c1 et c2 (p de 0 à 1), en RGB."""
    r1, g1, b1 = mcolors.to_rgb(c1)
    r2, g2, b2 = mcolors.to_rgb(c2)
    p = min(1.0, max(0.0, p))
    return (r1 + (r2 - r1) * p, g1 + (g2 - g1) * p, b1 + (b2 - b1) * p)


def decale(i: int, pas: float = 0.06) -> float:
    """Décalage d'un élément de liste (40–80 ms entre éléments)."""
    return i * pas


# ---------------------------------------------------------------------------
# Unités : la figure fait TAILLE pixels à 100 dpi ; les tailles de police sont en points.
# ---------------------------------------------------------------------------

DPI = 100


def px(pixels: float) -> float:
    """Taille de police en points pour une hauteur donnée en pixels (à 100 dpi : 28 px → 20,2 pt)."""
    return pixels * 72 / DPI


def mots(fig, liste, y: float, taille_px: float, poids: str = "bold", espace_px: float = 22.0):
    """
    Écrit une ligne de mots centrée, chaque mot avec sa couleur et son opacité :
    [(mot, couleur), ...] ou [(mot, couleur, alpha), ...].
    Mesure la largeur réelle de chaque mot pour les juxtaposer. Retourne la liste des artistes.
    """
    renderer = fig.canvas.get_renderer()
    largeur_fig = fig.get_figwidth() * fig.dpi
    artistes, largeurs = [], []
    for item in liste:
        mot, couleur = item[0], item[1]
        a_mot = item[2] if len(item) > 2 else 1.0
        a = fig.text(0, y, mot, fontsize=px(taille_px), fontweight=poids, color=couleur, ha="left", va="center", alpha=a_mot)
        largeurs.append(a.get_window_extent(renderer).width)
        artistes.append(a)
    total = sum(largeurs) + espace_px * (len(largeurs) - 1)
    x = (largeur_fig - total) / 2
    for a, w in zip(artistes, largeurs):
        a.set_x(x / largeur_fig)
        x += w + espace_px
    return artistes
