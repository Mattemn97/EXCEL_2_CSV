# Excel → SQL (multi‑dialect) Generator

Uno script Python che **legge file Excel (.xlsx/.xls)** e genera automaticamente uno **script SQL** con:
- `CREATE TABLE` per ogni foglio
- `INSERT INTO` per tutte le righe, in **batch** per performance

Supporta più **dialetti SQL** (PostgreSQL, MySQL, SQLite, SQL Server) e include **inferenza dei tipi** (BOOLEAN/INT/DECIMAL/FLOAT/VARCHAR/TEXT), **sanitizzazione dei nomi** e **quoting** corretto per ciascun database.

> Progettato per flussi rapidi: basta indicare il file Excel, scegliere il dialetto, soglia `VARCHAR`, dimensione del batch e se la prima riga contiene intestazioni.

---

## Caratteristiche principali

- ✅ **Multi‑dialetto**: `postgres`, `mysql`, `sqlite`, `sqlserver`
- ✅ **Inferenza robusta dei tipi**:
  - `BOOLEAN` (true/false, t/f, y/n, yes/no, 0/1)
  - `INT`
  - `DECIMAL(p,s)` con stima **precisione** e **scala**
  - `FLOAT` (notazione scientifica)
  - `VARCHAR(n)` / `TEXT` (`NVARCHAR(n)` / `NVARCHAR(MAX)` su SQL Server)
- ✅ **Quoting dei nomi** in base al dialetto:
  - Postgres/SQLite: `"nome"`
  - MySQL: `` `nome` ``
  - SQL Server: `[nome]`
- ✅ **Sanitizzazione nomi** di colonne e tabelle:
  - Rimozione caratteri non validi, sostituzione con `_`
  - Prefisso `_` se inizia con cifra
  - Condensazione `_`
  - Deduplica: `col`, `col_1`, `col_2`, …
- ✅ **INSERT in batch** (default: 1000 righe per statement)
- ✅ **Progress bar** con `tqdm`
- ✅ **Gestione NULL, escape di apici nelle stringhe (‘ → ‘’)**
- ✅ **Supporto fogli multipli**: un `CREATE TABLE` e INSERT per ciascun foglio

---

## Requisiti

- **Python 3.9+** (consigliato 3.10/3.11)
- Pacchetti:
  - `pandas`
  - `openpyxl` (per `.xlsx`)
  - `xlrd` (per `.xls`)
  - `tqdm`

### Installazione

```bash
python -m venv .venv
source .venv/bin/activate        # su Windows: .venv\Scripts\activate
pip install -U pandas openpyxl xlrd tqdm
```

*(Facoltativo) crea un `requirements.txt`:*

```text
pandas
openpyxl
xlrd
tqdm
```

---

## Utilizzo

Lo script è **interattivo**: avvia e rispondi alle domande.

```bash
python excel_to_sql.py
```

**Prompt di esempio:**

```
👉 Inserisci il percorso completo del file .xlsx/.xls: /percorso/dati.xlsx
👉 Dialetto SQL (postgres/mysql/sqlite/sqlserver) [postgres]: mysql
👉 Soglia VARCHAR(n) [255]: 200
👉 Dimensione batch INSERT [1000]: 500
👉 La prima riga contiene intestazioni? (s/n) [s]: s
```

**Output generato:**

```
/percorso/dati_mysql.sql
```

Nella stessa cartella dell’Excel, con il nome `<nomefile>_<dialect>.sql`.

---

## Esempio di output

### CREATE TABLE (MySQL)

```sql
CREATE TABLE `vendite` (
    `id` INT,
    `prodotto` TEXT,
    `quantita` INT,
    `prezzo_unitario` DECIMAL(10,2),
    `attivo` TINYINT(1)
);
```

### INSERT in batch

```sql
INSERT INTO `vendite` (`id`, `prodotto`, `quantita`, `prezzo_unitario`, `attivo`) VALUES
(1, 'Bulloni', 100, 0.25, 1),
(2, 'Rondelle', 50, 0.10, 0),
(3, 'Viti', 120, 0.30, 1);
```

---

## Come funziona (inferenze e regole)

### Dialetti e mappature di tipo

- **BOOLEAN**:  
  - `postgres`: `BOOLEAN` (valori `TRUE`/`FALSE`)  
  - `mysql`: `TINYINT(1)` (valori `1`/`0`)  
  - `sqlite`: `INTEGER` (valori `1`/`0`)  
  - **sqlserver**: `BIT` (valori `1`/`0`)
- **INT**:
  - `postgres/sqlite`: `INTEGER`
  - `mysql`: `INT`
  - **sqlserver**: `INT`
- **FLOAT**:
  - `postgres`: `DOUBLE PRECISION`
  - `mysql`: `DOUBLE`
  - `sqlite`: `REAL`
  - **sqlserver**: `FLOAT`
- **DECIMAL/NUMERIC**:
  - `postgres/sqlite`: `NUMERIC(p,s)`
  - `mysql`: `DECIMAL(p,s)`
  - **sqlserver**: `DECIMAL(p,s)`
- **TEXT/STRING**:
  - `postgres/sqlite`: `TEXT`
  - `mysql`: `TEXT`
  - `sqlserver`: `NVARCHAR(MAX)`  
  Se lunghezza massima `≤ soglia VARCHAR(n)`, usa `VARCHAR(n)` (o `NVARCHAR(n)` su SQL Server).

### Rilevamento BOOLEAN

Valori riconosciuti (anche come stringhe, ignorando spazi e maiuscole/minuscole):  
`true/false`, `t/f`, `y/n`, `yes/no`, `0/1`, `bool` Python.

### Inferenza numerica

- `INT`: tutti i valori sono interi (es. `1.0` ammesso se matematicamente intero)
- `FLOAT`: presente **notazione scientifica** (es. `1e-3`)
- `DECIMAL(p,s)`:
  - calcolo `p` (precisione) e `s` (scala) dal massimo numero di cifre
  - la **parte decimale** ignora **zeri finali** (`1.2300` ⇒ scala 2)
  - **limiti**: `p ≤ 38`, `s ≤ 18`  
- altrimenti, `VARCHAR(n)` o `TEXT` in base alla lunghezza massima

### Sanitizzazione e quoting identificatori

- rimozione caratteri non `[a-zA-Z0-9_]` ⇒ sostituiti con `_`
- prefisso `_` se l’identificatore inizia con cifra
- condensazione di `_` ripetuti
- se vuoto ⇒ `col`
- **deduplica** automatica: `nome`, `nome_1`, `nome_2`, …
- **quoting**:
  - `postgres/sqlite`: `"nome"`
  - `mysql`: `` `nome` ``
  - `sqlserver`: `[nome]`

### Gestione dei dati

- `NULL` per celle vuote / non convertibili
- stringhe **escape** `'` ⇒ `''`
- nessuna conversione di date/tempi (volutamente esclusa)

---

## Opzioni interattive

- **Dialetto SQL**: `postgres/mysql/sqlite/sqlserver` (default: `postgres`)
- **Soglia `VARCHAR(n)`**: default `255`  
  Se la lunghezza massima trovata supera la soglia, usa `TEXT` (o `NVARCHAR(MAX)` per SQL Server).
- **Batch size**: default `1000`  
  Numero di righe per ciascun `INSERT` (migliora performance).
- **Prima riga come intestazioni**: `s/n` (default: `s`)  
  Se `n`, le colonne saranno `col_1`, `col_2`, …

---

## Limitazioni note

- ❌ **Nessun parsing DATE/TIMESTAMP** (intenzionale)
- ❌ **Nessuna definizione di PK/Unique/Index/FK** (schema minimale)
- ⚠️ **Valori stringa numerici**: se non convertibili ⇒ `NULL`
- ⚠️ **Zeri a sinistra** in colonne testuali numeriche possono perdersi se convertite a numeri
- ⚠️ **Tipi testo**: su SQL Server si usa `NVARCHAR(MAX)` come testo “illimitato”
- ⚠️ **Performance e memoria**: per file Excel molto grandi, l’uso di batch e `tqdm` aiuta, ma il caricamento dei fogli avviene in memoria

---

## Compatibilità Excel

- `.xlsx` letto con **openpyxl**
- `.xls` letto con **xlrd**
- Fogli vuoti vengono **saltati**
- Se **niente intestazioni**, le colonne diventano `col_1`, `col_2`, …

---

## Struttura consigliata della repo

```
.
├── excel_to_sql.py
├── README.md
├── requirements.txt
└── examples/
    └── dati_di_esempio.xlsx
```

---

## Troubleshooting

- **Errore dialetto non valido**: assicurati di digitare esattamente uno tra `postgres/mysql/sqlite/sqlserver`
- **Errore su librerie Excel**: installa `openpyxl` (xlsx) o `xlrd` (xls)
- **Colonne duplicate**: lo script le deduplica automaticamente (`nome`, `nome_1`, …)
- **Valori testuali con apostrofi**: vengono correttamente escapati (`O'Brien` ⇒ `'O''Brien'`)
- **Numeri in notazione scientifica**: verranno trattati come `FLOAT`

---

## Contribuire

- Fai una **fork**
- Crea una branch: `feature/nome-feature`
- Aggiungi test e documentazione
- Apri una **pull request**

Idee per estensioni:
- Supporto `DATE/TIMESTAMP` con euristiche e/o formati configurabili
- Generazione automatica di **PK** o colonne `IDENTITY/SERIAL`
- Opzione **CLI non interattiva** (argomenti da riga di comando)
- Supporto a **CSV** e altri formati di input

---

## Licenza

Scegli una licenza (es. **MIT** o **Apache-2.0**). Aggiorna questa sezione con il testo ufficiale.

---

## Avvio rapido (TL;DR)

```bash
# 1) Installazione
pip install -U pandas openpyxl xlrd tqdm

# 2) Esecuzione
python excel_to_sql.py

# 3) Output
#   <cartella dell'Excel>/<nomefile>_<dialetto>.sql
```
