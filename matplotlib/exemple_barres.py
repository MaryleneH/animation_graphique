"""
exemple_barres.py — un graphique en barres animé, en matplotlib, sans navigateur.

Le même film que la version HTML : un titre, puis un graphique qui se construit dans l'ordre
de lecture (cadre et axe, ligne de référence, les barres avec leur compteur, puis une seule
annotation sur la valeur qui compte). Données fictives, à titre d'illustration.

Rendu : python rendu_mpl.py exemple_barres.py sortie.mp4
"""

import matplotlib
from matplotlib.lines import Line2D
from matplotlib.patheffects import withStroke
from matplotlib.transforms import blended_transform_factory

from anim import *  # noqa: F401,F403 — tween, alpha, sortie, compteur, mix, px, mots, easings

# ---------------------------------------------------------------------------
# Paramètres de la vidéo
# ---------------------------------------------------------------------------
DUREE = 11.0
TAILLE = (1920, 1080)
W, H = TAILLE

matplotlib.rcParams["font.family"] = ["Inter", "Segoe UI", "Arial", "DejaVu Sans"]  # repli si une police manque

# Palette
GROUND, INK, MUTED, ACCENT = "#0b1320", "#f3f5f7", "#8a97a8", "#ff8a3d"
BAR, DIM, GREY, GRID, AXIS = "#4f8df7", "#27354a", "#3b475a", "#223047", "#5b6b82"

# Un seul module de données pilote toutes les valeurs (même arrondi partout)
DATA = [18, 34, 15, 9, 12, 12]
CATEGORIES = ["Collecte", "Nettoyage", "Modélisation", "Évaluation", "Déploiement", "Documentation"]
HIGHLIGHT = 1  # Nettoyage
MOYENNE = 16.7

HALO = [withStroke(linewidth=6, foreground=GROUND)]  # halo couleur du fond : texte lisible sur la grille


def fy(y_px: float) -> float:
    """Ordonnée en pixels depuis le haut → fraction de figure (matplotlib compte depuis le bas)."""
    return 1 - y_px / H


# ---------------------------------------------------------------------------
# Scène 1 : le titre (0 → 4 s)
# ---------------------------------------------------------------------------
def scene_titre(fig, t):
    texte = ["Un", "graphique", "animé,", "écrit", "en", "Python"]
    liste = []
    for i, mot in enumerate(texte):
        cible = ACCENT if mot == "animé," else INK
        couleur = mix(GREY, cible, tween(t, 0.1 + i * 0.09, 0.25))      # gris → encre, mot par mot
        a = sortie(t, 3.45 + i * 0.05, 0.13)                               # puis disparaît, mot par mot
        liste.append((mot, couleur, a))
    mots(fig, liste, y=fy(468), taille_px=84)

    a_sub = alpha(t, 0.6, 0.2) * sortie(t, 3.55, 0.18)
    fig.text(0.5, fy(578), "Chaque image est une fonction du temps", fontsize=px(36), color=MUTED, alpha=a_sub, ha="center", va="center")


# ---------------------------------------------------------------------------
# Scène 2 : le graphique (4 → 11 s)
# ---------------------------------------------------------------------------
def scene_graphique(fig, t):
    S = 4.0  # début de la scène

    # 1) Le titre dit la seule chose que le graphique a à dire
    fig.text(0.1, fy(108), "Où passe le temps d'un projet data ?", fontsize=px(64), fontweight="bold",
             color=INK, alpha=alpha(t, S, 0.2), ha="left", va="top")
    fig.text(0.1, fy(196), "Part de chaque étape, en % du temps total", fontsize=px(30),
             color=MUTED, alpha=alpha(t, S + 0.15, 0.2), ha="left", va="top")

    # La zone du graphique : x de 192 à 1728 px, y de 300 (40 %) à 880 px (0 %)
    ax = fig.add_axes([192 / W, fy(880), (1728 - 192) / W, (880 - 300) / H])
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(0, 40)
    ax.axis("off")
    ax.set_facecolor("none")
    tr_grille = blended_transform_factory(ax.transAxes, ax.transData)  # x en fraction d'axe, y en données

    # 2) Le cadre : la grille apparaît, l'axe se trace de gauche à droite
    for i, v in enumerate([10, 20, 30, 40]):
        a = alpha(t, S + 0.45 + i * 0.06, 0.25)
        ax.plot([0, 1], [v, v], transform=tr_grille, color=GRID, lw=1.5, alpha=a, zorder=1)
        ax.text(-0.015, v, f"{v} %", transform=tr_grille, fontsize=px(28), color=MUTED,
                alpha=alpha(t, S + 0.5 + i * 0.06, 0.25), ha="right", va="center")
    p_axe = tween(t, S + 0.3, 0.5, ease=power2_inout)
    ax.plot([0, p_axe], [0, 0], transform=ax.transAxes, color=AXIS, lw=2.5, zorder=2, solid_capstyle="butt")
    for i, nom in enumerate(CATEGORIES):
        ax.text(i, -3.5, nom, fontsize=px(30), color=INK, alpha=alpha(t, S + 0.7 + i * 0.06, 0.2), ha="center", va="center")
    fig.text(0.1, fy(974), "Données fictives, à titre d'illustration — rendu matplotlib → MP4", fontsize=px(28),
             color=MUTED, alpha=alpha(t, S + 0.8, 0.2), ha="left", va="top")

    # 3) La ligne de référence (la moyenne)
    p_ref = tween(t, S + 1.1, 0.45, ease=power2_inout)
    ax.plot([0, p_ref], [MOYENNE, MOYENNE], transform=tr_grille, color=MUTED, lw=2, ls=(0, (6, 5)), zorder=1)
    ax.text(1.0, MOYENNE + 0.8, "moyenne : 16,7 %", transform=tr_grille, fontsize=px(28), color=MUTED,
            alpha=alpha(t, S + 1.45, 0.15), ha="right", va="bottom", path_effects=HALO)

    # 4) Les données se dessinent : chaque barre pousse depuis sa base, son compteur monte en 1,4 s
    T_BARS, T_NOTE = S + 1.7, S + 3.5
    p_note = tween(t, T_NOTE, 0.4, ease=power2_inout)  # 0 avant l'annotation, 1 après
    for i, valeur in enumerate(DATA):
        at = T_BARS + i * 0.07
        hauteur = valeur * tween(t, at, 0.9, ease=expo_out)
        hero = i == HIGHLIGHT
        couleur = mix(BAR, ACCENT if hero else DIM, p_note)
        ax.bar(i, hauteur, width=0.54, color=couleur, zorder=3)
        ax.text(i, valeur + 1.2, f"{compteur(t, at, 1.4, valeur)} %", fontsize=px(40), fontweight="bold",
                color=mix(INK, ACCENT if hero else MUTED, p_note), alpha=alpha(t, at, 0.15),
                ha="center", va="bottom", path_effects=HALO, zorder=4)

    # 5) Une seule annotation, posée sur la marque qui compte
    x0, dx = 652 / W, 56 / W
    p_ligne = tween(t, S + 3.7, 0.25)
    fig.add_artist(Line2D([x0, x0 + dx * p_ligne], [fy(380), fy(380)], transform=fig.transFigure, color=ACCENT, lw=3))
    fig.text(x0, fy(396), "Un tiers du temps\npart dans le nettoyage", fontsize=px(36), fontweight="bold",
             color=ACCENT, alpha=alpha(t, S + 3.72, 0.13), ha="left", va="top", linespacing=1.2)


# ---------------------------------------------------------------------------
# Le contrat : draw(fig, t) dessine l'image de l'instant t, à partir de t seulement
# ---------------------------------------------------------------------------
def draw(fig, t):
    fig.patch.set_facecolor(GROUND)
    if t < 4.0:
        scene_titre(fig, t)
    else:
        scene_graphique(fig, t)
