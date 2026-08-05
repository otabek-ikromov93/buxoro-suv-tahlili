# -*- coding: utf-8 -*-
"""
03_grafiklar.py
---------------
Таҳлил натижалари бўйича 10 та график тайёрлайди (PNG, 200 dpi + SVG).

Ранг тизими: валидациядан ўтган стандарт палитра.
  - Миқдорни солиштириш   -> кетма-кет (sequential) кўк рамп, кўпроқ = тўқроқ
  - Қутбийлик (+/-)       -> дивергент кўк <-> қизил, нейтрал кулранг марказ
  - Идентиклик (зона, усул) -> категориал 1-3 слот (кўк / тўқ сариқ / аква)
Ҳар бир графикда қиймат ёрлиқлари бевосита кўрсатилган (relief rule),
икки ўқли (dual-axis) графиклар ишлатилмаган.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "natijalar")
GRAF = os.path.join(ROOT, "grafiklar")
os.makedirs(GRAF, exist_ok=True)

# --- Палитра -----------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"      # категориал 1-3
NEUTRAL = "#f0efec"
DIV_POS, DIV_NEG = "#2a78d6", "#d03b3b"           # дивергент қутблар
BLUE_RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
             "#0d366b"]
CMAP_BLUE = LinearSegmentedColormap.from_list("blues", BLUE_RAMP)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8,
    "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})


def saqla(fig, nom):
    for kengaytma in ("png", "svg"):
        fig.savefig(os.path.join(GRAF, f"{nom}.{kengaytma}"))
    plt.close(fig)
    print("  ", nom + ".png / .svg")


def sarlavha(ax, matn, izoh=None):
    ax.set_title(matn, loc="left", fontsize=13, fontweight="600",
                 color=INK, pad=16 if izoh else 10)
    if izoh:
        ax.text(0, 1.015, izoh, transform=ax.transAxes, fontsize=9.5,
                color=INK2, va="bottom")


def rounded_hbar(ax, y, width, height, color, r_frac=0.45, x0=0.0):
    """Маълумот учи юмалоқланган горизонтал устун (асос томони тўғри)."""
    r = min(abs(width) * 0.5, height * r_frac)
    s = np.sign(width) if width != 0 else 1.0
    x1 = x0 + width
    xa = x1 - s * r
    y0, y1 = y - height / 2, y + height / 2
    verts = [(x0, y0), (xa, y0),
             (x1, y0), (x1, y), (x1, y1),
             (xa, y1), (x0, y1), (x0, y0)]
    codes = [Path.MOVETO, Path.LINETO,
             Path.CURVE3, Path.CURVE3, Path.CURVE3, Path.CURVE3,
             Path.LINETO, Path.CLOSEPOLY]
    # икки бурчак учун иккита квадратик эгри
    verts = [(x0, y0), (xa, y0), (x1, y0), (x1, y),
             (x1, y1), (xa, y1), (x0, y1), (x0, y0)]
    codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3,
             Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color,
                           edgecolor="none", clip_on=True))


def ramp_rang(qiymatlar, past=0.25, yuqori=0.92):
    q = np.asarray(qiymatlar, float)
    if q.max() == q.min():
        return [CMAP_BLUE(0.6)] * len(q)
    n = (q - q.min()) / (q.max() - q.min())
    return [CMAP_BLUE(past + (yuqori - past) * v) for v in n]


# --- Маълумотлар -------------------------------------------------------------
df = pd.read_csv(os.path.join(OUT, "panel_tolik_natijalar.csv"), encoding="utf-8-sig")
bal = pd.read_csv(os.path.join(OUT, "A_viloyat_suv_balansi.csv"), encoding="utf-8-sig")
sen = pd.read_csv(os.path.join(OUT, "I_senariylar.csv"), encoding="utf-8-sig")
lor = pd.read_csv(os.path.join(OUT, "D_lorenz_yalpi_suv.csv"), encoding="utf-8-sig")
with open(os.path.join(OUT, "kalit_korsatkichlar.json"), encoding="utf-8") as f:
    K = json.load(f)

d24 = df[df.yil == 2024].copy()
ZONA_NOM = {"bosh": "Канал боши", "orta": "Ўрта оқим", "oxirgi": "Канал охири"}
ZONA_RANG = {"bosh": S1, "orta": S2, "oxirgi": S3}
MANBA = ("Манба: муаллиф ҳисоб-китоблари. Маълумотлар АБМК тизими ва вилоят "
         "статистикасининг эълон қилинган йиғма кўрсаткичларига лангарланган.")

print("Графиклар тайёрланмоқда...")

# ===========================================================================
# 1. Сувнинг туманлар кесимида тақсимланиши (2024)
# ===========================================================================
g = d24.sort_values("suv_mln_m3")
fig, ax = plt.subplots(figsize=(9, 6))
ranglar = ramp_rang(g.suv_mln_m3)
for i, (v, c) in enumerate(zip(g.suv_mln_m3, ranglar)):
    rounded_hbar(ax, i, v, 0.68, c)
    ax.text(v + g.suv_mln_m3.max() * 0.015, i, f"{v:,.0f}", va="center",
            ha="left", fontsize=9.5, color=INK, fontweight="600")
    ulush = v / g.suv_mln_m3.sum() * 100
    ax.text(v + g.suv_mln_m3.max() * 0.135, i, f"{ulush:.1f}%", va="center",
            ha="left", fontsize=9, color=MUTED)
ax.set_yticks(range(len(g)))
ax.set_yticklabels(g.tuman, fontsize=10.5, color=INK)
ax.set_xlim(0, g.suv_mln_m3.max() * 1.22)
ax.set_ylim(-0.7, len(g) - 0.3)
ax.set_xlabel("млн м³/йил")
ax.xaxis.grid(True, alpha=0.9); ax.set_axisbelow(True)
ax.yaxis.grid(False)
sarlavha(ax, "Амударёдан олинган сувнинг туманлар кесимида тақсимланиши",
         f"2024 йил · жами {g.suv_mln_m3.sum():,.0f} млн м³ · "
         f"ўнг томонда — вилоят бўйича улуши")
fig.text(0.01, -0.02, MANBA, fontsize=8, color=MUTED, wrap=True)
saqla(fig, "01_suv_taqsimoti_tumanlar")

# ===========================================================================
# 2. Сув улуши ва майдон улуши ўртасидаги фарқ (дивергент)
# ===========================================================================
d24["suv_ulush"] = d24.suv_mln_m3 / d24.suv_mln_m3.sum() * 100
d24["maydon_ulush"] = d24.maydon_ming_ga / d24.maydon_ming_ga.sum() * 100
d24["farq"] = d24.suv_ulush - d24.maydon_ulush
g = d24.sort_values("farq")
fig, ax = plt.subplots(figsize=(9, 6))
for i, (v, tn) in enumerate(zip(g.farq, g.tuman)):
    rounded_hbar(ax, i, v, 0.68, DIV_POS if v >= 0 else DIV_NEG)
    ofs = 0.05 if v >= 0 else -0.05
    ax.text(v + ofs, i, f"{v:+.2f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=9.5,
            color=INK, fontweight="600")
ax.axvline(0, color=BASE, lw=1.2, zorder=3)
ax.set_yticks(range(len(g)))
ax.set_yticklabels(g.tuman, fontsize=10.5, color=INK)
lim = max(abs(g.farq)) * 1.45
ax.set_xlim(-lim, lim); ax.set_ylim(-0.7, len(g) - 0.3)
ax.set_xlabel("сув улуши − суғориладиган майдон улуши, фоиз пункт")
ax.xaxis.grid(True, alpha=0.9); ax.set_axisbelow(True); ax.yaxis.grid(False)
sarlavha(ax, "Сув тақсимоти майдон улушига мос келадими?",
         "Мусбат қиймат — туман ўз ер улушига нисбатан кўпроқ сув олмоқда "
         "(шўрланиш, юввиш суви, канал охиридаги йўқотишлар)")
fig.text(0.01, -0.02, MANBA, fontsize=8, color=MUTED)
saqla(fig, "02_suv_maydon_farqi")

# ===========================================================================
# 3. Сув унумдорлиги рейтинги (зона бўйича идентиклик)
# ===========================================================================
g = d24.sort_values("wp_som_m3")
fig, ax = plt.subplots(figsize=(9.5, 6))
for i, r in enumerate(g.itertuples()):
    rounded_hbar(ax, i, r.wp_som_m3, 0.68, ZONA_RANG[r.zona])
    ax.text(r.wp_som_m3 + 60, i, f"{r.wp_som_m3:,.0f}", va="center", ha="left",
            fontsize=9.5, color=INK, fontweight="600")
    ax.text(r.wp_som_m3 + 620, i, f"({r.wp_usd_m3:.3f} $)", va="center",
            ha="left", fontsize=8.5, color=MUTED)
ort = d24.yalpi_joriy_mlrd.sum() * 1e9 / (d24.suv_mln_m3.sum() * 1e6)
ax.axvline(ort, color=INK2, lw=1.4, ls=(0, (5, 3)), zorder=4)
ax.text(ort, len(g) - 0.35, f" вилоят ўртачаси {ort:,.0f}", fontsize=9,
        color=INK2, va="bottom", ha="left")
ax.set_yticks(range(len(g)))
ax.set_yticklabels(g.tuman, fontsize=10.5, color=INK)
ax.set_xlim(0, g.wp_som_m3.max() * 1.30); ax.set_ylim(-0.7, len(g) + 0.35)
ax.set_xlabel("1 м³ сувга тўғри келадиган ялпи маҳсулот, сўм (жорий нарх)")
ax.xaxis.grid(True, alpha=0.9); ax.set_axisbelow(True); ax.yaxis.grid(False)
ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=9, color=ZONA_RANG[k],
                          label=ZONA_NOM[k]) for k in ["bosh", "orta", "oxirgi"]],
          loc="lower right", frameon=False, fontsize=9.5, labelcolor=INK2)
sarlavha(ax, "Сувдан фойдаланиш самарадорлиги: 1 м³ сув қанча даромад беради",
         f"2024 йил · канал бошидаги туманлар охиридагиларга нисбатан "
         f"сезиларли устун (ANOVA F = {K['anova_F']:.2f}, p = {K['anova_p']:.3f})")
fig.text(0.01, -0.02, MANBA, fontsize=8, color=MUTED)
saqla(fig, "03_suv_unumdorligi_reyting")

# ===========================================================================
# 4. Динамика: 2014 = 100 индекс (икки ўқдан қочиш учун индекслаштирилган)
# ===========================================================================
vil = (df.groupby("yil")
         .agg(yalpi_real=("yalpi_2018narx_mlrd", "sum"),
              maydon=("maydon_ming_ga", "sum")).reset_index()
         .merge(bal[["yil", "amudaryodan_mln_m3"]], on="yil"))
vil["wp_real"] = vil.yalpi_real * 1e9 / (vil.amudaryodan_mln_m3 * 1e6)
baza = vil.iloc[0]
seriyalar = [("Амударёдан олинган сув", "amudaryodan_mln_m3", S1),
             ("Ялпи маҳсулот (2018 нархида)", "yalpi_real", S2),
             ("Сув унумдорлиги (сўм/м³, реал)", "wp_real", S3)]
fig, ax = plt.subplots(figsize=(9.5, 5.6))
for nom, ust, rang in seriyalar:
    y = vil[ust] / baza[ust] * 100
    ax.plot(vil.yil, y, color=rang, lw=2, marker="o", ms=5.5,
            mfc=rang, mec=SURFACE, mew=1.6, label=nom, zorder=3)
    ax.annotate(f"{y.iloc[-1]:,.0f}", (vil.yil.iloc[-1], y.iloc[-1]),
                xytext=(8, 0), textcoords="offset points", fontsize=10,
                color=INK, fontweight="600", va="center")
ax.axhline(100, color=BASE, lw=1)
ax.axvspan(2020.5, 2021.5, color=NEUTRAL, zorder=0)
ax.text(2021, ax.get_ylim()[1], " камсув\n йил", fontsize=8.5, color=MUTED,
        va="top", ha="center")
ax.set_xticks(vil.yil)
ax.set_xlim(vil.yil.min() - 0.3, vil.yil.max() + 1.1)
ax.set_ylabel("индекс, 2014 = 100")
ax.yaxis.grid(True, alpha=0.9); ax.set_axisbelow(True)
ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK2)
sarlavha(ax, "Сув сарфи барқарор, маҳсулот ва сув унумдорлиги ўсмоқда",
         "Вилоят бўйича, 2014 = 100 · инфляция таъсири 2018 йил "
         "солиштирма нархига келтириб чиқарилган")
fig.text(0.01, -0.03, MANBA, fontsize=8, color=MUTED)
saqla(fig, "04_dinamika_indeks")

# ===========================================================================
# 5. Сув сарфи <-> маҳсулот боғланиши (эластиклик)
# ===========================================================================
x = np.log(df.suv_mln_m3 / df.maydon_ming_ga)
y = np.log(df.yalpi_2018narx_mlrd / df.maydon_ming_ga)
kf = np.polyfit(x, y, 1)
xs = np.linspace(x.min(), x.max(), 100)
fig, ax = plt.subplots(figsize=(8.6, 5.8))
ax.scatter(x, y, s=46, c=S1, alpha=0.55, edgecolors=SURFACE, lw=1.2, zorder=3)
ax.plot(xs, np.polyval(kf, xs), color=DIV_NEG, lw=2, zorder=4,
        label=f"регрессия чизиғи (нишаб = {kf[0]:.3f})")
ax.set_xlabel("ln(1 га га сув сарфи)")
ax.set_ylabel("ln(1 га га ялпи маҳсулот, 2018 нархида)")
ax.grid(True, alpha=0.9); ax.set_axisbelow(True)
ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK2)
r = np.corrcoef(x, y)[0, 1]
ax.text(0.98, 0.04, f"n = {len(x)} кузатув (11 туман × 11 йил)\n"
                    f"корреляция r = {r:.3f}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        color=INK2)
sarlavha(ax, "Сув сарфи ва ҳосилдорлик ўртасидаги боғланиш",
         f"Панель FE баҳоси бўйича сув эластиклиги {K['suv_elastikligi']:.3f} — "
         f"сув 10% га камайса, маҳсулот ~{K['suv_elastikligi']*10:.1f}% га камаяди")
fig.text(0.01, -0.03, MANBA, fontsize=8, color=MUTED)
saqla(fig, "05_suv_mahsulot_boglanishi")

# ===========================================================================
# 6. DEA ва SFA самарадорлик балллари
# ===========================================================================
sam = (df.groupby("tuman").agg(dea=("dea_crs", "mean"), sfa=("sfa_te", "mean"))
       .sort_values("dea").reset_index())
# Балллар 1.000 га жуда яқин бўлгани учун устун (bar) шакли фарқларни
# кўрсата олмайди — dot-plot ишлатилади: маркер УЗУНЛИКНИ эмас, ЎРИННИ
# кодлайди, шу боис ўқни 0 дан бошламаслик мумкин.
fig, ax = plt.subplots(figsize=(9.5, 6.2))
for i, r in enumerate(sam.itertuples()):
    ax.plot([min(r.dea, r.sfa), max(r.dea, r.sfa)], [i, i],
            color=BASE, lw=2, zorder=2, solid_capstyle="round")
    ax.plot(r.dea, i, marker="o", ms=10, color=S1, mec=SURFACE, mew=1.6,
            zorder=3)
    ax.plot(r.sfa, i, marker="o", ms=10, color=S2, mec=SURFACE, mew=1.6,
            zorder=3)
    chap, ong = (r.dea, r.sfa) if r.dea < r.sfa else (r.sfa, r.dea)
    ax.text(chap - 0.006, i, f"{chap:.3f}", va="center", ha="right",
            fontsize=8.8, color=INK2)
    ax.text(ong + 0.006, i, f"{ong:.3f}", va="center", ha="left",
            fontsize=8.8, color=INK2)
ax.axvline(1.0, color=BASE, lw=1.2, zorder=1)
ax.text(1.0, len(sam) - 0.35, " чегара = 1.000", fontsize=9, color=MUTED,
        va="bottom")
ax.set_yticks(range(len(sam)))
ax.set_yticklabels(sam.tuman, fontsize=10.5, color=INK)
ax.set_xlim(0.70, 1.045); ax.set_ylim(-0.9, len(sam) - 0.15)
ax.set_xlabel("самарадорлик балли (1.000 = самарали чегарада)")
ax.xaxis.grid(True, alpha=0.9); ax.set_axisbelow(True); ax.yaxis.grid(False)
ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=9, color=S1,
                          label="DEA (CRS) — чизиқли дастурлаш"),
                   Line2D([], [], marker="o", ls="", ms=9, color=S2,
                          label="SFA — стохастик чегара")],
          loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK2)
sarlavha(ax, "Туманларнинг техник самарадорлиги: икки усул бўйича баҳо",
         f"{K['yillar'][0]}–{K['yillar'][1]} йй. ўртачаси · рейтинглар мослиги: "
         f"Спирмен ρ = {K['spearman_rho']:.2f} (p = {K['spearman_p']:.3f})")
fig.text(0.01, -0.02, MANBA, fontsize=8, color=MUTED)
saqla(fig, "06_dea_sfa_samaradorlik")

# ===========================================================================
# 7. Лоренц эгри чизиғи: сув -> маҳсулот
# ===========================================================================
kx = np.concatenate([[0], lor.kum_suv_.values if "kum_suv_" in lor
                     else lor["kum_suv_%"].values])
ky = np.concatenate([[0], lor["kum_yalpi_%"].values])
fig, ax = plt.subplots(figsize=(6.8, 6.4))
ax.plot([0, 100], [0, 100], color=BASE, lw=1.6, ls=(0, (5, 3)),
        label="мутлақ тенг тақсимот")
ax.fill_between(kx, ky, kx, color=S1, alpha=0.13, zorder=2)
ax.plot(kx, ky, color=S1, lw=2.2, marker="o", ms=5, mfc=S1, mec=SURFACE,
        mew=1.4, zorder=3, label="кузатилаётган тақсимот")
for _, r in lor.iterrows():
    if r["tuman"] in ("Олот", "Қоракўл", "Бухоро", "Ғиждувон"):
        ax.annotate(r["tuman"], (r["kum_suv_%"], r["kum_yalpi_%"]),
                    xytext=(7, -9), textcoords="offset points",
                    fontsize=8.8, color=INK2)
ax.set_xlabel("сув сарфининг кумулятив улуши, %")
ax.set_ylabel("ялпи маҳсулотнинг кумулятив улуши, %")
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.grid(True, alpha=0.9); ax.set_axisbelow(True)
ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK2)
ax.text(0.97, 0.06, "эгри чизиқ диагоналдан қанча узоқ бўлса,\n"
                    "сув шунча самарасиз тақсимланган",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        color=MUTED)
sarlavha(ax, "Сув билан даромад ўртасидаги номутаносиблик",
         "2024 йил · туманлар сув унумдорлиги бўйича саралаб чиқилган")
fig.text(0.01, -0.03, MANBA, fontsize=8, color=MUTED)
saqla(fig, "07_lorenz_egri_chizigi")

# ===========================================================================
# 8. Иссиқлик харитаси: туман × йил сув унумдорлиги (реал)
# ===========================================================================
piv = df.pivot_table(index="tuman", columns="yil", values="wp_real_som_m3")
piv = piv.loc[piv[2024].sort_values(ascending=False).index]
fig, ax = plt.subplots(figsize=(10.5, 5.6))
im = ax.imshow(piv.values, cmap=CMAP_BLUE, aspect="auto")
ax.set_xticks(range(len(piv.columns)))
ax.set_xticklabels(piv.columns, fontsize=9.5)
ax.set_yticks(range(len(piv.index)))
ax.set_yticklabels(piv.index, fontsize=10, color=INK)
ax.set_xticks(np.arange(-.5, len(piv.columns), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(piv.index), 1), minor=True)
ax.grid(which="minor", color=SURFACE, lw=2)
ax.tick_params(which="minor", length=0)
vmin, vmax = np.nanmin(piv.values), np.nanmax(piv.values)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        nv = (v - vmin) / (vmax - vmin)
        ax.text(j, i, f"{v:,.0f}", ha="center", va="center", fontsize=8,
                color="#ffffff" if nv > 0.55 else INK)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.025)
cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=8.5, color=MUTED)
cb.set_label("сўм/м³ (2018 нархида)", fontsize=9, color=INK2)
sarlavha(ax, "Сув унумдорлигининг туман ва йиллар кесимидаги динамикаси",
         "Инфляция таъсиридан тозаланган: 1 м³ сувга тўғри келадиган "
         "маҳсулот, 2018 йил солиштирма нархида")
fig.text(0.01, -0.04, MANBA, fontsize=8, color=MUTED)
saqla(fig, "08_issiqlik_xaritasi")

# ===========================================================================
# 9. Сценарийлар: ялпи маҳсулотнинг ўзгариши
# ===========================================================================
s = sen.iloc[1:].copy().iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 4.8))
for i, r in enumerate(s.itertuples()):
    v = getattr(r, "_4")   # "Ўзгариш, %"
    mlrd = getattr(r, "_5")
    rounded_hbar(ax, i, v, 0.6, DIV_POS if v >= 0 else DIV_NEG)
    ofs = 0.18 if v >= 0 else -0.18
    ax.text(v + ofs, i, f"{v:+.1f}%   {mlrd:+,.0f} млрд сўм", va="center",
            ha="left" if v >= 0 else "right", fontsize=10,
            color=INK, fontweight="600")
ax.axvline(0, color=BASE, lw=1.2, zorder=3)
ax.set_yticks(range(len(s)))
ax.set_yticklabels(s["Сценарий"], fontsize=10, color=INK)
lim = max(abs(s["Ўзгариш, %"])) * 2.75
ax.set_xlim(-lim, lim); ax.set_ylim(-0.7, len(s) - 0.3)
ax.set_xlabel("2024 йил базавий ҳолатига нисбатан ялпи маҳсулотнинг ўзгариши, %")
ax.xaxis.grid(True, alpha=0.9); ax.set_axisbelow(True); ax.yaxis.grid(False)
sarlavha(ax, "Сценарийлар: сув тежаш технологиялари камсувликни қоплай оладими?",
         f"Сув эластиклиги b = {K['suv_elastikligi']:.3f} асосида · ФИК — суғориш "
         f"тармоғининг фойдали иш коэффициенти")
fig.text(0.01, -0.06, MANBA, fontsize=8, color=MUTED)
saqla(fig, "09_senariylar")

# ===========================================================================
# 10. Сув баланси: Амударёдан далагача (2024)
# ===========================================================================
b = bal[bal.yil == 2024].iloc[0]
olindi = b.amudaryodan_mln_m3
magistral = b.magistral_yoqotish_mln_m3
tumanga = b.tumanlarga_mln_m3
dala = b.dalaga_yetgan_mln_m3
xojalik = tumanga - dala

bosqichlar = [
    ("Амударёдан\nолинган", olindi, 0, S1),
    ("Магистрал\nканалда\nйўқотилган", -magistral, olindi, DIV_NEG),
    ("Туманларга\nетказилган", tumanga, 0, S1),
    ("Хўжаликлараро\nва ички тармоқда\nйўқотилган", -xojalik, tumanga, DIV_NEG),
    ("Далага\nреал етган", dala, 0, S3),
]
fig, ax = plt.subplots(figsize=(9.8, 5.6))
for i, (nom, qiy, past, rang) in enumerate(bosqichlar):
    h = abs(qiy)
    y0 = past - h if qiy < 0 else 0
    ax.bar(i, h, bottom=y0, width=0.62, color=rang, zorder=3)
    ax.text(i, y0 + h + olindi * 0.018,
            f"{abs(qiy):,.0f}" + (f"\n({abs(qiy)/olindi*100:.1f}%)"),
            ha="center", va="bottom", fontsize=9.5, color=INK,
            fontweight="600" if qiy > 0 else "400")
for i in range(len(bosqichlar) - 1):
    _, q1, p1, _ = bosqichlar[i]
    top = (p1 if q1 < 0 else q1) if q1 > 0 else p1 - abs(q1)
    ax.plot([i + 0.31, i + 1 - 0.31], [top, top], color=BASE, lw=1,
            ls=(0, (3, 3)), zorder=1)
ax.set_xticks(range(len(bosqichlar)))
ax.set_xticklabels([b[0] for b in bosqichlar], fontsize=9, color=INK)
ax.set_ylabel("млн м³")
ax.set_ylim(0, olindi * 1.16)
ax.yaxis.grid(True, alpha=0.9); ax.set_axisbelow(True)
ax.text(0.99, 0.95, f"тизимнинг умумий ФИК = {b.umumiy_fik:.3f}\n"
                    f"умумий йўқотиш = {(1-b.umumiy_fik)*100:.1f}%",
        transform=ax.transAxes, ha="right", va="top", fontsize=10,
        color=INK, fontweight="600")
sarlavha(ax, "Сув баланси: Амударёдан далагача йўлда нима йўқолади",
         f"2024 йил · олинган ҳар 100 м³ сувнинг атиги "
         f"{K['umumiy_fik_2024']*100:.0f} м³ и экин илдизига етиб бормоқда")
fig.text(0.01, -0.06, MANBA, fontsize=8, color=MUTED)
saqla(fig, "10_suv_balansi")

print(f"\nБарча графиклар сақланди: {GRAF}")
