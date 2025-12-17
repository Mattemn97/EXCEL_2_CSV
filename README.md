# 🃏 Generatore di Flashcard Stampabili (Fronte/Retro)
Script Python per creare flashcard stampabili fronte-retro a partire da un file CSV.
Pensato per essere facile da usare, completamente personalizzabile e con una procedura guidata passo-passo da terminale.

## ✨ Funzionalità principali
- 🧭 Interfaccia guidata passo-passo da terminale
- 📐 Scelta del formato pagina (A0–A6)
- 🧮 Calcolo automatico del layout (righe, colonne, carte per pagina)
- 📝 Supporto CSV con intestazioni flessibili
- 🔄 Generazione automatica di fronte e retro specchiati
- 📊 Barra di progresso con tqdm
- 🖋️ Personalizzazione del font principale e dei tag
- 🧩 Possibilità di unione automatica in un singolo PDF finale

## 📂 Struttura del CSV
Il file CSV deve avere come delimitatore il punto e virgola (;) e deve contenere almeno le colonne per i due lati della carta.

Esempio:
```c
Lato A;Lato B;Tag
Ha salutato qualcuno che non lo stava salutando;6;Errori e figuracce
Ha risposto “anche a te” dopo un “buon appetito” del cameriere;1;Errori e figuracce
Ha riso a una battuta che non era una battuta;1;Errori e figuracce
```

Le intestazioni possono anche chiamarsi Side A, Side B, A, B, Etichetta, Label, ecc.
Lo script riconosce automaticamente le varianti più comuni.


Installa le dipendenze con:
```bash
pip install reportlab PyPDF2
```

## 📄 Formato del file CSV
Il file flashcards.csv deve contenere tre colonne separate da (;) e deve contenere almeno le colonne per i due lati della carta.

```csv
Lato A;Lato B;Tag
Che cos'è un algoritmo?;Una sequenza finita di istruzioni...;Informatica
Capitale della Francia?;Parigi;Geografia
```

## ⚙️ Installazione
Assicurati di avere Python 3.7+ installato, poi installa le dipendenze:
```bash
pip install reportlab tqdm PyPDF2
```

Clona o scarica questo repository, quindi esegui lo script:
```bash
python3 flashcard_generator.py
```

## 🧭 Utilizzo (modalità guidata)

Avvia lo script e segui le istruzioni nel terminale.

La procedura prevede i seguenti passaggi:
1. Percorso CSV → seleziona il file con le carte.
2. Formato pagina → scegli tra A0–A6.
3. Dimensioni carte → inserisci larghezza e altezza (cm).
4. Dimensione font → imposta la grandezza del testo principale.
5. Anteprima impostazioni → visualizza il layout calcolato.
6. Generazione → conferma per creare i PDF fronte e retro.

Al termine troverai:
- flashcards_fronte.pdf
- flashcards_retro.pdf
- flashcards.pdf (versione combinata fronte-retro)

# 📊 Esempio di output
``` yaml
📋 Anteprima impostazioni:
   • Formato pagina: A4 (21.0x29.7 cm)
   • Dimensione carta: 6.0x4.0 cm
   • Margini: 1.0x2.0 cm, gap 0.5 cm
   • Layout: 3 colonne x 5 righe = 15 carte per pagina
   • Font principale: 11 pt, tag: 10 pt
   • Numero carte totali: 60 → 4 pagine circa
```
Durante la generazione verrà mostrata una barra di progresso in tempo reale.


# 📦 Output finale
Lo script produce:
- ✅ flashcards_fronte.pdf – il lato A di ogni carta
- ✅ flashcards_retro.pdf – il lato B, specchiato per stampa corretta
- ✅ flashcards.pdf – versione combinata (fronte + retro intercalati)

🧠 Suggerimenti

- Stampa fronte-retro su lato corto per allineare perfettamente le carte.
- Usa carta spessa (150–200 g/m²) per un risultato migliore.
- Se vuoi carte più piccole o più grandi, modifica larghezza/altezza nella procedura guidata.
- I tag appaiono in basso a destra, in corsivo, utili per categorizzare le carte.

