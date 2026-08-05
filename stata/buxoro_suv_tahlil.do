*==============================================================================
* БУХОРО ВИЛОЯТИ: АМУДАРЁДАН ОЛИНГАН СУВНИНГ ТАҚСИМОТИ, ҚИШЛОҚ ХЎЖАЛИГИ
* ДАРОМАДИ ВА СУВДАН ФОЙДАЛАНИШ САМАРАДОРЛИГИНИНГ ИҚТИСОДИЙ ТАҲЛИЛИ
*
* Панель: 11 туман x 2014-2024 йй. (121 кузатув)
* Талаб: Stata 14 ёки юқори (UTF-8 кирилл матн учун)
*
* Ишга тушириш:
*   1) Қуйидаги global yol ни ўз папкангизга мослаштиринг
*   2) Stata да:  do "buxoro_suv_tahlil.do"
*
* Талаб қилинадиган қўшимча пакетлар (интернет керак):
*   ssc install estout, replace     // жадвалларни экспорт қилиш
*   ssc install dea, replace        // DEA таҳлили
*   ssc install heatplot, replace   // иссиқлик харитаси
*   ssc install palettes, replace   // heatplot учун ранглар
*   ssc install colrspace, replace  // heatplot учун ранглар
*==============================================================================

clear all
set more off
version 14

*--- ЙЎЛЛАРНИ МОСЛАШТИРИНГ -----------------------------------------------
global yol      "D:/IT Projects/buxoro-suv-tahlili"
global data     "$yol/data"
global natija   "$yol/natijalar_stata"
global grafik   "$yol/grafiklar_stata"

capture mkdir "$natija"
capture mkdir "$grafik"

log using "$natija/buxoro_suv_tahlil.log", replace text

*==============================================================================
* 0. МАЪЛУМОТЛАРНИ ЮКЛАШ ВА ҲОСИЛА КЎРСАТКИЧЛАРНИ ҲИСОБЛАШ
*==============================================================================
import delimited "$data/buxoro_suv_panel.csv", clear varnames(1) encoding(UTF-8)

* Панель тузилмасини эълон қилиш
xtset tuman_id yil
label var suv_mln_m3          "Олинган сув, млн м3"
label var maydon_ming_ga      "Суғориладиган майдон, минг га"
label var yalpi_joriy_mlrd    "Ялпи маҳсулот (жорий нарх), млрд сўм"
label var yalpi_2018narx_mlrd "Ялпи маҳсулот (2018 нархида), млрд сўм"
label var mehnat_ming_kishi   "Банд аҳоли, минг киши"
label var kapital_2018_mlrd   "Асосий капитал (2018 нархида), млрд сўм"
label var shorlanish_indeks   "Тупроқ шўрланиш индекси"
label var hisoblagich_qamrov  "Сув ҳисоблагичлари билан қамров, %"
label var kanal_fik           "Суғориш тармоғи ФИК"

*--- Ҳосила кўрсаткичлар ---
gen suv_m3_ga     = suv_mln_m3*1e6 / (maydon_ming_ga*1e3)
gen wp_som_m3     = yalpi_joriy_mlrd*1e9    / (suv_mln_m3*1e6)
gen wp_real       = yalpi_2018narx_mlrd*1e9 / (suv_mln_m3*1e6)
gen wp_usd_m3     = wp_som_m3 / kurs_som_usd
gen daromad_usd_ga= yalpi_joriy_mlrd*1e9 / kurs_som_usd / (maydon_ming_ga*1e3)
gen suv_sigimi    = (suv_mln_m3*1e6) / (yalpi_2018narx_mlrd*1e3)

label var suv_m3_ga  "Солиштирма сув сарфи, м3/га"
label var wp_som_m3  "Сув унумдорлиги, сўм/м3"
label var wp_usd_m3  "Сув унумдорлиги, USD/м3"
label var suv_sigimi "Сув сиғими, м3 / млн сўм"

*--- Логарифмлар (Кобб-Дуглас учун) ---
gen ln_y   = ln(yalpi_2018narx_mlrd)
gen ln_suv = ln(suv_mln_m3)
gen ln_meh = ln(mehnat_ming_kishi)
gen ln_may = ln(maydon_ming_ga)
gen ln_kap = ln(kapital_2018_mlrd)
gen t      = yil - 2014

*--- Интенсив (1 га га) шакл ---
gen ln_y_ga   = ln(yalpi_2018narx_mlrd / maydon_ming_ga)
gen ln_suv_ga = ln(suv_mln_m3          / maydon_ming_ga)
gen ln_meh_ga = ln(mehnat_ming_kishi   / maydon_ming_ga)
gen ln_kap_ga = ln(kapital_2018_mlrd   / maydon_ming_ga)

*--- Канал зонаси ---
encode zona, gen(zona_id)
label define zonal 1 "Канал боши" 2 "Канал охири" 3 "Ўрта оқим"
* (encode алифбо тартибида кодлайди: bosh, oxirgi, orta)

save "$natija/buxoro_panel.dta", replace

*==============================================================================
* A. ТАВСИФИЙ СТАТИСТИКА
*==============================================================================
display _newline(2) "=== A. ТАВСИФИЙ СТАТИСТИКА ==="

summarize suv_mln_m3 maydon_ming_ga suv_m3_ga yalpi_joriy_mlrd ///
          yalpi_2018narx_mlrd wp_som_m3 wp_usd_m3 mehnat_ming_kishi ///
          kapital_2018_mlrd shorlanish_indeks hisoblagich_qamrov, detail

* Панель тузилмасининг ички/ташқи вариацияси
xtsum suv_mln_m3 maydon_ming_ga wp_som_m3 shorlanish_indeks

* Йиллар кесимида вилоят якуни
preserve
    collapse (sum) suv_mln_m3 maydon_ming_ga yalpi_joriy_mlrd ///
                   yalpi_2018narx_mlrd, by(yil)
    gen wp_som_m3 = yalpi_joriy_mlrd*1e9 / (suv_mln_m3*1e6)
    gen suv_m3_ga = suv_mln_m3*1e6 / (maydon_ming_ga*1e3)
    list, sep(0) noobs
    export delimited "$natija/A_viloyat_yillar.csv", replace
restore

*==============================================================================
* B. СУВНИНГ ТУМАНЛАР КЕСИМИДА ТАҚСИМЛАНИШИ (2024)
*==============================================================================
display _newline(2) "=== B. СУВ ТАҚСИМОТИ, 2024 ==="

preserve
    keep if yil == 2024
    egen jami_suv    = total(suv_mln_m3)
    egen jami_maydon = total(maydon_ming_ga)
    egen jami_yalpi  = total(yalpi_joriy_mlrd)
    gen suv_ulush    = suv_mln_m3     / jami_suv    * 100
    gen maydon_ulush = maydon_ming_ga / jami_maydon * 100
    gen yalpi_ulush  = yalpi_joriy_mlrd / jami_yalpi * 100
    gen farq_pp      = suv_ulush - maydon_ulush
    label var farq_pp "Сув улуши - майдон улуши, фоиз пункт"

    gsort -suv_mln_m3
    list tuman zona suv_mln_m3 suv_ulush maydon_ming_ga maydon_ulush ///
         suv_m3_ga yalpi_joriy_mlrd yalpi_ulush farq_pp, sep(0) noobs ///
         abbreviate(16)
    export delimited "$natija/B_suv_taqsimoti_2024.csv", replace

    *--- 1-график: туманлар кесимида сув олиш ---
    graph hbar (asis) suv_mln_m3, over(tuman, sort(1) descending    ///
        label(labsize(small)))                                      ///
        bar(1, color("42 120 214"))                                 ///
        blabel(bar, format(%9.0fc) size(vsmall))                    ///
        ytitle("млн м3/йил", size(small))                           ///
        title("Амударёдан олинган сувнинг туманлар кесимида тақсимланиши", ///
              size(medsmall) position(11))                          ///
        subtitle("2024 йил", size(small) position(11))              ///
        note("Манба: муаллиф ҳисоб-китоблари", size(vsmall))         ///
        graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/01_suv_taqsimoti.png", replace width(2000)

    *--- 2-график: сув улуши ва майдон улуши фарқи (дивергент) ---
    gen pos = farq_pp if farq_pp >= 0
    gen neg = farq_pp if farq_pp <  0
    graph hbar (asis) pos neg, over(tuman, sort(farq_pp)            ///
        label(labsize(small)))                                      ///
        bar(1, color("42 120 214")) bar(2, color("208 59 59"))      ///
        legend(off) ytitle("фоиз пункт", size(small))               ///
        title("Сув тақсимоти майдон улушига мос келадими?",         ///
              size(medsmall) position(11))                          ///
        subtitle("Мусбат — туман ер улушига нисбатан кўпроқ сув олмоқда", ///
                 size(vsmall) position(11))                         ///
        graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/02_suv_maydon_farqi.png", replace width(2000)
restore

*==============================================================================
* C. СУВДАН ФОЙДАЛАНИШ САМАРАДОРЛИГИ ИНДИКАТОРЛАРИ
*==============================================================================
display _newline(2) "=== C. САМАРАДОРЛИК ИНДИКАТОРЛАРИ, 2024 ==="

preserve
    keep if yil == 2024
    gsort -wp_som_m3
    list tuman zona suv_m3_ga wp_som_m3 wp_usd_m3 daromad_usd_ga ///
         suv_sigimi shorlanish_indeks kanal_fik, sep(0) noobs abbreviate(16)
    export delimited "$natija/C_samaradorlik_2024.csv", replace

    * Канал зонаси бўйича фарқ аҳамиятлими?
    display _newline "--- Зоналар кесимида дисперсион таҳлил (ANOVA) ---"
    oneway wp_som_m3 zona_id, tabulate
    * Бонферрони тузатиши билан жуфт солиштириш
    oneway wp_som_m3 zona_id, bonferroni noanova

    *--- 3-график: сув унумдорлиги рейтинги, зона бўйича рангланган ---
    graph hbar (asis) wp_som_m3, over(tuman, sort(1) descending     ///
        label(labsize(small))) asyvars                              ///
        blabel(bar, format(%9.0fc) size(vsmall))                    ///
        ytitle("сўм / м3 (жорий нарх)", size(small))                ///
        title("Сувдан фойдаланиш самарадорлиги: 1 м3 сув қанча даромад беради", ///
              size(medsmall) position(11))                          ///
        legend(off)                                                 ///
        graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/03_suv_unumdorligi.png", replace width(2000)
restore

*==============================================================================
* D. ТАҚСИМОТ ТЕНГСИЗЛИГИ: ДЖИНИ ВА ЛОРЕНЦ
*==============================================================================
display _newline(2) "=== D. ТЕНГСИЗЛИК ==="

preserve
    keep if yil == 2024
    * Джини коэффициенти (ineqdeco ёки fastgini бўлмаса — қўлда)
    capture ssc install fastgini
    capture noisily fastgini suv_m3_ga
    capture noisily fastgini wp_som_m3

    * Лоренц эгри чизиғи учун кумулятив улушлар
    gsort wp_som_m3
    egen jami_suv2   = total(suv_mln_m3)
    egen jami_yalpi2 = total(yalpi_joriy_mlrd)
    gen kum_suv   = sum(suv_mln_m3)       / jami_suv2   * 100
    gen kum_yalpi = sum(yalpi_joriy_mlrd) / jami_yalpi2 * 100
    * Бошланғич (0,0) нуқтасини қўшиш
    local N = _N + 1
    set obs `N'
    replace kum_suv   = 0 in `N'
    replace kum_yalpi = 0 in `N'
    sort kum_suv

    twoway (line kum_yalpi kum_suv, lcolor("42 120 214") lwidth(medthick) ///
                                    msymbol(O) mcolor("42 120 214"))      ///
           (function y = x, range(0 100) lcolor(gs10) lpattern(dash)),    ///
           xtitle("сув сарфининг кумулятив улуши, %", size(small))        ///
           ytitle("ялпи маҳсулотнинг кумулятив улуши, %", size(small))    ///
           title("Сув билан даромад ўртасидаги номутаносиблик",           ///
                 size(medsmall) position(11))                             ///
           legend(order(1 "кузатилаётган тақсимот" 2 "мутлақ тенглик")    ///
                  size(small) region(lstyle(none)))                       ///
           graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/07_lorenz.png", replace width(1600)
    export delimited tuman kum_suv kum_yalpi using ///
        "$natija/D_lorenz.csv", replace
restore

*==============================================================================
* E. КОББ-ДУГЛАС ИШЛАБ ЧИҚАРИШ ФУНКЦИЯСИ
*    ln(Y) = a_i + b1 ln(Сув) + b2 ln(Меҳнат) + b3 ln(Ер) + b4 ln(Капитал)
*            + b5 Шўрланиш + c_t + e
*==============================================================================
display _newline(2) "=== E. ИШЛАБ ЧИҚАРИШ ФУНКЦИЯСИ ==="

*--- E1. Pooled OLS (кластер-мустаҳкам стандарт хатолар) ---
display _newline "--- E1. Pooled OLS ---"
regress ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, ///
        vce(cluster tuman_id)
estimates store OLS

* Мультиколлинеарлик текшируви
quietly regress ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t
vif
* Гетероскедастиклик ва нормаллик
estat hettest
predict resid_ols, residuals
swilk resid_ols
drop resid_ols

*--- E2. Fixed Effects (туман + йил эффектлари) ---
display _newline "--- E2. Fixed Effects ---"
xtreg ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks i.yil, ///
      fe vce(cluster tuman_id)
estimates store FE

*--- E3. Random Effects ---
display _newline "--- E3. Random Effects ---"
xtreg ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, re
estimates store RE

*--- Хаусман тести (FE ва RE ўртасида танлов) ---
display _newline "--- Хаусман тести ---"
quietly xtreg ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, fe
estimates store fe_h
quietly xtreg ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, re
estimates store re_h
hausman fe_h re_h, sigmamore

* Брейш-Пейган LM тести (Pooled OLS га қарши RE)
quietly xtreg ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, re
xttest0

*--- E4. Интенсив шакл (1 га га; доимий миқёс самараси шарти) ---
* ИЗОҲ: суғориладиган майдон панелда деярли ўзгармас бўлгани учун
* экстенсив FE да ер ва сув коэффициентлари ўзаро коллинеар бўлади.
* Шу боис базавий баҳо сифатида интенсив шакл олинади.
display _newline "--- E4. FE, интенсив шакл (1 га га) ---"
xtreg ln_y_ga ln_suv_ga ln_meh_ga ln_kap_ga shorlanish_indeks i.yil, ///
      fe vce(cluster tuman_id)
estimates store FE_INT
scalar b_suv = _b[ln_suv_ga]
display "СУВ ЭЛАСТИКЛИГИ b = " %6.3f scalar(b_suv)
display "Ер эластиклиги (CRS шарти остида қолдиқ) = " ///
        %6.3f 1 - _b[ln_suv_ga] - _b[ln_meh_ga] - _b[ln_kap_ga]

*--- Барча моделларни бир жадвалда солиштириш ---
capture which esttab
if _rc == 0 {
    esttab OLS FE RE FE_INT using "$natija/E_modellar.rtf", replace ///
        b(4) se(4) star(* 0.10 ** 0.05 *** 0.01) r2 ar2 nogaps      ///
        drop(*.yil) title("Кобб-Дуглас ишлаб чиқариш функцияси")    ///
        mtitles("Pooled OLS" "FE" "RE" "FE интенсив")
    esttab OLS FE RE FE_INT, b(4) se(4) star(* 0.10 ** 0.05 *** 0.01) ///
        drop(*.yil) mtitles("OLS" "FE" "RE" "FE-инт")
}

*--- 5-график: сув сарфи <-> ҳосилдорлик боғланиши ---
twoway (scatter ln_y_ga ln_suv_ga, mcolor("42 120 214%55")            ///
            msymbol(O) msize(medsmall))                               ///
       (lfit ln_y_ga ln_suv_ga, lcolor("208 59 59") lwidth(medthick)), ///
       xtitle("ln(1 га га сув сарфи)", size(small))                   ///
       ytitle("ln(1 га га ялпи маҳсулот, 2018 нархида)", size(small)) ///
       title("Сув сарфи ва ҳосилдорлик ўртасидаги боғланиш",          ///
             size(medsmall) position(11))                             ///
       legend(order(1 "туман-йил кузатувлари" 2 "регрессия чизиғи")   ///
              size(small) region(lstyle(none)))                       ///
       graphregion(color("252 252 251")) plotregion(color("252 252 251"))
graph export "$grafik/05_suv_mahsulot.png", replace width(1600)

*==============================================================================
* F. СУВНИНГ ЧЕККИ МАҲСУЛДОРЛИГИ (MPW) ВА СОЯ НАРХИ
*==============================================================================
display _newline(2) "=== F. СУВНИНГ ЧЕККИ МАҲСУЛДОРЛИГИ ==="
* MPW = b_сув * (Y / W)  — 1 қўшимча м3 сув берадиган қўшимча маҳсулот

gen mpw_som_m3 = scalar(b_suv) * yalpi_joriy_mlrd*1e9 / (suv_mln_m3*1e6)
gen mpw_usd_m3 = mpw_som_m3 / kurs_som_usd
label var mpw_som_m3 "Сувнинг чекли маҳсулдорлиги, сўм/м3"

preserve
    keep if yil == 2024
    gsort -mpw_som_m3
    list tuman zona wp_som_m3 mpw_som_m3 mpw_usd_m3, sep(0) noobs abbreviate(16)
    export delimited "$natija/F_mpw_2024.csv", replace
    summarize mpw_som_m3
    display "Иқтисодий маъно: сувнинг соя нархи (shadow price). Сув тарифи"
    display "шу даражадан анча паст бўлса — сувни тежашга рағбат йўқ."
restore

*==============================================================================
* G. DEA — ТЕХНИК САМАРАДОРЛИК (кириш-йўналтирилган)
*==============================================================================
display _newline(2) "=== G. DEA ТАҲЛИЛИ ==="
* Талаб: ssc install dea
* Киришлар: сув, майдон, меҳнат, капитал | Чиқиш: ялпи маҳсулот (2018 нархида)

* ДИҚҚАТ: SSC даги `dea` пакетининг синтаксиси версияга қараб фарқ қилади.
* Ишга туширишдан олдин `help dea` орқали текширинг. Асосий шакли:
*     dea <киришлар> = <чиқишлар>, rts(crs|vrs) ori(in|out) saving(файл)
* Натижалар r(dearslt) матрицасида ва saving() файлида сақланади.

capture which dea
if _rc != 0 {
    display as error "DEA пакети ўрнатилмаган. Ишга тушириш: ssc install dea"
    display as error "Муқобил йўл: Python да ҳисобланган DEA балларини улаш"
    display as error "(қуйидаги merge блоки)."
}
else {
    tempfile dea_hammasi
    local birinchi = 1
    levelsof yil, local(yillar)
    foreach y of local yillar {
        preserve
            keep if yil == `y'
            keep tuman_id yil suv_mln_m3 maydon_ming_ga ///
                 mehnat_ming_kishi kapital_2018_mlrd yalpi_2018narx_mlrd
            tempfile crs_f vrs_f
            quietly dea suv_mln_m3 maydon_ming_ga mehnat_ming_kishi ///
                kapital_2018_mlrd = yalpi_2018narx_mlrd,            ///
                rts(crs) ori(in) saving("`crs_f'", replace)
            quietly dea suv_mln_m3 maydon_ming_ga mehnat_ming_kishi ///
                kapital_2018_mlrd = yalpi_2018narx_mlrd,            ///
                rts(vrs) ori(in) saving("`vrs_f'", replace)
            * dea saving() файлидаги самарадорлик устуни одатда `te` ёки
            * `theta` деб номланади — версияга қараб мослаштиринг:
            preserve
                use "`crs_f'", clear
                capture rename theta te
                keep te
                rename te dea_crs
                tempfile c2
                save `c2', replace
            restore
            preserve
                use "`vrs_f'", clear
                capture rename theta te
                keep te
                rename te dea_vrs
                tempfile v2
                save `v2', replace
            restore
            merge 1:1 _n using `c2', nogen
            merge 1:1 _n using `v2', nogen
            gen miqyos_sam = dea_crs / dea_vrs
            keep tuman_id yil dea_crs dea_vrs miqyos_sam
            if `birinchi' == 1 {
                save `dea_hammasi', replace
                local birinchi = 0
            }
            else {
                append using `dea_hammasi'
                save `dea_hammasi', replace
            }
        restore
    }
    capture merge 1:1 tuman_id yil using `dea_hammasi', nogen
}

*--- МУҚОБИЛ ЙЎЛ: Python да ҳисобланган DEA балларини улаш ------------------
* Агар `dea` пакети ишламаса, қуйидаги 5 қаторни изоҳдан чиқаринг:
* preserve
*     import delimited "$yol/natijalar/panel_tolik_natijalar.csv", ///
*         clear varnames(1) encoding(UTF-8)
*     keep tuman_id yil dea_crs dea_vrs
*     tempfile dea_py
*     save `dea_py', replace
* restore
* merge 1:1 tuman_id yil using `dea_py', nogen

capture confirm variable dea_crs
if _rc == 0 {
    display _newline "--- Туманлар бўйича ўртача DEA баллари ---"
    tabstat dea_crs dea_vrs miqyos_sam, by(tuman) stat(mean) format(%6.4f)
    gen suv_tejash_pct = (1 - dea_crs) * 100
    label var dea_crs "DEA техник самарадорлик (CRS)"
    label var suv_tejash_pct "Назарий сув тежаш салоҳияти, %"
}

*==============================================================================
* H. SFA — СТОХАСТИК ЧЕГАРА ТАҲЛИЛИ
*    ln(Y) = f(киришлар) + v - u,  v ~ N(0,sv2),  u ~ N+(0,su2)
*==============================================================================
display _newline(2) "=== H. SFA ТАҲЛИЛИ ==="

*--- H1. Пул қилинган стохастик чегара (half-normal) ---
frontier ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, ///
         distribution(hnormal)
estimates store SFA_POOL
predict te_sfa, te
label var te_sfa "SFA техник самарадорлик"

display _newline "--- gamma = su2/(su2+sv2): самарасизликнинг қолдиқдаги улуши ---"
* frontier моделининг дисперсия параметрлари e() да сақланади
ereturn list
capture display "sigma_u = " %7.4f e(sigma_u)
capture display "sigma_v = " %7.4f e(sigma_v)
capture display "gamma   = " %7.4f e(sigma_u)^2 / (e(sigma_u)^2 + e(sigma_v)^2)
* Самарасизлик компоненти умуман мавжудлигини текшириш (LR тести)
* frontier автоматик равишда "LR test of sigma_u=0" ни чоп этади.
* Агар p > 0.10 бўлса — маълумотда бир томонлама самарасизлик топилмаган,
* бу ҳолда SFA ўрнига DEA натижаларига таяниш керак.

*--- H2. Панель SFA: вақт бўйича ўзгарувчи самарасизлик (Battese-Coelli) ---
xtfrontier ln_y ln_suv ln_meh ln_may ln_kap shorlanish_indeks t, tvd
estimates store SFA_PANEL
predict te_xt, te

display _newline "--- Туманлар бўйича ўртача SFA самарадорлиги ---"
tabstat te_sfa te_xt, by(tuman) stat(mean) format(%6.4f)
summarize te_sfa te_xt

* DEA ва SFA рейтинглари бир-бирига мос келадими?
capture confirm variable dea_crs
if _rc == 0 {
    spearman dea_crs te_sfa
    corr dea_crs te_sfa
}

*--- H3. Иккинчи босқич: самарасизликнинг омиллари ---
display _newline "--- H3. Самарадорликка таъсир этувчи омиллар ---"
regress te_sfa hisoblagich_qamrov shorlanish_indeks kanal_fik t, ///
        vce(cluster tuman_id)
estimates store TE_OMIL
display "Талқин: ҳисоблагичлар қамрови 10 п.п. ошса, самарадорлик " ///
        %6.4f _b[hisoblagich_qamrov]*10 " балга ортади."

*--- 6-график: DEA ва SFA солиштируви ---
capture confirm variable dea_crs
if _rc == 0 {
    preserve
        collapse (mean) dea_crs te_sfa, by(tuman)
        graph hbar (asis) dea_crs te_sfa, over(tuman, sort(dea_crs) ///
            label(labsize(small)))                                  ///
            bar(1, color("42 120 214")) bar(2, color("235 104 52"))  ///
            blabel(bar, format(%4.3f) size(vsmall))                 ///
            ytitle("самарадорлик балли (1.000 = чегара)", size(small)) ///
            title("Туманларнинг техник самарадорлиги: икки усул бўйича", ///
                  size(medsmall) position(11))                      ///
            legend(order(1 "DEA (CRS)" 2 "SFA") size(small)          ///
                   region(lstyle(none)))                            ///
            graphregion(color("252 252 251")) plotregion(color("252 252 251"))
        graph export "$grafik/06_dea_sfa.png", replace width(2000)
    restore
}

*==============================================================================
* I. СУВ ТЕЖАШ САЛОҲИЯТИ ВА СЦЕНАРИЙ ТАҲЛИЛИ
*==============================================================================
display _newline(2) "=== I. СУВ ТЕЖАШ САЛОҲИЯТИ ==="

preserve
    keep if yil == 2024
    * Илғор чорак (25-перцентиль) — эталон солиштирма сарф
    _pctile suv_m3_ga, p(25)
    scalar etalon = r(r1)
    display "Эталон солиштирма сарф (25-перцентиль): " %9.0fc scalar(etalon) " м3/га"

    gen norma_suv   = scalar(etalon) * maydon_ming_ga*1e3 / 1e6
    gen ortiqcha    = max(suv_mln_m3 - norma_suv, 0)
    egen jami_ort   = total(ortiqcha)
    egen jami_suv3  = total(suv_mln_m3)

    gsort -ortiqcha
    list tuman suv_m3_ga suv_mln_m3 norma_suv ortiqcha, sep(0) noobs abbreviate(14)
    display "ЖАМИ ортиқча сарф = " %9.0fc jami_ort[1] " млн м3 (" ///
            %4.1f jami_ort[1]/jami_suv3[1]*100 "% жами сувдан)"
    export delimited "$natija/I_suv_tejash.csv", replace
restore

*--- Сценарийлар: сув ҳажми ва ФИК ўзгаришининг маҳсулотга таъсири ---
display _newline "--- Сценарий таҳлили (b_сув = " %5.3f scalar(b_suv) ") ---"
preserve
    keep if yil == 2024
    collapse (sum) suv_mln_m3 yalpi_joriy_mlrd
    scalar baza_suv   = suv_mln_m3[1]
    scalar baza_yalpi = yalpi_joriy_mlrd[1]

    clear
    set obs 6
    gen str60 senariy = ""
    gen d_suv = .
    gen d_fik = .
    replace senariy = "Базавий ҳолат (2024)"                    in 1
    replace d_suv =  0.00  in 1
    replace d_fik =  0.00  in 1
    replace senariy = "Камсув йил: сув -10%"                    in 2
    replace d_suv = -0.10  in 2
    replace d_fik =  0.00  in 2
    replace senariy = "Кескин камсувлик: сув -20%"              in 3
    replace d_suv = -0.20  in 3
    replace d_fik =  0.00  in 3
    replace senariy = "Сув -10%, ФИК +5 п.п. (томчилатиб)"      in 4
    replace d_suv = -0.10  in 4
    replace d_fik =  0.075 in 4
    replace senariy = "Сув -20%, ФИК +10 п.п. + агротехника"    in 5
    replace d_suv = -0.20  in 5
    replace d_fik =  0.16  in 5
    replace senariy = "Сув ўзгармайди, ФИК +10 п.п."            in 6
    replace d_suv =  0.00  in 6
    replace d_fik =  0.16  in 6

    * Самарали сув = олинган сув x ФИК ошиши
    gen samarali = (1 + d_suv)*(1 + d_fik) - 1
    gen d_yalpi_pct = ((1 + samarali)^scalar(b_suv) - 1) * 100
    gen yangi_suv   = scalar(baza_suv)   * (1 + d_suv)
    gen yangi_yalpi = scalar(baza_yalpi) * (1 + d_yalpi_pct/100)
    gen ozgarish_mlrd = yangi_yalpi - scalar(baza_yalpi)
    gen wp_yangi = yangi_yalpi*1e9 / (yangi_suv*1e6)

    format d_yalpi_pct %6.1f
    format yangi_suv yangi_yalpi ozgarish_mlrd wp_yangi %12.1fc
    list senariy yangi_suv yangi_yalpi d_yalpi_pct ozgarish_mlrd wp_yangi, ///
         sep(0) noobs abbreviate(16)
    export delimited "$natija/I_senariylar.csv", replace

    *--- 9-график: сценарийлар ---
    drop in 1
    gen pos = d_yalpi_pct if d_yalpi_pct >= 0
    gen neg = d_yalpi_pct if d_yalpi_pct <  0
    graph hbar (asis) pos neg, over(senariy, label(labsize(vsmall)))  ///
        bar(1, color("42 120 214")) bar(2, color("208 59 59"))        ///
        blabel(bar, format(%5.1f) size(vsmall)) legend(off)           ///
        ytitle("ялпи маҳсулотнинг ўзгариши, %", size(small))          ///
        title("Сув тежаш технологиялари камсувликни қоплай оладими?", ///
              size(medsmall) position(11))                            ///
        graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/09_senariylar.png", replace width(2000)
restore

*==============================================================================
* J. ҚЎШИМЧА ГРАФИКЛАР
*==============================================================================

*--- 4-график: динамика (2014 = 100 индекс) ---
preserve
    collapse (sum) suv_mln_m3 yalpi_2018narx_mlrd, by(yil)
    gen wp_real = yalpi_2018narx_mlrd*1e9 / (suv_mln_m3*1e6)
    foreach v in suv_mln_m3 yalpi_2018narx_mlrd wp_real {
        quietly summarize `v' if yil == 2014
        gen i_`v' = `v' / r(mean) * 100
    }
    twoway (connected i_suv_mln_m3 yil, lcolor("42 120 214")             ///
                mcolor("42 120 214") lwidth(medthick))                   ///
           (connected i_yalpi_2018narx_mlrd yil, lcolor("235 104 52")    ///
                mcolor("235 104 52") lwidth(medthick))                   ///
           (connected i_wp_real yil, lcolor("27 175 122")                ///
                mcolor("27 175 122") lwidth(medthick)),                  ///
           yline(100, lcolor(gs12))                                      ///
           xlabel(2014(1)2024, labsize(small)) ytitle("индекс, 2014 = 100") ///
           title("Сув сарфи барқарор, маҳсулот ва сув унумдорлиги ўсмоқда", ///
                 size(medsmall) position(11))                            ///
           legend(order(1 "Олинган сув" 2 "Ялпи маҳсулот (2018 нархида)" ///
                        3 "Сув унумдорлиги") size(small) rows(3)         ///
                  region(lstyle(none)) position(11) ring(0))             ///
           graphregion(color("252 252 251")) plotregion(color("252 252 251"))
    graph export "$grafik/04_dinamika.png", replace width(1800)
restore

*--- 8-график: иссиқлик харитаси (heatplot пакети керак) ---
capture which heatplot
if _rc == 0 {
    heatplot wp_real i.tuman_id i.yil, color(Blues) ///
        values(format(%9.0fc) size(tiny))           ///
        title("Сув унумдорлигининг туман ва йиллар кесимидаги динамикаси", ///
              size(medsmall) position(11))          ///
        graphregion(color("252 252 251"))
    graph export "$grafik/08_issiqlik_xaritasi.png", replace width(2200)
}
else {
    display as error "heatplot ўрнатилмаган: ssc install heatplot, palettes, colrspace"
}

*==============================================================================
* ЯКУН
*==============================================================================
save "$natija/buxoro_panel_natijalar.dta", replace
display _newline(2) "=== ТАҲЛИЛ ЯКУНЛАНДИ ==="
display "Натижалар: $natija"
display "Графиклар: $grafik"

log close
