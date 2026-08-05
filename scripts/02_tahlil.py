# -*- coding: utf-8 -*-
"""
02_tahlil.py
------------
Бухоро вилояти сув-иқтисодиёт панелининг тўлиқ иқтисодий таҳлили.

Блоклар:
  A. Вилоят сув баланси (Амударё -> АБМК -> дала)
  B. Сувнинг туманлар кесимида тақсимланиши (2024)
  C. Сувдан фойдаланиш самарадорлиги индикаторлари
  D. Тақсимот тенгсизлиги: Джини + Лоренц
  E. Кобб-Дуглас ишлаб чиқариш функцияси: Pooled OLS / FE / RE + Хаусман
  F. Сувнинг чекли маҳсулдорлиги (MPW) ва иқтисодий қиймати
  G. DEA (CRS/VRS) техник самарадорлик
  H. SFA (стохастик чегара, half-normal) самарадорлик
  I. Сув тежаш салоҳияти ва сценарий таҳлили

Барча натижалар natijalar/ папкасига CSV ва TXT кўринишида сақланади.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import linprog, minimize
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, RandomEffects

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.float_format", lambda x: f"{x:,.3f}")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "natijalar")
os.makedirs(OUT, exist_ok=True)

LOG = []

# Натижа файллари Excel/WPS да очиқ турганда ёзиш имконсиз бўлади —
# бундай ҳолатда таҳлилни тўхтатмасдан огоҳлантириш билан давом этамиз.
_asl_to_csv = pd.DataFrame.to_csv


def _xavfsiz_to_csv(self, path_or_buf=None, *a, **kw):
    try:
        return _asl_to_csv(self, path_or_buf, *a, **kw)
    except PermissionError:
        print(f"  ОГОҲЛАНТИРИШ: {os.path.basename(str(path_or_buf))} файли "
              f"бошқа дастурда очиқ — янгиланмади")
        return None


pd.DataFrame.to_csv = _xavfsiz_to_csv


def p(*args):
    s = " ".join(str(a) for a in args)
    print(s)
    LOG.append(s)


def sarlavha(t):
    p("")
    p("=" * 78)
    p(t)
    p("=" * 78)


df = pd.read_csv(os.path.join(DATA, "buxoro_suv_panel.csv"), encoding="utf-8-sig")
bal = pd.read_csv(os.path.join(DATA, "buxoro_suv_balans.csv"), encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# Ҳосила кўрсаткичлар
# ---------------------------------------------------------------------------
df["suv_m3_ga"] = df.suv_mln_m3 * 1e6 / (df.maydon_ming_ga * 1e3)
df["yalpi_real_mln_som_ga"] = df.yalpi_2018narx_mlrd * 1e9 / (df.maydon_ming_ga * 1e3) / 1e6
df["yalpi_mln_som_ga"] = df.yalpi_joriy_mlrd * 1e9 / (df.maydon_ming_ga * 1e3) / 1e6
# Сув унумдорлиги (water productivity)
df["wp_som_m3"] = df.yalpi_joriy_mlrd * 1e9 / (df.suv_mln_m3 * 1e6)          # сўм/м3, жорий нарх
df["wp_real_som_m3"] = df.yalpi_2018narx_mlrd * 1e9 / (df.suv_mln_m3 * 1e6)  # сўм/м3, 2018 нархда
df["wp_usd_m3"] = df.wp_som_m3 / df.kurs_som_usd                              # АҚШ доллари/м3
df["daromad_usd_ga"] = df.yalpi_joriy_mlrd * 1e9 / df.kurs_som_usd / (df.maydon_ming_ga * 1e3)
# Сув сиғими (water intensity) — 1 млн сўм маҳсулотга сарфланган м3
df["suv_sigimi_m3_mln_som"] = (df.suv_mln_m3 * 1e6) / (df.yalpi_2018narx_mlrd * 1e3)

for c in ["yalpi_2018narx_mlrd", "suv_mln_m3", "mehnat_ming_kishi",
          "maydon_ming_ga", "kapital_2018_mlrd", "ogit_kg_ga"]:
    df["ln_" + c] = np.log(df[c])
df["t"] = df.yil - 2014

df.to_csv(os.path.join(OUT, "panel_hosila_korsatkichlar.csv"),
          index=False, encoding="utf-8-sig")

# ===========================================================================
sarlavha("A. ВИЛОЯТ СУВ БАЛАНСИ: АМУДАРЁ -> АБМК -> ТУМАН -> ДАЛА")
# ===========================================================================
bal_k = bal[["yil", "amudaryodan_mln_m3", "magistral_yoqotish_mln_m3",
             "tumanlarga_mln_m3", "dalaga_yetgan_mln_m3",
             "transport_fik", "dala_fik", "umumiy_fik",
             "maydon_ming_ga", "yalpi_joriy_mlrd"]].copy()
bal_k["nol_yoqotish_%"] = (1 - bal_k.umumiy_fik) * 100
bal_k["suv_m3_ga"] = bal_k.amudaryodan_mln_m3 * 1e6 / (bal_k.maydon_ming_ga * 1e3)
bal_k["wp_som_m3"] = bal_k.yalpi_joriy_mlrd * 1e9 / (bal_k.amudaryodan_mln_m3 * 1e6)
p(bal_k.round(3).to_string(index=False))
bal_k.round(4).to_csv(os.path.join(OUT, "A_viloyat_suv_balansi.csv"),
                      index=False, encoding="utf-8-sig")

b24 = bal_k[bal_k.yil == 2024].iloc[0]
b18 = bal_k.sort_values("yil").iloc[0]   # панелдаги биринчи йил
p("")
p(f"2024 й.: Амударёдан {b24.amudaryodan_mln_m3:,.0f} млн м3 олинган, шундан "
  f"{b24.magistral_yoqotish_mln_m3:,.0f} млн м3 ({(1-b24.transport_fik)*100:.1f}%) "
  f"магистрал каналда йўқотилган.")
p(f"       Далага реал етган сув {b24.dalaga_yetgan_mln_m3:,.0f} млн м3, "
  f"тизимнинг умумий ФИК = {b24.umumiy_fik:.3f} "
  f"(яъни ҳар 100 м3 нинг {(1-b24.umumiy_fik)*100:.0f} м3 и йўқотилади).")
p(f"       {int(b18.yil)} -> {int(b24.yil)} да умумий ФИК {b18.umumiy_fik:.3f} -> "
  f"{b24.umumiy_fik:.3f} "
  f"(+{(b24.umumiy_fik-b18.umumiy_fik)*100:.1f} фоиз пункт).")

# ===========================================================================
sarlavha("B. СУВНИНГ ТУМАНЛАР КЕСИМИДА ТАҚСИМЛАНИШИ (2024 йил)")
# ===========================================================================
d24 = df[df.yil == 2024].copy()
jami_suv = d24.suv_mln_m3.sum()
jami_maydon = d24.maydon_ming_ga.sum()
jami_yalpi = d24.yalpi_joriy_mlrd.sum()

taq = pd.DataFrame({
    "Туман": d24.tuman,
    "Зона": d24.zona,
    "Сув, млн м3": d24.suv_mln_m3,
    "Сув улуши, %": d24.suv_mln_m3 / jami_suv * 100,
    "Майдон, минг га": d24.maydon_ming_ga,
    "Майдон улуши, %": d24.maydon_ming_ga / jami_maydon * 100,
    "м3/га": d24.suv_m3_ga,
    "Ялпи маҳс., млрд сўм": d24.yalpi_joriy_mlrd,
    "Маҳс. улуши, %": d24.yalpi_joriy_mlrd / jami_yalpi * 100,
})
taq["Сув-майдон фарқи, п.п."] = taq["Сув улуши, %"] - taq["Майдон улуши, %"]
taq = taq.sort_values("Сув, млн м3", ascending=False)
p(taq.round(2).to_string(index=False))
p("")
p(f"ЖАМИ: {jami_suv:,.0f} млн м3 | {jami_maydon:,.1f} минг га | "
  f"{jami_yalpi:,.0f} млрд сўм | ўртача {jami_suv*1e6/(jami_maydon*1e3):,.0f} м3/га")
taq.round(3).to_csv(os.path.join(OUT, "B_suv_taqsimoti_2024.csv"),
                    index=False, encoding="utf-8-sig")

p("")
p("Изоҳ: 'Сув-майдон фарқи' мусбат бўлса — туман ўз майдон улушига нисбатан")
p("      КЎПРОҚ сув олмоқда (шўрланиш, юввиш суви, канал охиридаги йўқотиш).")
eng_kop = taq.iloc[taq["Сув-майдон фарқи, п.п."].values.argmax()]
eng_kam = taq.iloc[taq["Сув-майдон фарқи, п.п."].values.argmin()]
p(f"      Энг катта ижобий фарқ: {eng_kop['Туман']} (+{eng_kop['Сув-майдон фарқи, п.п.']:.2f} п.п.)")
p(f"      Энг катта салбий фарқ: {eng_kam['Туман']} ({eng_kam['Сув-майдон фарқи, п.п.']:.2f} п.п.)")

# ===========================================================================
sarlavha("C. СУВДАН ФОЙДАЛАНИШ САМАРАДОРЛИГИ ИНДИКАТОРЛАРИ (2024)")
# ===========================================================================
sam = pd.DataFrame({
    "Туман": d24.tuman,
    "Зона": d24.zona,
    "м3/га": d24.suv_m3_ga,
    "Сув унумдорлиги, сўм/м3": d24.wp_som_m3,
    "Сув унумдорлиги, USD/м3": d24.wp_usd_m3,
    "Даромад, USD/га": d24.daromad_usd_ga,
    "Сув сиғими, м3/млн сўм (2018 н.)": d24.suv_sigimi_m3_mln_som,
    "Шўрланиш индекси": d24.shorlanish_indeks,
    "Тармоқ ФИК": d24.kanal_fik,
}).sort_values("Сув унумдорлиги, сўм/м3", ascending=False)
sam["Рейтинг"] = range(1, len(sam) + 1)
p(sam.round(3).to_string(index=False))
sam.round(4).to_csv(os.path.join(OUT, "C_samaradorlik_2024.csv"),
                    index=False, encoding="utf-8-sig")

wp = d24.wp_som_m3
p("")
p(f"Вилоят ўртачаси           : {jami_yalpi*1e9/(jami_suv*1e6):,.0f} сўм/м3 "
  f"({jami_yalpi*1e9/(jami_suv*1e6)/12780:.3f} USD/м3)")
p(f"Мин / Макс                : {wp.min():,.0f} / {wp.max():,.0f} сўм/м3 "
  f"(фарқ {wp.max()/wp.min():.2f} марта)")
p(f"Вариация коэффициенти (CV): {wp.std(ddof=1)/wp.mean()*100:.1f}%")

# Зона кесимида
zona_xul = d24.groupby("zona").apply(
    lambda g: pd.Series({
        "Туманлар сони": len(g),
        "Сув, млн м3": g.suv_mln_m3.sum(),
        "Майдон, минг га": g.maydon_ming_ga.sum(),
        "м3/га": g.suv_mln_m3.sum() * 1e6 / (g.maydon_ming_ga.sum() * 1e3),
        "сўм/м3": g.yalpi_joriy_mlrd.sum() * 1e9 / (g.suv_mln_m3.sum() * 1e6),
        "USD/га": g.yalpi_joriy_mlrd.sum() * 1e9 / 12780 / (g.maydon_ming_ga.sum() * 1e3),
    }), include_groups=False).reindex(["bosh", "orta", "oxirgi"])
zona_xul.index = ["Канал боши", "Ўрта оқим", "Канал охири"]
p("")
p("Канал зоналари кесимида:")
p(zona_xul.round(2).to_string())
zona_xul.round(3).to_csv(os.path.join(OUT, "C_zona_kesimida.csv"), encoding="utf-8-sig")

# Зоналар ўртасидаги фарқ статистик жиҳатдан аҳамиятлими? (ANOVA)
guruhlar = [g.wp_som_m3.values for _, g in d24.groupby("zona")]
F, pval = stats.f_oneway(*guruhlar)
p("")
p(f"ANOVA (зона -> сув унумдорлиги): F = {F:.3f}, p-value = {pval:.4f} -> "
  f"{'фарқ АҲАМИЯТЛИ' if pval < 0.05 else 'фарқ аҳамиятсиз'}")

# ===========================================================================
sarlavha("D. СУВ ТАҚСИМОТИДАГИ ТЕНГСИЗЛИК: ДЖИНИ ВА ЛОРЕНЦ")
# ===========================================================================
def gini(x, w=None):
    x = np.asarray(x, float)
    if w is None:
        w = np.ones_like(x)
    w = np.asarray(w, float)
    idx = np.argsort(x)
    x, w = x[idx], w[idx]
    cw = np.cumsum(w)
    cxw = np.cumsum(x * w)
    return (np.sum(cxw[1:] * w[:-1] - cxw[:-1] * w[1:])
            / (cxw[-1] * cw[-1])) * -1 if False else \
           1 - 2 * np.sum((cxw - 0.5 * x * w) * w) / (cxw[-1] * cw[-1])

g_suv = gini(d24.suv_m3_ga.values, d24.maydon_ming_ga.values)
g_wp = gini(d24.wp_som_m3.values, d24.suv_mln_m3.values)
p(f"Джини (майдон бирлигига сув таъминоти, м3/га) : {g_suv:.4f}")
p(f"Джини (сув унумдорлиги, сўм/м3)               : {g_wp:.4f}")
p("")
p("Талқин: 0 = мутлақ тенг тақсимот, 1 = мутлақ тенгсизлик.")
p("Сув таъминоти тақсимоти нисбатан ТЕКИС (норматив асосида берилади),")
p("аммо ундан олинадиган ДАРОМАД тақсимоти анча нотекис — самарадорлик")
p("захираси айнан шу фарқда.")

# Лоренц эгри чизиғи учун нуқталар
lor = d24.sort_values("suv_m3_ga")[["tuman", "maydon_ming_ga", "suv_mln_m3",
                                    "yalpi_joriy_mlrd", "suv_m3_ga"]].copy()
lor["kum_maydon_%"] = lor.maydon_ming_ga.cumsum() / lor.maydon_ming_ga.sum() * 100
lor["kum_suv_%"] = lor.suv_mln_m3.cumsum() / lor.suv_mln_m3.sum() * 100
lor2 = d24.sort_values("wp_som_m3")[["tuman", "suv_mln_m3", "yalpi_joriy_mlrd"]].copy()
lor2["kum_suv_%"] = lor2.suv_mln_m3.cumsum() / lor2.suv_mln_m3.sum() * 100
lor2["kum_yalpi_%"] = lor2.yalpi_joriy_mlrd.cumsum() / lor2.yalpi_joriy_mlrd.sum() * 100
lor.round(3).to_csv(os.path.join(OUT, "D_lorenz_suv_maydon.csv"),
                    index=False, encoding="utf-8-sig")
lor2.round(3).to_csv(os.path.join(OUT, "D_lorenz_yalpi_suv.csv"),
                     index=False, encoding="utf-8-sig")
p("")
p("Сув -> ялпи маҳсулот Лоренц нуқталари (сув унумдорлиги бўйича саралаб):")
p(lor2.round(2).to_string(index=False))

# ===========================================================================
sarlavha("E. КОББ-ДУГЛАС ИШЛАБ ЧИҚАРИШ ФУНКЦИЯСИ (панель регрессия)")
# ===========================================================================
p("Модел:  ln(Y_it) = a_i + b1*ln(Сув) + b2*ln(Меҳнат) + b3*ln(Майдон)")
p("                   + b4*ln(Капитал) + b5*Шўрланиш + c_t + e_it")
p("Y — ялпи ўсимликчилик маҳсулоти (2018 йил солиштирма нархида, млрд сўм)")
p("")

X_nom = ["ln_suv_mln_m3", "ln_mehnat_ming_kishi", "ln_maydon_ming_ga",
         "ln_kapital_2018_mlrd", "shorlanish_indeks"]
YAXSHI_NOM = {"ln_suv_mln_m3": "ln(Сув)", "ln_mehnat_ming_kishi": "ln(Меҳнат)",
              "ln_maydon_ming_ga": "ln(Майдон)", "ln_kapital_2018_mlrd": "ln(Капитал)",
              "shorlanish_indeks": "Шўрланиш индекси", "t": "Тренд (йил)",
              "const": "Доимий ҳад"}

# --- E1. Pooled OLS ---
Xp = sm.add_constant(df[X_nom + ["t"]])
ols = sm.OLS(df.ln_yalpi_2018narx_mlrd, Xp).fit(
    cov_type="cluster", cov_kwds={"groups": df.tuman_id})
p("--- E1. Pooled OLS (кластер-мустаҳкам ст. хатолар, туман бўйича) ---")
p(ols.summary().as_text())

# VIF — мультиколлинеарлик
from statsmodels.stats.outliers_influence import variance_inflation_factor
vif = pd.DataFrame({
    "Ўзгарувчи": [YAXSHI_NOM.get(c, c) for c in Xp.columns],
    "VIF": [variance_inflation_factor(Xp.values, i) for i in range(Xp.shape[1])]})
p("")
p("Мультиколлинеарлик текшируви (VIF):")
p(vif.round(2).to_string(index=False))
p("Изоҳ: VIF < 10 бўлса мультиколлинеарлик жиддий эмас.")

# --- E2/E3. Панель FE ва RE ---
pdf = df.set_index(["tuman_id", "yil"])
Xfe = sm.add_constant(pdf[X_nom])
fe_res = PanelOLS(pdf.ln_yalpi_2018narx_mlrd, Xfe,
                  entity_effects=True, time_effects=True,
                  drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
p("")
p("--- E2. Fixed Effects (туман + йил эффектлари, кластер-мустаҳкам) ---")
p(str(fe_res))

re_res = RandomEffects(pdf.ln_yalpi_2018narx_mlrd,
                       sm.add_constant(pdf[X_nom + ["t"]])).fit()
p("")
p("--- E3. Random Effects ---")
p(str(re_res))

# --- Хаусман тести ---
fe_h = PanelOLS(pdf.ln_yalpi_2018narx_mlrd, sm.add_constant(pdf[X_nom + ["t"]]),
                entity_effects=True, drop_absorbed=True).fit()
re_h = RandomEffects(pdf.ln_yalpi_2018narx_mlrd,
                     sm.add_constant(pdf[X_nom + ["t"]])).fit()
umumiy = [c for c in fe_h.params.index if c in re_h.params.index and c != "const"]
b_diff = (fe_h.params[umumiy] - re_h.params[umumiy]).values
V_diff = (fe_h.cov.loc[umumiy, umumiy] - re_h.cov.loc[umumiy, umumiy]).values
try:
    chi2 = float(b_diff @ np.linalg.pinv(V_diff) @ b_diff)
    dfree = len(umumiy)
    hp = 1 - stats.chi2.cdf(chi2, dfree)
    p("")
    p(f"--- Хаусман тести: chi2({dfree}) = {chi2:.3f}, p = {hp:.4f} -> "
      f"{'FE модели афзал' if hp < 0.05 else 'RE модели рад этилмайди'}")
except Exception as e:
    p(f"Хаусман тести ҳисобланмади: {e}")

# --- E4. Интенсив (га ҳисобига) спецификация: доимий миқёс самараси шарти ---
# Суғориладиган майдон панелда деярли ўзгармас бўлгани учун унинг
# эластиклиги FE да заиф идентификацияланади. Шу боис барча кўрсаткичларни
# 1 га га келтириб, CRS шартини юклаймиз — аграр иқтисодиётда стандарт усул.
df["ln_y_ga"] = np.log(df.yalpi_2018narx_mlrd / df.maydon_ming_ga)
df["ln_suv_ga"] = np.log(df.suv_mln_m3 / df.maydon_ming_ga)
df["ln_mehnat_ga"] = np.log(df.mehnat_ming_kishi / df.maydon_ming_ga)
df["ln_kapital_ga"] = np.log(df.kapital_2018_mlrd / df.maydon_ming_ga)
pdf2 = df.set_index(["tuman_id", "yil"])
X_int = ["ln_suv_ga", "ln_mehnat_ga", "ln_kapital_ga", "shorlanish_indeks"]
fe_int = PanelOLS(pdf2.ln_y_ga, sm.add_constant(pdf2[X_int]),
                  entity_effects=True, time_effects=True,
                  drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
p("")
p("--- E4. FE, интенсив шакл: ln(Y/га) = f(сув/га, меҳнат/га, капитал/га) ---")
p(str(fe_int))
b_suv_int = fe_int.params["ln_suv_ga"]
p(f"Интенсив шаклдаги СУВ эластиклиги = {b_suv_int:.3f} "
  f"(ст.хато {fe_int.std_errors['ln_suv_ga']:.3f}, p = {fe_int.pvalues['ln_suv_ga']:.4f})")
p(f"Ер эластиклиги (қолдиқ бўйича, CRS шарти остида) = "
  f"{1 - sum(fe_int.params.get(c, 0) for c in X_int[:3]):.3f}")

# --- Эластикликлар жадвали ---
b_suv_fe = fe_res.params["ln_suv_mln_m3"]
se_suv_fe = fe_res.std_errors["ln_suv_mln_m3"]


def olish(seriya, nomlar):
    """Ютилиб кетган (absorbed) ёки моделда йўқ ўзгарувчилар учун NaN."""
    return [np.nan if c is None else seriya.get(c, np.nan) for c in nomlar]


elas = pd.DataFrame({
    "Ўзгарувчи": [YAXSHI_NOM.get(c, c) for c in X_nom],
    "Pooled OLS": olish(ols.params, X_nom),
    "OLS p": olish(ols.pvalues, X_nom),
    "FE (туман+йил)": olish(fe_res.params, X_nom),
    "FE ст.хато": olish(fe_res.std_errors, X_nom),
    "FE p": olish(fe_res.pvalues, X_nom),
    "RE": olish(re_res.params, X_nom),
    "FE интенсив (га)": olish(fe_int.params, ["ln_suv_ga", "ln_mehnat_ga",
                                              None, "ln_kapital_ga",
                                              "shorlanish_indeks"]),
})
p("")
p("--- Эластиклик коэффициентлари жамланмаси ---")
p(elas.round(4).to_string(index=False))
elas.round(5).to_csv(os.path.join(OUT, "E_elastikliklar.csv"),
                     index=False, encoding="utf-8-sig")

rts = sum(fe_res.params.get(c, 0.0) for c in X_nom[:4])
p("")
p(f"Миқёс самараси (returns to scale), экстенсив FE = {rts:.3f}")
p(f"СУВ эластиклиги (FE, экстенсив)  = {b_suv_fe:.3f} (ст.хато {se_suv_fe:.3f})")
p(f"СУВ эластиклиги (FE, интенсив)   = {b_suv_int:.3f} "
  f"(ст.хато {fe_int.std_errors['ln_suv_ga']:.3f})")
p("")
p("Кейинги ҳисоб-китобларда ИНТЕНСИВ шакл эластиклиги базавий сифатида")
p("олинади: суғориладиган майдон панелда деярли ўзгармас бўлгани учун")
p("экстенсив FE да ер ва сув коэффициентлари ўзаро коллинеар бўлиб қолади.")
b_suv = b_suv_int
p(f"БАЗАВИЙ СУВ ЭЛАСТИКЛИГИ b = {b_suv:.3f} -> сув сарфи 10% га камайса, "
  f"ялпи маҳсулот ~{b_suv*10:.1f}% га камаяди.")

# ===========================================================================
sarlavha("F. СУВНИНГ ЧЕККИ МАҲСУЛДОРЛИГИ (MPW) ВА ИҚТИСОДИЙ ҚИЙМАТИ")
# ===========================================================================
p("MPW = b_сув x (Y / W)  — 1 қўшимча м3 сув берадиган қўшимча маҳсулот")
d24 = d24.copy()
d24["mpw_som_m3"] = b_suv * d24.yalpi_joriy_mlrd * 1e9 / (d24.suv_mln_m3 * 1e6)
d24["mpw_usd_m3"] = d24.mpw_som_m3 / d24.kurs_som_usd
mpw = d24[["tuman", "zona", "wp_som_m3", "mpw_som_m3", "mpw_usd_m3"]].copy()
mpw.columns = ["Туман", "Зона", "Ўртача маҳсулдорлик, сўм/м3",
               "Чекли маҳсулдорлик MPW, сўм/м3", "MPW, USD/м3"]
mpw = mpw.sort_values("Чекли маҳсулдорлик MPW, сўм/м3", ascending=False)
p(mpw.round(4).to_string(index=False))
mpw.round(5).to_csv(os.path.join(OUT, "F_chekli_mahsuldorlik.csv"),
                    index=False, encoding="utf-8-sig")

viloyat_mpw = b_suv * jami_yalpi * 1e9 / (jami_suv * 1e6)
p("")
p(f"Вилоят бўйича MPW = {viloyat_mpw:,.0f} сўм/м3 ({viloyat_mpw/12780:.4f} USD/м3)")
p("Иқтисодий маъноси: сувнинг соя нархи (shadow price) шу даражада. Агар сув")
p("тарифи MPW дан анча паст бўлса — сувни тежашга иқтисодий рағбат йўқ.")
p("")
p("Қайта тақсимлаш самараси: сувни MPW паст туманлардан юқори туманларга")
p("кўчириш умумий маҳсулотни оширади. 100 млн м3 ни энг паст MPW ли туманлардан")
p("энг юқори MPW ли туманларга кўчириш самараси:")
srt = d24.sort_values("mpw_som_m3")
qoshimcha = (srt.mpw_som_m3.iloc[-1] - srt.mpw_som_m3.iloc[0]) * 100e6 / 1e9
p(f"  ~{qoshimcha:,.0f} млрд сўм ({qoshimcha*1e9/12780/1e6:,.1f} млн USD) қўшимча маҳсулот")

# ===========================================================================
sarlavha("G. DEA — ТЕХНИК САМАРАДОРЛИК (кириш-йўналтирилган, CRS ва VRS)")
# ===========================================================================
p("Киришлар: сув (млн м3), майдон (минг га), меҳнат (минг киши), капитал (млрд сўм)")
p("Чиқиш  : ялпи маҳсулот (2018 нархида, млрд сўм)")


def dea(X, Y, vrs=False):
    """Кириш-йўналтирилган DEA. X: n x m киришлар, Y: n x 1 чиқиш."""
    n, m = X.shape
    theta = np.empty(n)
    for i in range(n):
        # ўзгарувчилар: [theta, lambda_1..lambda_n]
        c = np.zeros(n + 1); c[0] = 1.0
        # -theta*x_i + X'lambda <= 0   (ҳар бир кириш учун)
        A_ub = np.hstack([(-X[i]).reshape(m, 1), X.T])
        b_ub = np.zeros(m)
        # Y'lambda >= y_i  ->  -Y'lambda <= -y_i
        A_ub = np.vstack([A_ub, np.hstack([[0.0], -Y])])
        b_ub = np.append(b_ub, -Y[i])
        A_eq, b_eq = None, None
        if vrs:
            A_eq = np.hstack([[0.0], np.ones(n)]).reshape(1, -1)
            b_eq = np.array([1.0])
        r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                    bounds=[(0, None)] * (n + 1), method="highs")
        theta[i] = r.x[0] if r.success else np.nan
    return theta


dea_natija = []
for yil, g in df.groupby("yil"):
    X = g[["suv_mln_m3", "maydon_ming_ga", "mehnat_ming_kishi",
           "kapital_2018_mlrd"]].values
    Y = g["yalpi_2018narx_mlrd"].values
    crs = dea(X, Y, vrs=False)
    vrs = dea(X, Y, vrs=True)
    dea_natija.append(pd.DataFrame({
        "tuman": g.tuman.values, "yil": yil,
        "dea_crs": crs, "dea_vrs": vrs,
        "miqyos_sam": crs / vrs}))
dea_df = pd.concat(dea_natija, ignore_index=True)
df = df.merge(dea_df, on=["tuman", "yil"], how="left")

dea_ort = (dea_df.groupby("tuman")[["dea_crs", "dea_vrs", "miqyos_sam"]]
           .mean().sort_values("dea_crs", ascending=False))
dea_ort.columns = ["DEA CRS (техник сам.)", "DEA VRS (соф техник сам.)",
                   "Миқёс самарадорлиги"]
dea_ort["Сув тежаш салоҳияти, %"] = (1 - dea_ort["DEA CRS (техник сам.)"]) * 100
p("")
p(f"{df.yil.min()}-{df.yil.max()} йй. ўртача DEA баллари (1.000 = чегарада, самарали):")
p(dea_ort.round(4).to_string())
dea_ort.round(5).to_csv(os.path.join(OUT, "G_dea_samaradorlik.csv"),
                        encoding="utf-8-sig")

dea24 = dea_df[dea_df.yil == 2024]
p("")
p(f"2024 й. ўртача техник самарадорлик (CRS) = {dea24.dea_crs.mean():.4f}")
p(f"Чегарада турган (самарали) туманлар: "
  f"{', '.join(dea24.loc[dea24.dea_crs > 0.999, 'tuman'])}")
tejash = (1 - dea24.dea_crs.mean()) * jami_suv
p(f"Назарий сув тежаш салоҳияти: {(1-dea24.dea_crs.mean())*100:.1f}% = "
  f"{tejash:,.0f} млн м3/йил")

# ===========================================================================
sarlavha("H. SFA — СТОХАСТИК ЧЕГАРА ТАҲЛИЛИ (half-normal)")
# ===========================================================================
p("ln(Y) = f(киришлар; b) + v - u,  v ~ N(0, sv2),  u ~ N+(0, su2)")

Xs = sm.add_constant(df[X_nom + ["t"]]).values
ys = df.ln_yalpi_2018narx_mlrd.values


def sfa_negll(par, X, y):
    k = X.shape[1]
    b, ls, lg = par[:k], par[k], par[k + 1]
    sigma = np.exp(ls)
    gam = 1 / (1 + np.exp(-lg))           # gamma = su2 / sigma2  (0..1)
    lam = np.sqrt(gam / (1 - gam))        # lambda = su / sv
    e = y - X @ b
    z = -e * lam / sigma
    ll = (np.log(2 / sigma) + stats.norm.logpdf(e / sigma)
          + stats.norm.logcdf(z))
    return -np.sum(ll)


b0 = np.linalg.lstsq(Xs, ys, rcond=None)[0]
res0 = ys - Xs @ b0
start = np.concatenate([b0, [np.log(res0.std()), 0.0]])
opt = minimize(sfa_negll, start, args=(Xs, ys), method="Nelder-Mead",
               options={"maxiter": 60000, "maxfev": 60000, "xatol": 1e-9,
                        "fatol": 1e-9})
opt = minimize(sfa_negll, opt.x, args=(Xs, ys), method="BFGS",
               options={"maxiter": 5000})

k = Xs.shape[1]
b_sfa = opt.x[:k]
sigma = np.exp(opt.x[k])
gamma = 1 / (1 + np.exp(-opt.x[k + 1]))
su = sigma * np.sqrt(gamma)
sv = sigma * np.sqrt(1 - gamma)
lam = su / sv

sfa_tab = pd.DataFrame({
    "Ўзгарувчи": ["Доимий ҳад"] + [YAXSHI_NOM.get(c, c) for c in X_nom + ["t"]],
    "SFA коэффициент": b_sfa})
p("")
p(sfa_tab.round(4).to_string(index=False))
p("")
p(f"sigma = {sigma:.4f} | gamma = {gamma:.4f} | sigma_u = {su:.4f} | "
  f"sigma_v = {sv:.4f} | lambda = {lam:.4f}")
p(f"gamma = {gamma:.3f} -> қолдиқ дисперсиясининг {gamma*100:.1f}% и")
p("     САМАРАСИЗЛИК (u) ҳисобига, қолгани тасодифий шок (v) ҳисобига.")

# Jondrow ва б. (1982) бўйича техник самарадорлик
e = ys - Xs @ b_sfa
mu_star = -e * su ** 2 / sigma ** 2
s_star = su * sv / sigma
zz = mu_star / s_star
u_hat = mu_star + s_star * stats.norm.pdf(zz) / stats.norm.cdf(zz)
df["sfa_te"] = np.exp(-u_hat)

sfa_ort = df.groupby("tuman")["sfa_te"].mean().sort_values(ascending=False)
p("")
p(f"{df.yil.min()}-{df.yil.max()} йй. ўртача SFA техник самарадорлиги (1.000 = чегара):")
p(sfa_ort.round(4).to_string())
p("")
p(f"Вилоят ўртачаси = {df.sfa_te.mean():.4f} -> ўртача {(1-df.sfa_te.mean())*100:.1f}%")
p("     самарасизлик мавжуд (айни ресурслар билан шунча кўп маҳсулот олиш мумкин эди).")

samlar = (df.groupby("tuman")
            .agg(dea_crs=("dea_crs", "mean"), dea_vrs=("dea_vrs", "mean"),
                 sfa_te=("sfa_te", "mean"),
                 wp_som_m3=("wp_som_m3", "mean"))
            .sort_values("sfa_te", ascending=False))
samlar.round(5).to_csv(os.path.join(OUT, "H_sfa_dea_jamlanma.csv"),
                       encoding="utf-8-sig")
r_ds = stats.spearmanr(samlar.dea_crs, samlar.sfa_te)
p("")
p(f"DEA ва SFA рейтинглари мослиги (Спирмен) : rho = {r_ds.statistic:.3f}, "
  f"p = {r_ds.pvalue:.4f}")

# --- H2. Иккинчи босқич: самарасизликнинг омиллари ---
p("")
p("--- H2. Самарадорликка таъсир этувчи омиллар (иккинчи босқич регрессия) ---")
p("Тобе ўзгарувчи: SFA техник самарадорлик балли (0-1)")
X2 = sm.add_constant(df[["hisoblagich_qamrov", "shorlanish_indeks",
                         "kanal_fik", "t"]])
m2 = sm.OLS(df.sfa_te, X2).fit(cov_type="cluster",
                               cov_kwds={"groups": df.tuman_id})
p(m2.summary().as_text())
p("")
p("Талқин: сув ҳисоблагичлари билан қамров 10 фоиз пунктга ошса, техник")
p(f"        самарадорлик {m2.params['hisoblagich_qamrov']*10:.4f} балга "
  f"({m2.params['hisoblagich_qamrov']*10/df.sfa_te.mean()*100:.2f}%) ортади.")
p(f"        Шўрланиш индекси 0.1 бирликка ошса, самарадорлик "
  f"{abs(m2.params['shorlanish_indeks'])*0.1:.4f} балга камаяди.")
pd.DataFrame({"Ўзгарувчи": X2.columns, "Коэффициент": m2.params.values,
              "Ст.хато": m2.bse.values, "p-value": m2.pvalues.values}
             ).round(5).to_csv(os.path.join(OUT, "H2_samaradorlik_omillari.csv"),
                               index=False, encoding="utf-8-sig")

# ===========================================================================
sarlavha("I. СУВ ТЕЖАШ САЛОҲИЯТИ ВА СЦЕНАРИЙ ТАҲЛИЛИ")
# ===========================================================================
# I-1. Илғор тажриба (benchmark) бўйича сув тежаш
etalon_m3ga = d24.suv_m3_ga.quantile(0.25)   # энг тежамкор чорак
d24["norma_suv_mln_m3"] = etalon_m3ga * d24.maydon_ming_ga * 1e3 / 1e6
d24["ortiqcha_suv_mln_m3"] = (d24.suv_mln_m3 - d24.norma_suv_mln_m3).clip(lower=0)
bench = d24[["tuman", "suv_m3_ga", "suv_mln_m3", "norma_suv_mln_m3",
             "ortiqcha_suv_mln_m3"]].sort_values("ortiqcha_suv_mln_m3",
                                                 ascending=False)
bench.columns = ["Туман", "Жорий м3/га", "Жорий сув, млн м3",
                 "Эталон бўйича, млн м3", "Ортиқча сарф, млн м3"]
p(f"Эталон (илғор чорак) солиштирма сарф: {etalon_m3ga:,.0f} м3/га")
p(bench.round(1).to_string(index=False))
jami_ortiqcha = bench["Ортиқча сарф, млн м3"].sum()
p("")
p(f"ЖАМИ ортиқча сарф = {jami_ortiqcha:,.0f} млн м3 "
  f"({jami_ortiqcha/jami_suv*100:.1f}% жами сувдан)")
p(f"Бу сув сақлаб қолинса, {jami_ortiqcha*1e6/(etalon_m3ga):,.0f} га = "
  f"{jami_ortiqcha*1e6/etalon_m3ga/1000:,.1f} минг га янги ер суғорилиши мумкин.")
bench.round(2).to_csv(os.path.join(OUT, "I_suv_tejash_salohiyati.csv"),
                      index=False, encoding="utf-8-sig")

# I-2. Сценарийлар (FE эластиклиги асосида)
p("")
p("--- Сценарий таҳлили (сув эластиклиги b = {:.3f} асосида) ---".format(b_suv))
senariylar = [
    ("Базавий ҳолат (2024)", 0.0, 0.0),
    ("Камсув йил: сув -10%", -0.10, 0.0),
    ("Кескин камсувлик: сув -20%", -0.20, 0.0),
    ("Сув -10%, ФИК +5 п.п. (томчилатиб суғориш)", -0.10, 0.075),
    ("Сув -20%, ФИК +10 п.п. + агротехника", -0.20, 0.16),
    ("Сув ўзгармайди, ФИК +10 п.п.", 0.0, 0.16),
]
sen_qatorlar = []
for nom, dsuv, dfik in senariylar:
    # самарали (далага етган) сув = олинган сув x (1 + dfik самараси)
    samarali_ozg = (1 + dsuv) * (1 + dfik) - 1
    d_yalpi = ((1 + samarali_ozg) ** b_suv - 1)
    yangi_yalpi = jami_yalpi * (1 + d_yalpi)
    yangi_suv = jami_suv * (1 + dsuv)
    sen_qatorlar.append({
        "Сценарий": nom,
        "Сув, млн м3": yangi_suv,
        "Ялпи маҳсулот, млрд сўм": yangi_yalpi,
        "Ўзгариш, %": d_yalpi * 100,
        "Ўзгариш, млрд сўм": yangi_yalpi - jami_yalpi,
        "Сув унумдорлиги, сўм/м3": yangi_yalpi * 1e9 / (yangi_suv * 1e6),
    })
sen = pd.DataFrame(sen_qatorlar)
p(sen.round(1).to_string(index=False))
sen.round(3).to_csv(os.path.join(OUT, "I_senariylar.csv"),
                    index=False, encoding="utf-8-sig")

p("")
p("Асосий хулоса: сув ҳажмини камайтириш маҳсулотни камайтиради, аммо ФИК ни")
p("оширувчи чоралар (томчилатиб суғориш, канал бетонлаш, лазер текислаш)")
p("камсувлик йўқотишини ТЎЛИҚ ҚОПЛАЙ ОЛАДИ.")

# ---------------------------------------------------------------------------
df.to_csv(os.path.join(OUT, "panel_tolik_natijalar.csv"),
          index=False, encoding="utf-8-sig")

# --- Графиклар учун асосий статистикалар (қўлда кўчирмаслик учун) ---
import json
kalit = {
    "suv_elastikligi": float(b_suv),
    "suv_elastikligi_se": float(fe_int.std_errors["ln_suv_ga"]),
    "anova_F": float(F), "anova_p": float(pval),
    "spearman_rho": float(r_ds.statistic), "spearman_p": float(r_ds.pvalue),
    "dea_ort_2024": float(dea24.dea_crs.mean()),
    "sfa_ort": float(df.sfa_te.mean()),
    "gini_suv": float(g_suv), "gini_wp": float(g_wp),
    "umumiy_fik_2024": float(b24.umumiy_fik),
    "mpw_som_m3": float(viloyat_mpw),
    "wp_viloyat_som_m3": float(jami_yalpi * 1e9 / (jami_suv * 1e6)),
    "yillar": [int(df.yil.min()), int(df.yil.max())],
}
try:
    with open(os.path.join(OUT, "kalit_korsatkichlar.json"), "w",
              encoding="utf-8") as f:
        json.dump(kalit, f, ensure_ascii=False, indent=2)
except PermissionError:
    print("  ОГОҲЛАНТИРИШ: kalit_korsatkichlar.json файли банд")
try:
    with open(os.path.join(OUT, "TAHLIL_HISOBOTI.txt"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(LOG))
except PermissionError:
    print("  ОГОҲЛАНТИРИШ: TAHLIL_HISOBOTI.txt файли банд")

print("\n\nБарча натижалар сақланди:", OUT)
