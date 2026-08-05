# -*- coding: utf-8 -*-
"""
01_malumot_yaratish.py
----------------------
Бухоро вилояти бўйича "Амударёдан олинган сув — тумандаги тақсимот —
қишлоқ хўжалиги даромади — сувдан фойдаланиш самарадорлиги" панель
маълумотлар базасини тузади (11 туман x 2018-2024 йй. = 77 кузатув).

МУҲИМ ИЗОҲ (методология):
  Рақамлар Аму-Бухоро машина канали (АБМК) тизими ва вилоят статистикаси
  бўйича ЭЪЛОН ҚИЛИНГАН ЙИҒМА кўрсаткичларга (жами сув олиш ~3.5-3.7 км3,
  суғориладиган майдон ~274 минг га, ялпи ўсимликчилик маҳсулоти) ЛАНГАР
  қилинган ва туманлар кесимида агрономик норматив (м3/га), тупроқ
  шўрланиши ҳамда канал бош/охирги қисми (head/tail) омиллари асосида
  КАЛИБРЛАНГАН. Ялпи маҳсулот Кобб-Дуглас ишлаб чиқариш функцияси
  генератори орқали ҳосил қилинган — шу боис эконометрик боғланишлар
  ички жиҳатдан изчил.

  Бу ИНДИКАТИВ база. Расмий рақамларингиз бўлса, шу устун номларини
  сақлаган ҳолда data/buxoro_suv_panel.csv файлини алмаштиринг —
  бошқа ҳеч нарсани ўзгартириш шарт эмас.
"""

import os
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RNG = np.random.default_rng(20240805)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

YILLAR = list(range(2014, 2025))
BAZA_YIL = 2014      # тренд бошланиши
LANGAR_YIL = 2018    # ялпи маҳсулот шкаласи лангарланадиган йил

# ---------------------------------------------------------------------------
# 1. Туманлар профили (2024 йил лангар қиймати)
# ---------------------------------------------------------------------------
# zona      : канал тизимидаги ўрни (bosh / orta / oxirgi)
# maydon    : суғориладиган майдон, минг га (2024)
# m3_ga     : йиллик сув олиш нормативи, м3/га (2024)
# shor      : тупроқ шўрланиш индекси (0 = шўрланмаган ... 1 = кучли)
# hosildor  : тупроқ/агротехника унумдорлик омили (A_i)
TUMANLAR = [
    # nomi,            zona,     maydon, m3_ga,  shor,  hosildor
    ("Бухоро",         "bosh",    23.5, 12400, 0.28, 1.06),
    ("Вобкент",        "bosh",    22.5, 12000, 0.24, 1.09),
    ("Ғиждувон",       "bosh",    31.5, 11800, 0.22, 1.12),
    ("Жондор",         "orta",    32.0, 13200, 0.36, 1.00),
    ("Когон",          "orta",    19.0, 12600, 0.33, 1.02),
    ("Олот",           "oxirgi",  27.5, 14600, 0.62, 0.86),
    ("Пешку",          "orta",    23.5, 12900, 0.31, 1.03),
    ("Ромитан",        "orta",    26.0, 12700, 0.30, 1.04),
    ("Шофиркон",       "bosh",    28.5, 12200, 0.26, 1.07),
    ("Қоракўл",        "oxirgi",  33.0, 14200, 0.58, 0.88),
    ("Қоровулбозор",   "oxirgi",   7.0, 13500, 0.55, 0.90),
]

# ---------------------------------------------------------------------------
# 2. Йиллик макро омиллар
# ---------------------------------------------------------------------------
# Амударё сувлилиги индекси (1.00 = ўртача сувли йил).
# 2021 — ҳавзада кескин камсувли йил, 2020 ҳам камсув.
SUV_INDEKS = {2014: 1.03, 2015: 0.98, 2016: 0.93, 2017: 0.99,
              2018: 0.96, 2019: 1.02, 2020: 0.94, 2021: 0.87, 2022: 0.97,
              2023: 1.00, 2024: 1.00}

# Қишлоқ хўжалиги маҳсулоти нархлари дефлятори (2018 = 100).
# 2017 йилги валюта либерализациясидан кейин нархлар кескин ошган.
DEFLYATOR = {2014: 44.0, 2015: 51.0, 2016: 59.0, 2017: 74.0,
             2018: 100.0, 2019: 115.2, 2020: 132.8, 2021: 152.4, 2022: 175.1,
             2023: 196.3, 2024: 213.9}

# Ўртача йиллик алмашув курси, сўм/АҚШ доллари
KURS = {2014: 2320, 2015: 2570, 2016: 2965, 2017: 5120,
        2018: 8340, 2019: 9500, 2020: 10480, 2021: 10840, 2022: 11220,
        2023: 12340, 2024: 12780}

# Суғориш тармоғи ФИК (фойдали иш коэффициенти) — кластер/сув тежовчи
# технологиялар ҳисобига йиллар давомида ўсиб боради
FIK_BAZA = {2014: 0.578, 2015: 0.586, 2016: 0.594, 2017: 0.604,
            2018: 0.615, 2019: 0.622, 2020: 0.630, 2021: 0.641, 2022: 0.652,
            2023: 0.664, 2024: 0.678}

# Суғориладиган майдоннинг йиллар бўйича индекси (шўрланиш ҳисобига
# айрим майдонлар чиқиб кетган, кластерлар ҳисобига қайта ўзлаштирилган)
MAYDON_INDEKS = {2014: 1.012, 2015: 1.010, 2016: 1.008, 2017: 1.006,
                 2018: 1.005, 2019: 1.003, 2020: 1.000, 2021: 0.994,
                 2022: 0.996, 2023: 0.999, 2024: 1.000}

# ---------------------------------------------------------------------------
# 3. Ишлаб чиқариш функцияси параметрлари (генератор DGP)
# ---------------------------------------------------------------------------
BETA_SUV = 0.32      # сув эластиклиги
BETA_MEHNAT = 0.20   # меҳнат эластиклиги
BETA_MAYDON = 0.30   # ер эластиклиги
BETA_KAPITAL = 0.15  # капитал эластиклиги
TFP_OSISH = 0.028    # йиллик умумий омилли унумдорлик ўсиши
SHOR_JAZO = 0.19     # шўрланишнинг ҳосилдорликка салбий таъсири
NOISE_SD = 0.035     # тасодифий (икки томонлама) шок v ~ N(0, sd)
# Техник самарасизлик u ~ N+(0, su) — суғоришни бошқариш сифати, сув
# истеъмолчилари уюшмаларининг фаоллиги, сув ҳисоби интизоми
SAMARASIZ_BAZA = 0.048   # барча туманлар учун базавий даража
SAMARASIZ_SHOR = 0.065   # шўрланиш ҳисобига қўшимча
SAMARASIZ_HISOB = 0.075  # сув ҳисоблагичлари билан қамров пастлиги ҳисобига
# Бошқарув сифати вақт бўйича БАРҚАРОР: туманнинг суғоришни ташкил этиш
# маданияти йилдан-йилга кескин ўзгармайди (доимий + ўткинчи компонент)
SAMARASIZ_DOIMIY = 0.85   # доимий (туманга хос) компонент оғирлиги
SAMARASIZ_OTKINCHI = 0.53  # ўткинчи компонент оғирлиги (0.85^2+0.53^2 ~ 1)

# 2018 йилдаги вилоят ялпи ўсимликчилик маҳсулоти (2018 нархида), млрд сўм
YALPI_2018_LANGAR = 5400.0

# ---------------------------------------------------------------------------
# 4. Панель базани йиғиш
# ---------------------------------------------------------------------------
qatorlar = []
for tid, (nom, zona, maydon24, m3ga24, shor, hosildor) in enumerate(TUMANLAR, start=1):
    # тумандаги меҳнат ва капитал зичлиги (га ҳисобига)
    mehnat_ga = 0.62 + 0.10 * RNG.standard_normal() * 0.3     # киши/га
    kapital_ga_baza = 4.4 * (0.9 + 0.2 * hosildor)   # млн сўм/га (2018 нархда), 2014 й.
    # ҳар бир туманнинг ўз инвестиция суръати (кластер/фермер хўжаликлари
    # инвестиция фаоллиги ҳар хил) ва меҳнат бозори тенденцияси
    inv_sur = 0.055 + 0.020 * RNG.standard_normal()           # йиллик капитал ўсиши
    mehnat_trend = -0.008 + 0.006 * RNG.standard_normal()     # аграр бандлик тренди
    kap_zaxira = 1.0                                          # кумулятив капитал индекси
    # Ер майдони тренди: шўрланган туманларда майдон қисқаради (ердан
    # чиқариш), канал бошидаги туманларда қўриқ ерлар ўзлаштирилади
    yer_trend = 0.005 - 0.020 * shor + 0.003 * RNG.standard_normal()
    # Коллектор-дренаж тармоғига инвестиция суръати — туманлар бўйича ҳар хил
    drenaj_sur = 0.013 + 0.011 * RNG.standard_normal()
    # Сув ҳисоблагичлари билан қамров: 2014 йилдаги базавий даража ва
    # йиллик ўсиш суръати (туманлар бўйича турлича жорий этилган)
    hisob_2014 = np.clip(28 + 22 * (1 - shor) + 6 * RNG.standard_normal(), 8, 62)
    hisob_sur = 4.4 + 1.6 * RNG.standard_normal()   # фоиз пункт/йил
    # Туманнинг доимий бошқарув сифати компоненти (бир марта тортилади)
    boshqaruv_doimiy = RNG.standard_normal()

    for yil in YILLAR:
        t = yil - BAZA_YIL       # тренд ўзгарувчиси (0 = 2014)
        t18 = yil - 2018         # 2018 йилга нисбатан марказлаштирилган

        # --- Ер: умумвилоят индекси x туманга хос тренд x тасодифий шок ---
        maydon = maydon24 * MAYDON_INDEKS[yil]                       # минг га
        maydon *= (1 + yer_trend) ** (yil - 2024)  # 2024 = лангар йил
        maydon *= np.exp(0.013 * RNG.standard_normal())

        # --- Сув: норматив x сувлилик индекси x зона омили ---
        # камсув йилларда канал охиридаги туманлар кўпроқ зарар кўради
        zona_zarar = {"bosh": 0.35, "orta": 0.70, "oxirgi": 1.25}[zona]
        kamsuvlik = (1 - SUV_INDEKS[yil]) * zona_zarar
        # идиосинкратик омиллар: канал таъмири, насос станцияси тўхташи,
        # ички лимит қайта тақсимланиши, юввиш сувига бўлган талаб
        m3ga = m3ga24 * (1 - kamsuvlik) * np.exp(0.055 * RNG.standard_normal())
        # ФИК ошиши ҳисобига солиштирма сув сарфи аста-секин камаяди
        m3ga *= (FIK_BAZA[2024] / FIK_BAZA[yil]) ** 0.55
        suv_mln_m3 = maydon * 1000 * m3ga / 1e6                      # млн м3

        # --- Меҳнат: аграр бандлик, миграция ва мавсумий талаб шоклари ---
        mehnat = (maydon * 1000 * mehnat_ga * (1 + mehnat_trend) ** t
                  * np.exp(0.070 * RNG.standard_normal()) / 1000)     # минг киши

        # --- Капитал: кумулятив инвестиция (ўзгарувчан суръат + шок) ---
        if t > 0:
            kap_zaxira *= (1 + inv_sur) * np.exp(0.075 * RNG.standard_normal())
        kapital = maydon * 1000 * kapital_ga_baza * kap_zaxira / 1000  # млрд сўм (2018 нархда)

        # --- Минерал ўғит ---
        ogit_kg_ga = (285 + 60 * (hosildor - 1) * 5) * (1 + 0.02 * t18) \
                     * (1 + 0.05 * RNG.standard_normal())

        # --- Экин майдони таркиби (улушлар) ---
        # Кластер ислоҳоти: пахта ва ғалла майдонлари қисқариб, боғ-узумзор
        # ҳамда сабзавот майдонлари кенгайиб бормоқда
        paxta = 0.34 - 0.018 * t18 + 0.02 * RNG.standard_normal()
        gala = 0.30 - 0.010 * t18 + 0.02 * RNG.standard_normal()
        bog_uzum = 0.11 + 0.009 * t18 + 0.01 * RNG.standard_normal()
        sabzavot = 1 - paxta - gala - bog_uzum

        # --- Шўрланиш: камсув йилларда кучаяди, дренаж ҳисобига камаяди ---
        shor_it = (shor * (1 - drenaj_sur) ** t
                   * (1 + 0.90 * (1 - SUV_INDEKS[yil]))
                   * np.exp(0.055 * RNG.standard_normal()))

        # --- Сув ҳисоблагичлари билан қамров, % ---
        hisoblagich = float(np.clip(hisob_2014 + hisob_sur * t
                                    + 2.5 * RNG.standard_normal(), 5, 99))

        # --- Техник самарасизлик u ~ N+(0, su): бир томонлама компонент ---
        su_i = (SAMARASIZ_BAZA
                + SAMARASIZ_SHOR * shor_it
                + SAMARASIZ_HISOB * (1 - hisoblagich / 100))
        u_it = abs(SAMARASIZ_DOIMIY * boshqaruv_doimiy
                   + SAMARASIZ_OTKINCHI * RNG.standard_normal()) * su_i

        # --- Ялпи маҳсулот (Кобб-Дуглас DGP, 2018 нархида) ---
        ln_y = (np.log(hosildor)
                + BETA_SUV * np.log(suv_mln_m3)
                + BETA_MEHNAT * np.log(mehnat)
                + BETA_MAYDON * np.log(maydon)
                + BETA_KAPITAL * np.log(kapital)
                + TFP_OSISH * t
                - SHOR_JAZO * shor_it
                + 0.25 * (bog_uzum + sabzavot - 0.45)   # юқори қийматли экинлар самараси
                + NOISE_SD * RNG.standard_normal()      # v: тасодифий шок
                - u_it)                                 # u: техник самарасизлик
        yalpi_real = np.exp(ln_y)   # шкаласи кейин калибрланади

        qatorlar.append(dict(
            tuman=nom, tuman_id=tid, zona=zona, yil=yil,
            suv_mln_m3=suv_mln_m3,
            maydon_ming_ga=maydon,
            mehnat_ming_kishi=mehnat,
            kapital_2018_mlrd=kapital,
            ogit_kg_ga=ogit_kg_ga,
            paxta_ulush=paxta, gala_ulush=gala,
            sabzavot_ulush=sabzavot, bog_uzum_ulush=bog_uzum,
            shorlanish_indeks=shor_it,
            shorlanish_bazaviy=shor,
            hisoblagich_qamrov=hisoblagich,
            kanal_fik=FIK_BAZA[yil] * (1 - 0.06 * (zona == "oxirgi")),
            deflyator=DEFLYATOR[yil],
            kurs_som_usd=KURS[yil],
            _yalpi_xom=yalpi_real,
        ))

df = pd.DataFrame(qatorlar)

# --- Ялпи маҳсулот шкаласини 2018 йил лангарига калибрлаш ---
skala = YALPI_2018_LANGAR / df.loc[df.yil == LANGAR_YIL, "_yalpi_xom"].sum()
df["yalpi_2018narx_mlrd"] = df["_yalpi_xom"] * skala
df["yalpi_joriy_mlrd"] = df["yalpi_2018narx_mlrd"] * df["deflyator"] / 100.0
df = df.drop(columns=["_yalpi_xom"])

# --- Яхлитлаш (статистика тўпламларидаги аниқлик даражасигача) ---
yaxlit = {
    "suv_mln_m3": 1, "maydon_ming_ga": 2, "mehnat_ming_kishi": 2,
    "kapital_2018_mlrd": 1, "ogit_kg_ga": 0,
    "paxta_ulush": 3, "gala_ulush": 3, "sabzavot_ulush": 3, "bog_uzum_ulush": 3,
    "kanal_fik": 3, "yalpi_2018narx_mlrd": 1, "yalpi_joriy_mlrd": 1,
    "shorlanish_indeks": 3, "shorlanish_bazaviy": 2, "hisoblagich_qamrov": 1,
}
for k, v in yaxlit.items():
    df[k] = df[k].round(v)

df = df.sort_values(["tuman_id", "yil"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 5. Вилоят даражасидаги сув баланси (Амударё -> АБМК -> туманлар)
# ---------------------------------------------------------------------------
# АБМК бош иншоотидаги олиш = туманларга етказилган сув / (тизим ФИК)
balans = (df.groupby("yil")
            .agg(tumanlarga_mln_m3=("suv_mln_m3", "sum"),
                 maydon_ming_ga=("maydon_ming_ga", "sum"))
            .reset_index())
TRANSPORT_FIK = {2014: 0.826, 2015: 0.830, 2016: 0.834, 2017: 0.839,
                 2018: 0.845, 2019: 0.848, 2020: 0.852, 2021: 0.856,
                 2022: 0.861, 2023: 0.866, 2024: 0.872}   # магистрал каналдаги ФИК
balans["transport_fik"] = balans["yil"].map(TRANSPORT_FIK)
balans["amudaryodan_mln_m3"] = balans["tumanlarga_mln_m3"] / balans["transport_fik"]
balans["magistral_yoqotish_mln_m3"] = balans["amudaryodan_mln_m3"] - balans["tumanlarga_mln_m3"]
balans["dala_fik"] = df.groupby("yil")["kanal_fik"].mean().values
balans["dalaga_yetgan_mln_m3"] = balans["tumanlarga_mln_m3"] * balans["dala_fik"]
balans["umumiy_fik"] = balans["dalaga_yetgan_mln_m3"] / balans["amudaryodan_mln_m3"]
balans["yalpi_joriy_mlrd"] = df.groupby("yil")["yalpi_joriy_mlrd"].sum().values
balans["yalpi_2018narx_mlrd"] = df.groupby("yil")["yalpi_2018narx_mlrd"].sum().values
balans["kurs_som_usd"] = balans["yil"].map(KURS)
balans = balans.round(3)

# ---------------------------------------------------------------------------
# 6. Сақлаш
# ---------------------------------------------------------------------------
csv_yol = os.path.join(DATA, "buxoro_suv_panel.csv")
df.to_csv(csv_yol, index=False, encoding="utf-8-sig")

bal_yol = os.path.join(DATA, "buxoro_suv_balans.csv")
balans.to_csv(bal_yol, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(os.path.join(DATA, "buxoro_suv_baza.xlsx"), engine="openpyxl") as xl:
    df.to_excel(xl, sheet_name="panel_2018_2024", index=False)
    balans.to_excel(xl, sheet_name="viloyat_suv_balansi", index=False)

print("Панель база яратилди:", df.shape[0], "кузатув,", df.shape[1], "ўзгарувчи")
print("Файллар:")
print("  ", csv_yol)
print("  ", bal_yol)
print("  ", os.path.join(DATA, "buxoro_suv_baza.xlsx"))
print()
print("2024 йил якуни:")
s24 = df[df.yil == 2024]
print("  Туманларга етказилган сув : {:,.0f} млн м3".format(s24.suv_mln_m3.sum()))
print("  Амударёдан олинган сув    : {:,.0f} млн м3".format(
    balans.loc[balans.yil == 2024, "amudaryodan_mln_m3"].iat[0]))
print("  Суғориладиган майдон      : {:,.1f} минг га".format(s24.maydon_ming_ga.sum()))
print("  Ялпи маҳсулот (жорий нарх): {:,.0f} млрд сўм".format(s24.yalpi_joriy_mlrd.sum()))
print("  Сув унумдорлиги           : {:,.0f} сўм/м3".format(
    s24.yalpi_joriy_mlrd.sum() * 1e9 / (s24.suv_mln_m3.sum() * 1e6)))
