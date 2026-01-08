## 1. Nazwa projektu

**[AI PRV]: DIET_APP**
Owner: **Grzegorz** (vibe coding w VS Code + Claude Code)
Data / wersja: **2026-01-07 / v0.x**

---

## 2. „Vibe coding brief” (jak ma pracować Claude Code)

### Tryb pracy

* **Rola Claude Code:** Senior Python Engineer + QA + DevOps light
* **Styl:** minimalny, iteracyjny, bez over-engineeringu
* **Zasada:** najpierw działający szkielet → potem testy → potem UX → na końcu “ładne” LLM

### Ograniczenia i priorytety

* Każdy commit = mały krok (≤ 2h weekday / 4h weekend)
* Zawsze utrzymuj uruchamialność (run succeeds) + minimalne testy regresji
* **Zero chmury / offline-first / brak egress**
* **CFO-grade:** deterministyczne liczby + explainability + eksport (Excel/PDF/JSON)
* **DGX Spark-first:** jeśli coś da się sensownie przyspieszyć GPU (forecast/LLM/feature engineering) → rób to, ale prosto

### Format zadań dla Claude Code (kopiuj-wklej)

**Prompt do Claude Code (szablon):**

* Cel bloku: `<1 zdanie>`
* Zmiany: `<lista plików / funkcji>`
* DoD bloku: `<checklista>`
* Uruchom: `<komendy>`
* Testy: `<komendy>`
* Notatka: „Jeśli niepewne → wybierz najprostsze rozwiązanie”.

---

## 3. Cel produktu i JTBD

### Cel (1 zdanie)

Aplikacja ma śledzić moje postępy w diecie i treningu, liczyć bilans energii, oceniać trend i proponować proste korekty prowadzące do celu (75 kg / redukcja tłuszczu).

### JTBD

Kiedy **Grzegorz Hankus** ma **dzienne dane poranne** (masa ciała + skład) oraz **dzienny bilans kalorii** (zjedzone vs wydatkowane), chce **otrzymać analizę**, wykresy, krótką prognozę i komentarz (opcjonalnie z LLM), aby podejmować decyzje “co zmienić jutro/ten tydzień”.

---

## 4. Użytkownicy i use cases

### Persony

**1299. Grzegorz Hankus** – użytkownik single, analityczny (“CFO-grade”), chce trendów, KPI, czerwonych flag, eksportu i powtarzalności.

### Top use cases (max 7)

* **UC1:** Dzienny wpis danych (waga, %tłuszczu itp., kalorie zjedzone, kalorie sport) w < 60 sekund.
* **UC2:** Dashboard: trend wagi/tłuszczu, rolling averages, bilans energii, “czy idę zgodnie z planem?”.
* **UC3:** Prognoza (7/14/30 dni) + scenariusz “co jeśli” (np. -200 kcal/dzień).
* **UC4:** KPI + red flags (np. stagnacja trendu, zbyt duża zmienność, brak danych).
* **UC5:** Eksport tygodniowy/miesięczny: **Excel + PDF + analysis.json**.
* **UC6:** (Opcjonalnie) LLM: krótki komentarz i rekomendacje oparte WYŁĄCZNIE na policzonych metrykach (bez halucynacji).
* **UC7:** Korekty/edycja danych i audyt zmian (kto/co/kiedy – nawet jeśli to tylko Ty).

---

## 5. Zakres (MVP → Phase 2 → Phase 3)

### MVP – In scope (konkret)

* Lokalna baza danych (SQLite/DuckDB) + prosty model danych
* Formularz dzienny (manual entry) + walidacje + edycja wpisów
* Metryki bazowe + KPI + red flags
* Wykresy trendu (waga, tłuszcz, bilans kcal)
* Prosta prognoza (baseline: rolling trend / regresja / Kalman-lite)
* Eksport: Excel + PDF + JSON
* Opcjonalnie: lokalny LLM (Ollama/vLLM) do narracji + Q&A “na moich danych” (bez chmury)

### MVP – Out of scope

* Integracje API z wagą/smartwatchem (Garmin/Withings/Fitbit)
* Skanowanie posiłków, baza produktów, barcode
* Aplikacja mobilna (native)
* Zaawansowane plany treningowe/dietetyczne (medyczne)
* Chmurowa synchronizacja, multi-user

### Phase 2

* Import CSV (z wagi / zegarka / MyFitnessPal itp.)
* Scenariusze i cele (np. etap redukcji/utrzymania) + porównanie tygodni
* Lepsza prognoza (bayes/prophet-like offline) + wykrywanie plateau
* Szyfrowanie danych “at rest” (np. SQLCipher) + backup/restore
* LLM: “weekly coach summary” z twardymi guard-rails

### Phase 3

* Personalizacja modeli (fine-tuning małego modelu / LoRA lokalnie)
* RAG nad własnymi notatkami (Evernote-export offline) + reguły nawyków
* Automatyczna detekcja anomalii (np. woda/retencja) i rekomendacje scenariuszowe
* Benchmark jakości LLM (regresja jakościowa) + scoring użyteczności

---

## 6. KPI sukcesu (mierzalne)

* **Czas E2E (open → dashboard):** ≤ 2 s dla 365 dni danych (bez LLM)
* **Czas “dodaj wpis”:** ≤ 60 s
* **Poprawność (deterministyczna):** 100% zgodność metryk z testami golden-set
* **Usefulness:** min. 1 konkretna rekomendacja/alert dziennie lub tygodniowo (bez “wodolejstwa”)
* **Coverage:** ≥ 90% dni z kompletem danych w danym miesiącu (w praktyce – target)

---

## 7. High-level rozwiązanie (MVP)

### Jednozdaniowy opis

**Wejście (daily entry) → walidacja → persist → metryki bazowe → KPI/flags → wykresy → eksport → (opcjonalnie) LLM narracja + Q&A**

### Artefakty output

* **Excel:** `exports/report_<yyyy-mm-dd>.xlsx`
* **PDF:** `exports/report_<yyyy-mm-dd>.pdf`
* **JSON:** `exports/analysis_<yyyy-mm-dd>.json`

---

## 8. Functional Requirements (FR)

| ID     | Nazwa                     | Priorytet       | Opis                                                                 | Kryteria akceptacji (Given/When/Then)                                                       |
| ------ | ------------------------- | --------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| FR-001 | Model danych “DailyEntry” | Must            | Zapis dzienny: waga, skład ciała, kcal in/out, notatka, źródło       | Given puste DB When dodam wpis Then wpis zapisany i widoczny w tabeli historii              |
| FR-002 | Walidacja i jednostki     | Must            | Zakresy (np. waga 30–200 kg), procenty 0–100, kcal ≥ 0               | Given błędna wartość When zapis Then błąd walidacji i brak zapisu                           |
| FR-003 | Edycja i usuwanie wpisu   | Must            | Poprawki danych z audytem (timestamp)                                | Given wpis istnieje When edytuję Then metryki przeliczają się deterministycznie             |
| FR-004 | Dashboard: wykres wagi    | Must            | Waga dzienna + 7/14-dniowy rolling avg                               | Given ≥ 14 dni danych When dashboard Then wykres + rolling avg                              |
| FR-005 | Dashboard: bilans energii | Must            | kcal_in, kcal_out_sport, net_balance                                 | Given dane kcal When dashboard Then pokazuje bilans dzienny i tygodniowy                    |
| FR-006 | Metryki bazowe składu     | Must            | Fat mass / lean mass (jeśli %tłuszczu dostępny)                      | Given waga + bf% When compute Then oblicza FM i FFM                                         |
| FR-007 | KPI engine (v1)           | Must            | Wylicza zestaw KPI (sekcja 11)                                       | Given dane 30 dni When compute Then KPI w JSON + UI                                         |
| FR-008 | Flags engine (v1)         | Must            | Red flags z progami i opisem                                         | Given stagnacja 14 dni When compute Then RF aktywny                                         |
| FR-009 | Prognoza 7/14/30 dni      | Must            | Forecast wagi (i opcjonalnie BF%) z przedziałem niepewności (prosto) | Given 60 dni When forecast Then generuje predykcję i zapisuje w JSON                        |
| FR-010 | Scenariusz “-200 kcal/d”  | Should          | Prosty what-if na bazie reguły energii                               | Given dane When what-if Then pokazuje delta prognozy                                        |
| FR-011 | Eksport Excel             | Must            | Tabele: daily, weekly, KPI, flags, forecast                          | Given dane When export Then plik xlsx z zakładkami                                          |
| FR-012 | Eksport PDF               | Must            | 1–3 strony: wykresy + podsumowanie KPI/flags                         | Given dane When export Then PDF generuje się bez chmury                                     |
| FR-013 | Eksport JSON kontrakt     | Must            | `analysis.json` wg kontraktu (sekcja 12)                             | Given dane When export Then JSON waliduje się schemą                                        |
| FR-014 | Import CSV (manual)       | Could (MVP+)    | Wczytanie CSV o znanym formacie                                      | Given CSV When import Then mapuje i waliduje rekordy                                        |
| FR-015 | LLM narracja lokalna      | Should          | Krótki komentarz + rekomendacje wyłącznie na policzonych metrykach   | Given compute done When “Generate summary” Then tekst nie zawiera nowych liczb spoza inputu |
| FR-016 | Q&A nad danymi            | Could           | Chat: pytania typu “co pogorszyło trend?” (RAG z tabel)              | Given dane When pytam Then odpowiedź cytuje metryki i okres                                 |
| FR-017 | Benchmark LLM na DGX      | Could           | Tokens/s, latency, koszt jakościowy                                  | Given model lokalny When benchmark Then zapis wyników do `benchmarks.json`                  |
| FR-018 | Backup/restore            | Should (Phase2) | Kopia DB + exports                                                   | Given backup When restore Then stan identyczny                                              |
| FR-019 | Konfiguracja celów        | Must            | Cel wagi, termin, progi flag                                         | Given ustawienia When compute Then KPI/flags używają konfiguracji                           |
| FR-020 | Tryb “no-network”         | Must            | Aplikacja nie wymaga internetu; brak call-out                        | Given brak internetu When run Then działa w pełni (poza opcjonalnym pobraniem modelu)       |

---

## 9. Non-Functional Requirements (NFR) – mierzalne

* **Offline-first:** brak zależności runtime od internetu; domyślnie blokada egress (np. dokumentacja “run behind firewall”)
* **Determinism:** te same dane → identyczne wyniki KPI/flags/forecast (z kontrolą seed tam gdzie losowość)
* **Wydajność:** dashboard ≤ 2 s dla 365 dni, export xlsx ≤ 3 s, export pdf ≤ 5 s (na DGX Spark)
* **Test coverage (MVP):** min. 25 testów, w tym golden-set na metryki i eksport
* **Observability light:** logi bez danych wrażliwych; poziomy INFO/WARN/ERROR
* **Explainability:** każdy KPI i flag ma opis + formułę + okno czasowe
* **Bezpieczeństwo:** dane lokalne; rekomendowane szyfrowanie dysku; opcjonalnie szyfrowana DB w Phase 2

---

## 10. Minimalny „Semantic Layer”

### Metryki bazowe (v1)

* `bs_weight_kg`: masa ciała [kg], źródło: daily entry
* `bs_bodyfat_pct`: % tłuszczu [%], źródło: daily entry (opcjonalne)
* `bs_fat_mass_kg`: tłuszcz [kg] = `weight_kg * bodyfat_pct`
* `bs_lean_mass_kg`: beztłuszczowa [kg] = `weight_kg - fat_mass_kg`
* `cal_in_kcal`: kalorie spożyte [kcal], źródło: daily entry
* `cal_out_sport_kcal`: kalorie wydatkowane sport [kcal], źródło: daily entry
* `cal_net_kcal`: bilans netto [kcal] = `cal_in_kcal - cal_out_sport_kcal`
* `bs_weight_7d_avg_kg`: średnia 7d [kg]
* `cal_net_7d_avg_kcal`: średnia 7d [kcal]

### Zasady mapowania

* Wszystko zapisujemy jako **wartości dzienne** z datą (`date` = dzień pomiaru)
* Jeśli brak bf% → metryki FM/FFM = null (nie imputujemy w MVP)
* Rolling averages liczone tylko, gdy okno ma ≥ 70% pokrycia danych

---

## 11. Minimalny zestaw KPI + red flags

### KPI (10–15)

1. **KPI_Weight_Trend_7d (kg/tydz.)** – trend wagi na bazie 7d avg
2. **KPI_Weight_Change_30d (kg)** – zmiana 30 dni (avg vs avg)
3. **KPI_BF_Change_30d (pp)** – zmiana bf% (jeśli dostępne)
4. **KPI_FatMass_Change_30d (kg)** – zmiana FM (jeśli dostępne)
5. **KPI_NetCalories_7d (kcal/d)** – średni bilans netto 7 dni
6. **KPI_Intake_7d (kcal/d)** – średnie kcal in 7 dni
7. **KPI_Sport_7d (kcal/d)** – średnie kcal sport 7 dni
8. **KPI_Consistency_Coverage_30d (%)** – % dni z kompletem danych
9. **KPI_Volatility_Weight_14d (std kg)** – zmienność wagi (retencja/wahania)
10. **KPI_Streak_Days** – ile dni z rzędu z wpisem
11. **KPI_Goal_ETA (days)** – estymacja dni do celu (prosta)
12. **KPI_Adherence_Score (0–100)** – heurystyka (coverage + stabilność + bilans)

### Red flags (8–12)

1. **RF-001_MissingData_7d** – >3 brakujące dni w 7 dniach
2. **RF-002_MissingCalories_7d** – brak kcal_in/out w większości dni
3. **RF-003_Plateau_14d** – trend wagi ~0 przez 14 dni mimo ujemnego bilansu
4. **RF-004_Volatility_Spike** – skok std wagi (np. > 2× mediany 60d)
5. **RF-005_TooAggressive_Deficit** – średni bilans < -1000 kcal/d (heurystyka)
6. **RF-006_Sport_Zero_14d** – zero sport kcal przez 14 dni (jeśli plan zakłada ruch)
7. **RF-007_Inconsistent_Measurement** – pomiary o losowych godzinach / brak (Phase2)
8. **RF-008_BF_Outlier** – bf% skok > X pp dzień/dzień
9. **RF-009_Goal_Drift** – ETA rośnie przez 2 tygodnie
10. **RF-010_DataEntry_OutOfRange** – wartości spoza sensownych zakresów

---

## 12. Architektura i kontrakty (pod vibe coding)

### Komponenty (MVP – minimal)

* **UI:** Streamlit (`/app`)
* **Core:**

  * `storage` (SQLite/DuckDB)
  * `schemas` (Pydantic)
  * `kpi_engine`
  * `flags_engine`
  * `forecast_engine`
  * `exports` (xlsx/pdf/json)
* (Opcjonalnie) **LLM:** `llm_narration`, `qa_engine`

### DGX Spark leverage (praktycznie)

DGX Spark jest projektowany do lokalnego prototypowania, fine-tuningu i inference dużych modeli na biurku; NVIDIA podaje m.in. **128 GB unified memory** i możliwość uruchamiania modeli do **~200B parametrów** oraz wydajność rzędu **1 petaFLOP (FP4)**. ([NVIDIA][1])
Dokumentacja NVIDIA opisuje DGX Spark jako desktop do prototypowania/deploy/fine-tune na architekturze Grace Blackwell. ([NVIDIA Docs][2])
Datasheet wspomina gotowy stack (DGX OS na Ubuntu) i narzędzia typu PyTorch/Jupyter/Ollama jako typowy workflow. ([Aspen Systems Inc.][3])

### Kontrakt danych (analysis.json)

* `metadata`: wersja app, data eksportu, zakres dat, konfiguracja celu, wersje modeli (opcjonalnie)
* `metrics_base[]`: lista metryk bazowych (key, unit, value, date)
* `kpi[]`: (id, name, value, unit, window, explanation)
* `red_flags[]`: (id, severity, triggered, explanation, window, suggested_action)
* `forecast[]`: (target_metric, horizon_days, yhat[], yhat_low[], yhat_high[])
* `coverage`: kompletność danych + braki per pole

---

## 13. Repo structure + naming (Codex-friendly)

### Struktura repo (prosta)

* `/app/` – Streamlit UI
* `/core/` – logika (storage, engines, exports, llm)
* `/configs/` – progi KPI/flags, cele, schemy
* `/data/` – demo + golden (małe, sztuczne)
* `/tests/` – unit + golden + eksport
* `/docs/` – opis metryk, ADR-lite
* `/scripts/` – run/export/benchmark

### Naming

* Metryki: `bs_*`, `cal_*`
* Flags: `RF-###_*`
* Output: `analysis_<date>.json`, `report_<date>.xlsx`, `report_<date>.pdf`

---

## 14. DGX Spark leverage (mini)

* **Local LLM ON:** start od **Ollama** (najprościej), alternatywnie **vLLM** gdy będziesz chciał serwować model jako endpoint lokalny
* **GPU-first:** tam gdzie możliwe, preferuj inference na GPU; quantization (FP4/INT8/INT4) zgodnie z możliwościami stacku
* **Benchmark:** tokens/s, time-to-first-token, czas generacji “daily summary”
* **RAG/fine-tune:** dopiero Phase 3 (najpierw świetne metryki + guard-rails)

---

## 15. Compliance/RODO/offline (mini)

* Offline-first, brak chmury
* Logi bez danych wrażliwych (bez surowych wartości wagi/kcal)
* Retencja: dane trzymasz lokalnie; exporty w katalogu `exports/`
* Rekomendacja: szyfrowanie dysku / katalogu; Phase 2: szyfrowana DB

---

## 16. Definition of Done (DoD)

### DoD – MVP

* Wszystkie **Must FR** ukończone
* Golden set tests przechodzą
* Eksport **Excel + PDF + JSON** działa i jest deterministyczny
* README: instalacja + demo + przykładowe dane
* Krótkie nagranie ekranu (90–180 s) z: dodaniem wpisu → dashboard → eksport

---

## 17. Ryzyka i mitigacje

* **R1: Halucynacje LLM (liczby/wnioski)** → LLM tylko narracja na bazie “facts JSON”; walidacja, zakaz tworzenia nowych liczb, testy regresji jakościowej
* **R2: Słaba jakość danych (braki, outliery)** → coverage KPI + red flags + proste reguły outlierów
* **R3: Przeinwestowanie w ML za wcześnie** → MVP: prosta prognoza i twarde KPI; dopiero potem ulepszanie modelu
* **R4: Zbyt wolny PDF/wykresy** → caching + prosty rendering, limit zakresu domyślnego
* **R5: Zmiany w sprzęcie/stacku** → izolacja w `core/llm/` + `core/bench/` i feature flags

---

## 18. Iteracyjny plan pracy (blokami) + „Codex block prompts”

### Milestones (2h/4h)

* **Po 1 bloku:** repo + uruchamialny Streamlit “hello” + puste storage
* **Po 3 blokach:** daily entry + lista wpisów + minimalne metryki + 5 testów
* **Po 10 blokach:** KPI/flags + wykresy + eksport JSON + golden set
* **Po 20 blokach:** Excel+PDF export, prognoza 30d, LLM narracja z guard-rails

### Block Prompts (kopiuj do Claude Code)

**Blok 1 – prompt**

* Cel bloku: Zainicjalizować repo i uruchomić minimalny szkielet aplikacji Streamlit offline.
* Zmiany: `pyproject.toml`, `app/main.py`, `core/__init__.py`, `README.md`
* DoD bloku:

  * `streamlit run app/main.py` działa
  * prosta strona “DIET_APP v0.x”
  * brak zależności sieciowych
* Uruchom: `uv run streamlit run app/main.py` (lub odpowiednik)
* Testy: `pytest -q` (nawet jeśli 0 testów)
* Notatka: „Jeśli niepewne → wybierz najprostsze rozwiązanie”.

**Blok 2 – prompt**

* Cel bloku: Dodać storage + schemę DailyEntry i zapis/odczyt.
* Zmiany: `core/storage.py`, `core/schemas.py`, `app/pages/entry.py`, `tests/test_storage.py`
* DoD bloku:

  * zapis i odczyt wpisu z DB
  * walidacje Pydantic
  * min. 3 testy
* Uruchom: `streamlit run app/main.py`
* Testy: `pytest -q`

**Blok 3 – prompt**

* Cel bloku: Metryki bazowe + pierwszy wykres wagi i bilansu kcal.
* Zmiany: `core/metrics.py`, `core/kpi_engine.py` (stub), `app/pages/dashboard.py`, `tests/test_metrics_golden.py`
* DoD bloku:

  * rolling avg 7d dla wagi
  * bilans kcal dzienny
  * golden test na małym dataset
* Uruchom: `streamlit run app/main.py`
* Testy: `pytest -q`

*(kolejne bloki analogicznie: flags → forecast → eksport → LLM)*

---

## 19. Test Plan (MVP) – checklist (min. 15)

1. Dodanie wpisu z poprawnymi danymi → zapis w DB
2. Walidacja: waga < 0 → błąd i brak zapisu
3. Walidacja: bf% > 100 → błąd i brak zapisu
4. Edycja wpisu → metryki przeliczone deterministycznie
5. Usunięcie wpisu → dashboard aktualizuje się
6. Rolling avg 7d liczy się poprawnie (golden)
7. Bilans `cal_net_kcal` poprawny (golden)
8. KPI_Consistency_Coverage_30d poprawny
9. RF-001_MissingData_7d odpala się po brakach
10. RF-003_Plateau_14d odpala się na sztucznym dataset
11. Forecast generuje wynik o poprawnych długościach horyzontu
12. Export JSON waliduje się schemą
13. Export Excel zawiera wymagane zakładki i liczby zgodne z core
14. Export PDF renderuje się bez błędów i zawiera wykresy
15. “No-network mode”: uruchomienie bez internetu działa
16. LLM narracja: test “no-new-numbers” (nie pojawiają się liczby spoza facts)
17. LLM narracja: spójność z KPI/flags (wymienia te same wnioski)
18. Regresja: ten sam dataset → identyczny JSON (snapshot)

---

## 20. Open Questions (min. 10)

1. Jak dokładnie chcesz liczyć **TDEE** (czy w ogóle w MVP), skoro masz tylko kcal sport + brak stałego “kcal out”?
2. Czy priorytetem jest **waga**, czy **fat mass / bf%** (jeśli bf% będzie niestabilny)?
3. Czy wpis dzienny ma być “rano na czczo” jako standard (wpływ na outliery)?
4. Jakie dokładnie pola składu ciała chcesz (woda, mięśnie, visceral fat)?
5. Czy chcesz obsługę wielu źródeł (waga A / waga B)?
6. Jakie progi dla “zbyt agresywnego deficytu” uznajesz za sensowne?
7. Czy eksport ma być “tydzień ISO” czy tygodnie kalendarzowe?
8. Czy w LLM chcesz ton: “coach” czy “analityk CFO”?
9. Jakie modele lokalne planujesz używać (rozmiar/język PL/EN)?
10. Czy dane mają być przechowywane jako pojedyncza DB, czy wersjonowane snapshotami?
11. Czy chcesz możliwość tagowania dni (choroba, podróż, alkohol, brak snu)?
12. Jak ważne jest porównanie “okres do okresu” (M/M, W/W)?

---

## 21. Assumptions (min. 10)

1. Dane będziesz wpisywał **codziennie** (docelowo coverage ≥ 90%).
2. W MVP dane są głównie **manualne** (integracje dopiero Phase 2).
3. Aplikacja działa lokalnie na DGX Spark i nie wymaga chmury.
4. Priorytetem jest **deterministyczna analityka**, nie “fancy AI”.
5. bf% bywa szumne → nie robimy agresywnej imputacji w MVP.
6. LLM jest **opcjonalny** i nie może zmieniać liczb ani wyciągać “medycznych” wniosków.
7. Dataset będzie mały (setki–tysiące dni), więc prosty storage i obliczenia wystarczą.
8. Eksport Excel/PDF jest kluczowy do “przeglądu CFO”.
9. Forecast w MVP ma być “wystarczająco dobry”, a nie naukowo perfekcyjny.
10. Sprzęt DGX Spark ma wystarczającą pamięć i moc, by uruchamiać lokalne modele (w tym większe) oraz stack dev; to jest jedna z głównych przewag projektu. ([NVIDIA][1])

---

Jeśli chcesz, mogę od razu dopisać: **konkretną listę pól dziennych (schema DailyEntry v1)** + przykładowy **golden dataset (30 dni)** + gotowe **progi KPI/flags** pod Twój cel 75 kg (żeby Claude Code od razu miał “twarde” liczby do implementacji).

[1]: https://www.nvidia.com/en-us/products/workstations/dgx-spark/?utm_source=chatgpt.com "A Grace Blackwell AI supercomputer on your desk | NVIDIA DGX Spark"
[2]: https://docs.nvidia.com/dgx/dgx-spark/hardware.html?utm_source=chatgpt.com "Hardware Overview — DGX Spark User Guide - NVIDIA Documentation Hub"
[3]: https://www.aspsys.com/wp-content/uploads/2025/05/nvidia-dgx-spark-datasheet.pdf?utm_source=chatgpt.com "workstation-datasheet-dgx-spark-gtc25-spring-nvidia-us-3716899-web"
