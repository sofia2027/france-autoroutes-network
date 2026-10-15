"""France autoroutes – Network growth: every autoroute section drawn the year it opened (1946–2025).

Usage (PowerShell, from this folder):
    python 01_network.py                 # every year -> output/frames_network/*.png + output/france_autoroutes_network.mp4
    python 01_network.py --year 2020     # one PNG -> output/network_2020.png
    python 01_network.py --size 1080 --spy 0.4

Needs data/app_data.json, data/bg.jpg and fonts/ next to this script.
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
import matplotlib.patheffects as pe
from PIL import Image

# ----------------------------------------------------------------- setup
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"      # app_data.json, bg.jpg
FONTS = HERE / "fonts"    # Source Serif 4, Inter, Oswald
for f in FONTS.glob("*.ttf"):
    fm.fontManager.addfont(str(f))
SERIF = fm.FontProperties(fname=str(FONTS / "SourceSerif4[opsz,wght].ttf"))
SANS = fm.FontProperties(fname=str(FONTS / "Inter[opsz,wght].ttf"))
COND = fm.FontProperties(fname=str(FONTS / "Oswald[wght].ttf"))

N = 1440                  # frame size in pixels
S = N / 1210              # pixels per km (map is 1210 km wide, Lambert-93)
OY = 113                  # top padding above the map
AMBER, WHITE, TXT, SUB, MUTE, FUTURE = "#E9A23B", "#FFF7E6", "#EDE6D6", "#B9B2A5", "#86827A", "#3B3F46"

CITIES = {'Paris': (2.35, 48.857), 'Lille': (3.06, 50.63), 'Strasbourg': (7.75, 48.58), 'Lyon': (4.84, 45.76),
          'Marseille': (5.37, 43.30), 'Bordeaux': (-0.58, 44.84), 'Toulouse': (1.44, 43.60), 'Nantes': (-1.55, 47.22),
          'Rennes': (-1.68, 48.11), 'Nice': (7.26, 43.70), 'Montpellier': (3.88, 43.61), 'Clermont-Ferrand': (3.08, 45.78),
          'Dijon': (5.04, 47.32), 'Rouen': (1.10, 49.44), 'Brest': (-4.49, 48.39), 'Limoges': (1.26, 45.83),
          'Grenoble': (5.72, 45.19), 'Metz': (6.18, 49.12), 'Reims': (4.03, 49.26), 'Tours': (0.69, 47.39),
          'Caen': (-0.37, 49.18), 'Perpignan': (2.90, 42.70), 'Bayonne': (-1.47, 43.49), 'Le Mans': (0.20, 48.00),
          'Poitiers': (0.34, 46.58), 'Mulhouse': (7.34, 47.75)}
RIGHT = {'Strasbourg', 'Mulhouse', 'Nice', 'Metz', 'Grenoble'}


def l93(lon, lat):
    """WGS84 -> Lambert-93 (EPSG:2154) metres."""
    e, n, C, xs, ys = 0.0818191910428158, 0.725607765053267, 11754255.426096, 700000, 12655612.049876
    phi = math.radians(lat)
    L = math.log(math.tan(math.pi / 4 + phi / 2) * ((1 - e * math.sin(phi)) / (1 + e * math.sin(phi))) ** (e / 2))
    R = C * math.exp(-n * L); g = n * math.radians(lon - 3)
    return xs + R * math.sin(g), ys - R * math.cos(g)


def px(v):  # data coordinates are Lambert-93 metres / 10
    return (np.asarray(v, dtype=float) * 10 - 60000) / 1000 * S


def py(v):
    return OY + (7135000 - np.asarray(v, dtype=float) * 10) / 1000 * S


def load():
    D = json.loads((DATA / "app_data.json").read_text(encoding="utf-8"))
    net = D["net"]
    D["segs"] = [np.c_[px(np.asarray(g).reshape(-1, 2)[:, 0]), py(np.asarray(g).reshape(-1, 2)[:, 1])] for g in net["geom"]]
    D["year"] = np.asarray(net["year"]); D["rkm"] = np.asarray(net["rkm"])
    D["bg"] = np.asarray(Image.open(DATA / "bg.jpg").convert("RGB"))
    return D


# ----------------------------------------------------------------- drawing helpers
def new_frame(D):
    fig = plt.figure(figsize=(N / 100, N / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, N); ax.set_ylim(N, 0); ax.axis("off")
    ax.imshow(D["bg"], extent=(0, N, N, 0))
    return fig, ax


def lines(ax, D, idx, color, lw, alpha=1.0):
    if len(idx):
        ax.add_collection(LineCollection([D["segs"][i] for i in idx], colors=color, linewidths=lw, alpha=alpha, capstyle="round"))


def legend_line(ax, y, color, lw, label):
    ax.plot([40, 74], [y, y], color=color, lw=lw, solid_capstyle="round")
    ax.text(84, y, label, fontproperties=SANS, fontsize=13, color=TXT, va="center")


def legend_dot(ax, y, color, size, label):
    ax.plot(57, y, "o", ms=size, color=color, mec="none")
    ax.text(84, y, label, fontproperties=SANS, fontsize=13, color=TXT, va="center")


def bars(ax, vals, cfun):
    """Small year histogram on the Atlantic side. vals = [(year, value), ...]"""
    hx, hy, hw, hh = 40, 840, 215, 120
    mx = max(v for _, v in vals) or 1; bw = hw / len(vals)
    for i, (yy, v) in enumerate(vals):
        h = v / mx * hh
        ax.add_patch(plt.Rectangle((hx + i * bw, hy - h), max(1, bw * 0.72), h, color=cfun(yy), lw=0))
    ax.text(hx, hy + 20, str(vals[0][0]), fontproperties=SANS, fontsize=11, color=SUB, va="center")
    ax.text(hx + hw, hy + 20, str(vals[-1][0]), fontproperties=SANS, fontsize=11, color=SUB, va="center", ha="right")


def big_number(ax, year, main, s1, s2=""):
    ax.text(36, 1000, str(year), fontproperties=COND, fontsize=92, color=WHITE, va="baseline")
    ax.text(39, 1046, main, fontproperties=COND, fontsize=30, color=AMBER, va="baseline")
    ax.text(39, 1074, s1, fontproperties=SANS, fontsize=11.5, color=SUB)
    if s2:
        ax.text(39, 1093, s2, fontproperties=SANS, fontsize=11.5, color=SUB)


def furniture(ax, title, subtitle, credit):
    halo = [pe.withStroke(linewidth=3, foreground=(0.03, 0.04, 0.06, 0.85))]
    for k, (lo, la) in CITIES.items():
        x, y = l93(lo, la); x, y = px(x / 10), py(y / 10)
        ax.plot(x, y, "o", ms=4.2, color="white", mec=(0, 0, 0, 0.6), mew=0.8)
        r = k in RIGHT
        ax.text(x + (-8 if r else 8), y - 6, k, fontproperties=SANS, fontsize=11.5, color="#E6E0D3",
                ha="right" if r else "left", va="bottom", path_effects=halo)
    ax.text(56, 92, title, fontproperties=SERIF, fontsize=44, color=TXT, va="baseline")
    ax.text(58, 132, subtitle, fontproperties=SANS, fontsize=16, color=SUB)
    ax.text(58, 158, "Mainland France, autoroutes only (A-roads, conceded and non-conceded)", fontproperties=SANS, fontsize=11.5, color=MUTE)
    ax.text(N - 24, N - 36, credit, fontproperties=SANS, fontsize=10, color=MUTE, ha="right")
    ax.text(N - 24, N - 18, "Relief: AWS Terrain Tiles, path-traced with forge3d · Natural Earth", fontproperties=SANS, fontsize=10, color=MUTE, ha="right")


def to_image(fig):
    fig.canvas.draw()
    img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
    plt.close(fig)
    return img


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def run(name, years, draw):
    """Command line: python script.py [--year 2024] [--size 1080] [--spy 0.32] [--out folder]"""
    ap = argparse.ArgumentParser(description=f"France autoroutes – {name}")
    ap.add_argument("--year", type=int, help="render one PNG for this year only")
    ap.add_argument("--size", type=int, default=1440, help="output size in pixels (square)")
    ap.add_argument("--spy", type=float, default=0.32, help="seconds per year in the video")
    ap.add_argument("--out", default=str(HERE / "output"), help="output folder")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    D = load()
    ys = years(D)
    todo = [a.year] if a.year else ys
    if a.year and a.year not in ys:
        sys.exit(f"No data for {a.year}. Available years: {ys[0]}–{ys[-1]} ({len(ys)} years)")
    frames = out / f"frames_{name}"
    if not a.year:
        frames.mkdir(exist_ok=True)
    for i, y in enumerate(todo):
        im = draw(D, y)
        if a.size != N:
            im = im.resize((a.size, a.size), Image.LANCZOS)
        p = (out / f"{name}_{y}.png") if a.year else (frames / f"{name}_{y}.png")
        im.save(p)
        print(f"\r{name}: {y} ({i + 1}/{len(todo)})", end="", flush=True)
    print()
    if a.year:
        print("Saved", out / f"{name}_{a.year}.png"); return
    lst = frames / "list.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for i, y in enumerate(ys):
            d = 1.2 if i == 0 else (4.0 if i == len(ys) - 1 else a.spy)
            f.write(f"file '{(frames / f'{name}_{y}.png').as_posix()}'\nduration {d}\n")
        f.write(f"file '{(frames / f'{name}_{ys[-1]}.png').as_posix()}'\n")
    mp4 = out / f"france_autoroutes_{name}.mp4"
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", str(mp4)], check=True)
    print("Saved", mp4, "and frames in", frames)


# ----------------------------------------------------------------- layer: network growth
def years(D):
    return list(range(1946, 2026))


def draw(D, year):
    yrs, rkm = D["year"], D["rkm"]
    cum = {y: float(rkm[yrs <= y].sum()) for y in years(D)}
    fig, ax = new_frame(D)
    lines(ax, D, np.where(yrs < year)[0], AMBER, 1.5, 0.95)          # opened earlier
    new = np.where(yrs == year)[0]
    lines(ax, D, new, WHITE, 7, 0.18); lines(ax, D, new, WHITE, 2.6)  # opened this year, with glow
    legend_line(ax, 650, WHITE, 2.6, f"Opened in {year}")
    legend_line(ax, 680, AMBER, 2.6, "Opened earlier")
    bars(ax, list(cum.items()), lambda y: WHITE if y == year else (AMBER if y < year else FUTURE))
    big_number(ax, year, f"{cum[year]:,.0f} km", "of autoroute open, measured", "from OpenStreetMap lines")
    furniture(ax, "France's autoroutes", "Every section drawn the year it opened, 1946–2025",
              "Roads © OpenStreetMap contributors · Opening years: French Wikipedia")
    return to_image(fig)


if __name__ == "__main__":
    run("network", years, draw)
