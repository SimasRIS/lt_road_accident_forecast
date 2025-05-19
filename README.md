# Lietuvos kelių eismo įvykių analizė ir prognozė

Šiame projekte analizuojame Lietuvos kelių eismo įvykių duomenis per dešimties metų laikotarpį (2013–2023 m.), gautus iš oficialaus valstybinių duomenų portalo [data.gov.lt](http://data.gov.lt/). Pagrindinis dėmesys skiriamas LSTM (Long Short-Term Memory) neuroninio tinklo kūrimui, kuris, remdamasis istoriniais duomenimis ir nustatytais dėsningumais, prognozuos kasdienį eismo įvykių skaičių kiekvienoje Lietuvos savivaldybėje.

## Techniniai reikalavimai

- **Duomenų šaltinis:** žali JSON failai (`data/raw/ei_*.json`), sujungiami ir normalizuojami per `scripts/data_loading.py`
- **Duomenų valymas ir transformavimas:** `pandas` + `numpy` (`scripts/data_cleaning.py`)
- **Vizualizacijos:** `matplotlib` / `plotly` (`scripts/visualisation.py`, `scripts/map_visualisation.py`)
- **Modeliavimas:** LSTM neuroninis tinklas su `TensorFlow` / `Keras` (`model.py`)
- **Duomenų bazė:** lentelių kūrimas ir įrašymas per `INIT_DB.py` (PostgreSQL/SQLite)

## 2. Tikslas ir darbo eiga

**Tikslas:**

- Išanalizuoti Lietuvos kelių eismo įvykių duomenis (2013–2023 m.), kad būtų atskleistos tendencijos pagal laiką (metus, mėnesius, dienas), vietovę (savivaldybes) ir įvykio tipą.
- Sukurti LSTM neuroninį tinklą, galintį prognozuoti kasdienį eismo įvykių skaičių savivaldybėse.

**Darbo eiga:**

1. **Duomenų įkėlimas ir normalizavimas** (`scripts/data_loading.py`) 
2. **Duomenų valymas ir transformavimas** (`scripts/data_cleaning.py`) 
3. **Eksploracinė analizė ir vizualizacijos**
    - bendros tendencijos (`scripts/visualisation.py`)
    - geografinis paskirstymas žemėlapyje (`scripts/map_visualisation.py`)
4. **LSTM modelio apmokymas ir vertinimas** (`model.py`) 
5. **Web aplikacijos kūrimas** („Flask“; `app.py`, `templates/`, `static/style.css`) 

## 3. Duomenų šaltiniai

**Pagrindinis duomenų rinkinys:**

- Žali JSON failai (`ei_YYYY_MM_DD.json`) gauti iš [data.gov.lt: Kelių eismo įvykių duomenys](https://data.gov.lt/datasets/509/) (2013–2023 m.)
- Visi JSON failai saugomi kataloge `data/raw/`

**Duomenų įkėlimas ir sujungimas:**

- Funkcija `load_all_jsons(folder_path)` (`scripts/data_loading.py`) nuskaito visus JSON failus iš `data/raw/`, juos normalizuoja į lenteles naudojant `pd.json_normalize` ir sujungia į vieną DataFrame.

**Svarbiausi duomenų laukai (iš `clean_events`)**

- `registrokodas` – unikalus įvykio identifikatorius
- `dataLaikas` – įvykio data ir laikas
- `savivaldybe` – įvykio vietovė
- `ivykioVieta` – koordinačių laukai: `platuma`, `ilguma`
- `rusis`, `schema1`, `schema2` – įvykio tipai ir kategorijos
- `dangosBukle`, `parosMetas`, `kelioApsvietimas`, `meteoSalygos` – aplinkos sąlygos
- `neblaivusKaltininkai`, `apsvaigeKaltininkai` – kaltininkų blaivumo būsena
- `dalyviuSkaicius`, `zuvusiuSkaicius`, `suzeistuSkaicius` – įvykio mastas ir pasekmės

**Papildomas duomenų sluoksnis – dalyviai:**

- Iš `eismoDalyviai` JSON masyvo išskiriami atskiri dalyviai (`clean_participants`) su laukais: `dalyvisId`, `kategorija`, `lytis`, `amzius`, `kaltininkas`

Duomenys saugomi CSV formatu (`data/processed/cleaned_events.csv`, `cleaned_participants.csv`) ir PostgreSQL/SQLite duomenų bazėje, kuri inicijuojama per `INIT_DB.py`.

## 4. Duomenų saugojimas ir struktūra

### Projekto katalogų struktūra

```
project-root/
├─ data/
│  ├─ raw/            # Originalūs JSON failai
│  ├─ split/          # Dalinti JSON fragmentai (data_split.py)
│  └─ processed/      # Apvalyti CSV failai
│     ├─ cleaned_events.csv
│     └─ cleaned_participants.csv
├─ models/            # Išsaugoti LSTM modeliai ir LabelEncoder
├─ scripts/          # Vykdomieji Python skriptai
│  ├─ data_loading.py  # JSON įkėlimas ir sujungimas
│  ├─ data_cleaning.py # Valymas ir CSV/DB išsaugojimas
│  ├─ grouping.py      # SQL/CLI grupavimai
│  ├─ visualisation.py # Grafikai (SMA, mirties analizė)
│  ├─ map_visualisation.py # Žemėlapių kūrimas
│  └─ model.py         # Duomenų agregavimas ir LSTM apmokymas
├─ sql/
│  └─ INIT_DB.py     # Duomenų bazės bei lentelių kūrimas
├─ templates/        # Flask HTML šablonai
├─ static/          # CSS ir kiti statiniai failai
└─ app.py           # Flask web serveris
```

### Duomenų bazė

- `sql/INIT_DB.py` sukuria dvi lenteles:
    - **events**: saugo kiekvieną eismo įvykį (rakto laukas `registrokodas`, laikas, vieta, tipai, sąlygos, koordinatės, metai/mėnuo/diena/valanda)
    - **participants**: informacija apie kiekvieną eismo įvykio dalyvį, susieta su `events` per `registrokodas`

### CSV eksportas

Skripte `data_cleaning.py` po duomenų valymo:

1. Filtruoti įrašai (2013–2023 m.) įrašomi į:
    - `data/processed/cleaned_events.csv`
    - `data/processed/cleaned_participants.csv`
2. Įvykiai ir dalyviai importuojami į duomenų bazę naudojant `save_to_db()` funkciją.

### Duomenų skaidymas modeliavimui

- Siekiant optimizuoti našumą, 2019-12-31 JSON failas buvo padalytas į dvi dalis (`ei_2019_12_31_part1.json`, `ei_2019_12_31_part2.json`) naudojant `data_split.py` skriptą.
- Visi fragmentai vėliau sujungiami į vieną DataFrame naudojant `load_all_jsons()` funkciją (`data_loading.py`).

Šis procesas užtikrina aiškią ir logišką duomenų grandinę tiek failų sistemoje, tiek duomenų bazėje – nuo originalių JSON failų per apdorotus CSV iki SQL lentelių.

## 5. Duomenų valymas ir paruošimas

Siekiant užtikrinti patikimą analizę ir modelio treniravimą, skriptas `scripts/data_cleaning.py` atlieka šiuos duomenų tvarkymo veiksmus:

### 5.1. Įvykių duomenų valymas (`clean_events`)

- **Stulpelių atranka:** išrenkami esminiai laukai – `registrokodas`, `dataLaikas`, vietos ir sąlygų atributai, dalyvių ir nukentėjusiųjų skaičiai, koordinatės bei kitos susijusios stulpelių grupės.
- **Datos ir laiko kolonos:** `dataLaikas` paverčiamas į `datetime` formatą, sukuriant papildomus laukus `metai`, `menuo`, `diena`, `valanda`.
- **Boolean žemėlapis:** tekstinės reikšmės „Taip"/„Ne" pakeičiamos į 1/0 stulpeliuose `neblaivusKaltininkai` ir `apsvaigeKaltininkai`.
- **Trūkstamų duomenų tvarkymas:** objektiniams stulpeliams priskiriama reikšmė `"Unknown"`, skaitiniams – `0`.

### 5.2. Dalyvių duomenų apvalymas (`clean_participants`)

- **Flatten:** `eismoDalyviai` masyvas performuojamas į atskirą lentelę su `registrokodas` identifikatoriumi.
- **Stulpelių atranka:** išsaugomi `dalyvisId`, `kategorija`, `lytis`, `amzius`, `girtumasPromilemis`, `kaltininkas` ir kiti svarbūs laukai.
- **Boolean konvertavimas:** `kaltininkas` paverčiamas į `True`/`False`.
- **Trūkstamų duomenų užpildymas:** taikoma ta pati metodika kaip `clean_events`.

### 5.3. Metų filtravimas

- Iš abiejų DataFrame'ų atrenkami tik 2013–2023 metų įrašai. Dalyvių duomenys išsaugomi tik tiems įvykiams, kurie išlieka po filtravimo.

### 5.4. CSV eksportas ir duomenų bazės paruošimas

- **CSV:** apdoroti duomenys išsaugomi į `data/processed/cleaned_events.csv` ir `cleaned_participants.csv` per pagrindinį skriptą (`if __name__ == "__main__": …`)
- **Duomenų bazė:** funkcija `save_to_db(events_df, participants_df)` sujungia su PostgreSQL/SQLite ir įrašo duomenis į `events` bei `participants` lenteles, užtikrindama duomenų vientisumą (`ON CONFLICT DO NOTHING`)

Šio proceso rezultatas – išvalytas ir chronologiškai apribotas duomenų rinkinys, tinkamas tiek analizei, tiek LSTM modelio apmokymui.

## 6. Eksploracinė analizė (EDA) ir grupavimas

### 6.1. EDA su pandas

Visą EDA logiką įgyvendina `scripts/grouping.py`:

- `group_by_year(events_df)` — įvykių skaičius pagal metus
- `group_by_municipality(events_df)` — įvykių skaičius pagal savivaldybę
- `group_by_event_type(events_df)` — įvykių skaičius pagal tipą
- `group_by_road_surface(events_df)` — įvykių skaičius pagal kelio dangos būklę
- Dalyvių grupavimas: pagal amžių, lytį, būseną, sąlygas ir vairavimo stažą

### 6.2. Interaktyvus CLI meniu

Failas `scripts/grouping.py` turi `main()` funkciją, kuri:

1. Įkelia apvalytus CSV failus (`data/processed/cleaned_events.csv` ir `cleaned_participants.csv`)
2. Atvaizduoja meniu su pasirinkimais (metai, savivaldybė, tipas, dangos būklė, dalyvių atributai)
3. Pagal vartotojo įvestį atvaizduoja atitinkamas grupavimo lenteles konsolėje

## 7. Interaktyvios vizualizacijos

Šiame projekte interaktyvias vizualizacijas kuriame su Plotly biblioteka ir pateikiame Flask web-aplikacijoje puslapyje `/visualisations`. Kiekviena diagrama sukuriama atskiroje funkcijoje, o jos aprašymą automatiškai generuoja AI modulis.

### 7.1. Žemėlapio vizualizacija

- **Modulis:** `scripts/map_visualisation.py`
- **Koordinačių transformacija:** LKS92 (EPSG:3346) → WGS84 (EPSG:4326) per `pyproj.Transformer`
- **Funkcijos:**
    - `load_map_data(path)` – nuskaito `cleaned_events.csv`, filtruoja 2013–2023 m. įrašus ir prideda `lon`/`lat` koordinates.
    - `make_scatter_map(df, category=None, year=None)` – naudoja Plotly Express `scatter_mapbox` įvykių atvaizdavimui, spalvina pagal `rusis` ir rodo papildomą informaciją (`savivaldybe`, `dataLaikas`).
    - `create_map_div(csv_path, category, year)` – sukuria HTML `<div>` elementą su įterpiamu kodu.

### 7.2. Laiko eilių ir stulpelinės diagramos

Visos vizualizacijos apibrėžtos `scripts/visualisation.py`:

- **Slenkamasis vidurkis (SMA) prognozė:**
    - `forecast_accidents_sma(events_df)` – apskaičiuoja 3 metų SMA istoriniams duomenims (2013–2023) ir pratęsia prognozę iki 2026 m.
    - Naudoja Plotly Graph Objects (`go.Figure`, `go.Scatter`) su dviem kreivėmis: istoriniams duomenims ir prognozei su užbrūkšniuota sritimi.
- **Eismo įvykių pagal mėnesius diagrama:**
    - `accidents_by_month(events_df)` – stulpelinė diagrama, grupuojanti pagal `month` ir `metai`, su kasmetinių duomenų spalvinimu ir trimis raidėmis žymimais mėnesiais.
- **Mirties atvejų analizė:**
    - `analyze_deaths_by_gender_age_type(events_df, participants_df)` – trys stulpelinės diagramos, rodančios pasiskirstymą pagal lytį, amžiaus grupes ir įvykių tipus (2017–2023).
    - `analyze_deaths_by_weekday(events_df, participants_df)` – stulpelinė diagrama, vaizduojanti mirčių pasiskirstymą pagal savaitės dienas.
    - `plotly_death_forecast(events_df, participants_df)` – SMA prognozė mirčių skaičiui 2024–2026 m., analogiška avarijų prognozei.

### 7.3. Interaktyvumas ir AI aprašymai

- Flask šablone `visualisations.html` vartotojas gali pasirinkti norimus grafinius elementus naudodamas žymimąsias varneles.
- Kiekvienai diagramai funkcija `describe_chart(fig, title)` iš `scripts/openai.py` sugeneruoja trumpą, aiškų aprašymą.

## 8. Prognozės modelis

Šiame skyriuje aprašoma LSTM (Long Short-Term Memory) neuroninio tinklo metodologija, pritaikyta eismo įvykių laiko eilučių analizei. Modelis sukurtas prognozuoti būsimus eismo įvykius, remiantis istoriniais duomenimis ir savivaldybių charakteristikomis.

### 8.1. Duomenų agregavimas ir kodavimas

- Funkcija `load_and_aggregate(data_path)` (`scripts/model.py`) atlieka pagrindinius duomenų paruošimo žingsnius: įkelia `cleaned_events.csv` failą, agreguoja kasdienį įvykių skaičių savivaldybėms, sukuria stulpelį `accident_count` įvykių skaičiavimui ir transformuoja savivaldybių pavadinimus į identifikatorius `mun_code` naudodama `LabelEncoder`.
- LabelEncoder objektas išsaugomas faile `models/label_encoder.joblib` vėlesniam naudojimui.

### 8.2. Sequence paruošimas

- Funkcija `prepare_sequence(agg_df, seq_len=30)` naudoja slankiojo lango metodą: kiekvienai savivaldybei sukuriamos sekos iš 30 dienų įvykių istorijos (`X_seq`) sekančios dienos įvykių skaičiaus prognozei (`y_seq`). Taip pat išsaugoma savivaldybės identifikatorių seka `mun_seq`.

### 8.3. Train–test duomenų skaidymas

- Duomenys chronologiškai padalinami į treniravimo ir testavimo rinkinius: paskutiniai 2 metai (nuo `max_date - 2 metai`) skiriami testavimui, ankstesni – treniravimui.
- Pritaikius chronologinį maskavimą, duomenų rinkiniai (X, y ir `mun_seq`) padalinami į treniravimo (`X_train`, `y_train`) ir testavimo (`X_test`, `y_test`) imtis.

### 8.4. Modelio architektūra

- Funkcija `build_lstm_model(num_muns, seq_len, emb_dim=8, lstm_units=64, l2_reg=1e-6, dropout_rate=0.2)` sukuria dviejų įėjimų neuroninį tinklą:
    1. **Seq input:** LSTM sluoksnis laiko eilučių duomenims apdoroti (`(seq_len, 1)` formos).
    2. **Municipality input:** Embedding sluoksnis (`input_dim=num_muns`, `output_dim=emb_dim`) savivaldybių charakteristikoms, sujungtas su Flatten sluoksniu.
    3. LSTM išvestis sujungiama su embedding transformacija, pereina per aktyvuotą Dense sluoksnį (`relu`), Dropout sluoksnį ir galutinį Dense sluoksnį dienos prognozei.
- Modelis kompiliuojamas naudojant vidutinės kvadratinės paklaidos (`mean_squared_error`) funkciją ir šakninę vidutinę kvadratinę paklaidą (`root_mean_squared_error`) tikslumui matuoti.

### 8.5. Treniravimas

- Modelio treniravimui naudojami šie callback'ai:
    - `EarlyStopping(monitor='val_root_mean_squared_error', patience=7, restore_best_weights=True)` – sustabdo treniravimą be progreso ir atkuria geriausius svorius.
    - `ReduceLROnPlateau(monitor='val_root_mean_squared_error', factor=0.5, patience=5)` – adaptuoja mokymosi greitį.
    - `ModelCheckpoint('models/lstm_accident_model.keras', save_best_only=True, monitor='val_root_mean_squared_error')` – išsaugo geriausią modelį.
- Treniravimas vykdomas su parinktais parametrais: `validation_split=0.2`, `epochs=20` ir `batch_size=32`.

### 8.6. Vertinimas ir išsaugojimas

- Baigus treniravimą, modelio tikslumas įvertinamas naudojant nepriklausomą testinį duomenų rinkinį:
    
    ```python
    loss, rmse = model.evaluate([X_test, mun_test], y_test, verbose=0)
    print(f"Test RMSE: {rmse:.3f}")
    ```
    
- Gautas testavimo RMSE: **1.423**
- Modelis išsaugomas faile `models/lstm_accident_model_final.keras` be optimizatoriaus.

### 8.7. Rezultatai ir tobulinimo galimybės

- **Test RMSE = 1.423** rodo, kad modelio vidutinis dienos prognozių nuokrypis nuo faktinių duomenų yra apie 1.4 avarijos.
- Siekiant pagerinti tikslumą, siūloma eksperimentuoti su:
    - Sekvencijų ilgiu (`seq_len`)
    - Embedding dimensija (`emb_dim`)
    - Skirtingomis architektūromis (pvz., Transformer laikinių eilučių modeliai)
    - Papildomų savybių įtraukimu (pvz., orų duomenys, eismo intensyvumas)

## 9. Web aplikacija

Šiame projekte sukūrėme Flask pagrindu veikiančią interneto aplikaciją (`app.py`), kuri leidžia interaktyviai peržiūrėti projektą, vizualizacijas, žemėlapį ir prognozes.

### 9.1. Aplikacijos konfigūracija

- **`app.py`** – pagrindinis servisas, kuriame:
    - Įkeliamas modelis (`lstm_accident_model_final.keras`) ir `LabelEncoder`
    - Nuskaitomi apdoroti duomenys iš CSV failų (`cleaned_events.csv`, `cleaned_participants.csv`)
    - Aplinka konfigūruojama per `.env` failą (FLASK_SECRET_KEY, OPENAI_API_KEY, duomenų bazės prisijungimai)
- **Šablonų ir statinių failų katalogai:**
    - `templates/` – HTML šablonai (`home.html`, `visualisations.html`, `predict.html`, `map.html`)
    - `static/style.css` – bendri puslapio stiliai

### 9.2. Puslapiai ir maršrutai

1. **`/home`**
    - Rodo projekto aprašymą, kurį generuoja AI modulis (`describe_project()`)
2. **`/visualisations`**
    - Leidžia rinktis įvairias vizualizacijas (įvykių pasiskirstymas pagal mėnesius, SMA prognozė, mirčių analizė)
    - Dinamiškai generuoja Plotly diagramas ir AI aprašymus (`describe_chart`)
3. **`/map`**
    - Interaktyvus žemėlapis su filtravimu pagal įvykio tipą ir metus
    - Naudoja `create_map_div()` funkciją iš `scripts/map_visualisation.py` ir Plotly Mapbox
4. **`/predict`**
    - Forma savivaldybės ir datos pasirinkimui
    - Paruošia 30 dienų seką ir prognozuoja vienos dienos įvykių skaičių naudojant LSTM modelį

### 9.3. Pritaikyti AI aprašymai

- AI moduliai (`scripts/openai.py`) generuoja:
    - Projekto aprašymą pagrindiniame puslapyje
    - Kiekvienos vizualizacijos paaiškinimus
- Jei `OPENAI_API_KEY` nenustatytas, aplikacija įrašo klaidą į žurnalą ir toliau veikia be AI funkcionalumo

Taip sukurtas visapusiškas ir interaktyvus vartotojo sąsajos sluoksnis, apjungiantis duomenų analizę, vizualizacijas, prognozes ir AI aprašymus.

## 10. Išvados ir tobulinimo galimybės

**Pagrindinės išvados:**

- Daugiausia eismo įvykių registruota didmiesčių savivaldybėse, o mažiausiai – atokesnėse zonose (funkcija `group_by_municipality` skripte `grouping.py`)
- Sezoniškumas svarbu: pavasario ir rudens mėnesiais įvykių skaičius išauga, žiemos mėnesiais – sumažėja (`accidents_by_month` grafikas `visualisation.py`)
- Savaitės cikle didžiausi pikai užfiksuoti pirmadieniais ir penktadieniais, mažiausiai – savaitgaliais (`analyze_deaths_by_weekday` funkcija `visualisation.py`)
- LSTM modelis pasiekė **Test RMSE = 1.423**, t.y. vidutinis prognozių nuokrypis ~1.4 įvykio per dieną, kas rodo pakankamą bendrų tendencijų atkūrimą, bet riboja smulkesnių pokyčių prognozes (`model.py`)

**Trūkumai:**

- Ne visi duomenys yra tikslūs - kartais trūksta tikslių vietų ar laiko, kada įvyko avarijos.
- Mūsų sukurtas modelis atsižvelgia tik į ankstesnių avarijų skaičių ir savivaldybes. Jis nevertina svarbių dalykų, pavyzdžiui, oro sąlygų ar kiek automobilių važiuoja keliuose.
- Modelio prognozės nėra labai tikslios, kai kalbame apie mažus skaičius - pavyzdžiui, sunku tiksliai nuspėti, ar konkrečią dieną įvyks viena ar dvi avarijos.

**Kaip galėtume patobulinti projektą:**

- **Daugiau duomenų:** Įtraukti papildomą informaciją, kuri padėtų geriau suprasti avarijas, pavyzdžiui:
    - Oro sąlygas (lietų, temperatūrą)
    - Kada vyksta svarbūs renginiai mieste
- **Geresni modeliai:** Išbandyti naujus ir pažangesnius būdus avarijų prognozavimui, kurie galėtų pateikti tikslesnius rezultatus.
- **Modelio tobulinimas:** Pagerinti esamo modelio veikimą keičiant įvairius nustatymus ir naudojant papildomus patikrinimo metodus.

## 12. Diegimo gidas

1. **Repo klonavimas**
Pirmiausia nukopijuokite GitHub repozitoriją:
    
    ```bash
    git clone <https://github.com/SimasRIS/lt_road_accident_forecast.git>
    ```
    
    ```bash
    cd lt_road_accident_forecast
    ```
    

1. **Priklausomybių įdiegimas**
    
    Įdiekite visas reikalingas bibliotekas:
    
    ```bash
    pip install -r requirements.txt
    ```
    
2. **Aplinkos kintamųjų sukonfigūravimas**
    
    Sukurkite naują failą pavadinimu ".env" pagrindiniame projekto aplanke ir įrašykite į jį reikalingus nustatymus:
    
    ```makefile
    OPENAI_API_KEY=<jūsų_openai_raktas>
    FLASK_SECRET_KEY=<jūsų_slaptasis_raktas>
    
    PG_USER=postgres
    PG_PASSWORD=<jūsų_slaptažodis>
    PG_HOST=localhost
    PG_PORT=5432
    DB_NAME=<jūsų_duomenų_bazės_pavadinimas>
    ```
    
3. **Duomenų bazės inicializavimas**
    
    Paleiskite programą, kuri sukurs duomenų bazės lenteles:
    
    ```bash
    python sql/INIT_DB.py
    ```
    
4. **Duomenų paruošimas**
    
    Paruoškite ir sutvarkykite duomenis:
    
    ```bash
    python scripts/data_cleaning.py
    ```
    
5. **Modelio (per)treniravimas** *(nebūtina)*
    
    Jei norite iš naujo apmokyti modelį arba išbandyti skirtingus nustatymus:
    
    ```bash
    python scripts/model.py
    ```
    
6. **Web aplikacijos paleidimas**
    
    Įjunkite programos serverį:
    
    ```bash
    flask run --host=0.0.0.0 --port=5000
    ```
    

Po šių veiksmų aplikacija bus pasiekiama adresu `http://localhost:5000/`.

**Autoriai:**

- Simas B. (https://github.com/SimasRIS)
- Justina B. ( https://github.com/JustinaFox)