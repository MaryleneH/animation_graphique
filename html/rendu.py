#!/usr/bin/env python3
"""
rendu.py — transforme une page HTML animée en vidéo MP4, image par image.

Principe (le même qu'HyperFrames, réduit à l'essentiel) :
  1. Chromium (piloté par Playwright) ouvre la page en mode headless.
  2. Pour chaque image i, on appelle window.renderAt(i / fps) : la page se met
     dans l'état de l'instant t. Rien ne « joue » : tout est fonction de t.
  3. On photographie la page (PNG) et on envoie l'image à FFmpeg, qui encode le MP4.

Contrat de la page HTML (ce qu'AI Chat du SSP Cloud doit produire) :
  - window.renderAt(t)  : fonction qui met la page dans l'état de l'instant t (secondes)
  - window.__duration   : durée totale en secondes
  (voir docs/prompt-ai-chat-html.md pour le contrat complet)

Usage :
  python rendu.py exemple_graphique.html sortie.mp4
  python rendu.py page.html sortie.mp4 --fps 30 --width 1920 --height 1080
  python rendu.py page.html sortie.mp4 --channel msedge            # Edge déjà installé (poste hors ligne)
  python rendu.py page.html sortie.mp4 --executable-path "C:/Program Files/Google/Chrome/Application/chrome.exe"
  python rendu.py page.html sortie.mp4 --browser-arg=--no-zygote --browser-arg=--single-process   # conteneur Linux récalcitrant

Dépendances : pip install playwright  (+ `playwright install chromium` si on a Internet,
sinon --channel ou --executable-path vers un Chrome/Edge déjà présent) ; ffmpeg dans le PATH
(sinon `pip install imageio-ffmpeg`, qui embarque un binaire).
"""

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright


def trouver_ffmpeg() -> str:
    """ffmpeg du PATH, sinon le binaire embarqué par le paquet pip imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg introuvable : installe-le, ou `pip install imageio-ffmpeg`.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Rend une page HTML animée (window.renderAt) en MP4.")
    ap.add_argument("html", help="page HTML à rendre")
    ap.add_argument("sortie", help="fichier .mp4 de sortie")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--duration", type=float, default=None, help="durée en s (défaut : window.__duration)")
    ap.add_argument("--crf", type=int, default=18, help="qualité H.264 (18 = quasi sans perte, 23 = défaut ffmpeg)")
    ap.add_argument("--channel", default=None, help="navigateur du poste : chrome, msedge, chromium…")
    ap.add_argument("--executable-path", default=None, help="chemin explicite d'un Chrome/Chromium")
    ap.add_argument("--browser-arg", action="append", default=[],
                    help="option supplémentaire passée au navigateur (répétable), ex. --browser-arg=--no-zygote")
    args = ap.parse_args()

    html = pathlib.Path(args.html).resolve()
    if not html.exists():
        sys.exit(f"Fichier introuvable : {html}")
    ffmpeg = trouver_ffmpeg()

    with sync_playwright() as p:
        options = {"headless": True, "args": ["--no-sandbox", "--disable-gpu", "--hide-scrollbars", *args.browser_arg]}
        if args.channel:
            options["channel"] = args.channel
        if args.executable_path:
            options["executable_path"] = args.executable_path
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={"width": args.width, "height": args.height}, device_scale_factor=1)

        # Ouvre le fichier local ; aucune requête réseau n'est nécessaire si la page est autonome.
        page.goto(html.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")  # attend les polices avant la première image

        if not page.evaluate("typeof window.renderAt === 'function'"):
            sys.exit("La page ne définit pas window.renderAt(t) : voir le contrat dans docs/prompt-ai-chat-html.md.")
        duration = args.duration or page.evaluate("Number(window.__duration) || 0")
        if duration <= 0:
            sys.exit("Durée inconnue : définis window.__duration dans la page ou passe --duration.")

        nb = round(duration * args.fps)
        print(f"{html.name} → {args.sortie} : {nb} images, {args.width}x{args.height} @ {args.fps} i/s, {duration:.2f} s")

        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(args.fps), "-i", "-",   # PNG reçus sur stdin
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(args.crf),
            "-movflags", "+faststart", args.sortie,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        assert proc.stdin is not None

        t0 = time.time()
        for i in range(nb):
            t = i / args.fps
            # Bloc { … } sans return : Playwright ne doit rien recevoir à sérialiser.
            # (tl.seek() renvoie la timeline entière, un graphe circulaire : la sérialiser bloque tout.)
            page.evaluate("t => { window.renderAt(t); }", t)   # l'état de la page à l'instant t
            proc.stdin.write(page.screenshot(type="png"))      # une photo → une image de la vidéo
            if i % args.fps == 0 or i == nb - 1:
                print(f"  image {i + 1}/{nb}  (t = {t:.2f} s)", end="\r", flush=True)
        proc.stdin.close()
        proc.wait()
        browser.close()

    if proc.returncode != 0:
        sys.exit(f"\nffmpeg a échoué (code {proc.returncode}).")
    print(f"\nTerminé en {time.time() - t0:.1f} s → {args.sortie}")


if __name__ == "__main__":
    main()
