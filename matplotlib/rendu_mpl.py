#!/usr/bin/env python3
"""
rendu_mpl.py — rend une scène matplotlib en MP4, image par image, sans navigateur.

La scène est un fichier Python qui définit :
    DUREE  = 11.0            # secondes
    TAILLE = (1920, 1080)    # pixels (optionnel, défaut 1920x1080)
    def draw(fig, t): ...    # dessine l'image de l'instant t dans la figure (déjà vide)

Pour chaque image i : on vide la figure, on appelle draw(fig, i / fps), on récupère les pixels
et on les envoie à FFmpeg qui encode le MP4. Rien n'est conservé entre deux images : ce que
l'on voit à l'instant t ne dépend que de t, donc le rendu est reproductible.

Usage :
    python rendu_mpl.py exemple_barres.py sortie.mp4
    python rendu_mpl.py exemple_barres.py brouillon.mp4 --fps 5     # brouillon rapide
    python rendu_mpl.py scene.py sortie.gif --gif                     # sans FFmpeg (plus lourd, qualité moindre)

Dépendances : matplotlib (numpy, pillow viennent avec) ; ffmpeg dans le PATH,
ou `pip install imageio-ffmpeg` (la wheel embarque le binaire), ou --gif.
"""

import argparse
import importlib.util
import logging
import pathlib
import shutil
import subprocess
import sys
import time

import matplotlib

matplotlib.use("Agg")  # rendu hors écran, sans fenêtre
import matplotlib.pyplot as plt  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)  # silence « font not found »


def trouver_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def charger_scene(chemin: pathlib.Path):
    sys.path.insert(0, str(chemin.parent))  # pour `from anim import *` dans la scène
    spec = importlib.util.spec_from_file_location("scene", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "draw") or not hasattr(module, "DUREE"):
        sys.exit("La scène doit définir DUREE (secondes) et draw(fig, t).")
    return module


def main() -> None:
    ap = argparse.ArgumentParser(description="Rend une scène matplotlib (draw(fig, t)) en vidéo.")
    ap.add_argument("scene", help="fichier Python de la scène")
    ap.add_argument("sortie", help="fichier .mp4 (ou .gif avec --gif)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--duration", type=float, default=None, help="durée en s (défaut : DUREE de la scène)")
    ap.add_argument("--crf", type=int, default=18, help="qualité H.264 (18 = quasi sans perte)")
    ap.add_argument("--gif", action="store_true", help="écrit un GIF avec Pillow, sans FFmpeg")
    args = ap.parse_args()

    scene = charger_scene(pathlib.Path(args.scene).resolve())
    w, h = getattr(scene, "TAILLE", (1920, 1080))
    duree = args.duration or float(scene.DUREE)
    nb = round(duree * args.fps)
    dpi = 100
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    print(f"{pathlib.Path(args.scene).name} → {args.sortie} : {nb} images, {w}x{h} @ {args.fps} i/s, {duree:.2f} s")

    ffmpeg = None if args.gif else trouver_ffmpeg()
    if not args.gif and ffmpeg is None:
        sys.exit("ffmpeg introuvable : installe-le, `pip install imageio-ffmpeg`, ou utilise --gif.")

    proc, images = None, []
    if ffmpeg:
        proc = subprocess.Popen(
            [ffmpeg, "-y", "-loglevel", "error",
             "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", str(args.fps), "-i", "-",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(args.crf), "-movflags", "+faststart", args.sortie],
            stdin=subprocess.PIPE,
        )

    t0 = time.time()
    for i in range(nb):
        t = i / args.fps
        fig.clear()                       # repart de zéro : aucun état hérité de l'image précédente
        scene.draw(fig, t)                # l'image de l'instant t
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()    # les pixels (h, w, 4)
        if buf.shape[:2] != (h, w):
            sys.exit(f"Taille inattendue {buf.shape[1]}x{buf.shape[0]} (attendu {w}x{h}) : ne change pas la figure dans draw().")
        if proc:
            proc.stdin.write(bytes(buf))
        else:
            from PIL import Image

            images.append(Image.frombuffer("RGBA", (w, h), bytes(buf)).convert("RGB"))
        if i % args.fps == 0 or i == nb - 1:
            print(f"  image {i + 1}/{nb}  (t = {t:.2f} s)", end="\r", flush=True)

    if proc:
        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            sys.exit(f"\nffmpeg a échoué (code {proc.returncode}).")
    else:
        images[0].save(args.sortie, save_all=True, append_images=images[1:], duration=round(1000 / args.fps), loop=0)
    print(f"\nTerminé en {time.time() - t0:.1f} s → {args.sortie}")


if __name__ == "__main__":
    main()
