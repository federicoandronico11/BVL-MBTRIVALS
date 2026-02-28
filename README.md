# 🏐 Beach Volley Tournament Manager Pro

**Streamlit app per la gestione di tornei di beach volleyball con stile FC26 Ultimate Team.**

---

## 📦 Struttura del Progetto

```
beach_volley/
├── app.py                   # Entry point principale, routing tra le pagine
├── data_manager.py          # Logica dati, state, bracket, overall FIFA
├── fase_setup.py            # Setup torneo: atleti, squadre, configurazione
├── fase_gironi.py           # Fase gironi: partite, classifiche, modalità
├── fase_eliminazione.py     # Bracket playoff con semifinali + finali 3°/4° e 1°/2°
├── fase_proclamazione.py    # Proclamazione vincitori, ranking globale, carriera
├── ranking_page.py          # Carte giocatore stile FC26 (11 tier: Bronzo → GOAT)
├── segnapunti_live.py       # Segnapunti live con 8 stili e modalità libera
├── incassi.py               # Gestione pagamenti per squadra, storico, export PDF
├── ui_components.py         # CSS dark mode DAZN, header, match card, podio
├── theme_manager.py         # Sistema temi personalizzabili, scoreboard styles
├── requirements.txt         # Dipendenze Python
└── beach_volley_data.json   # Dati persistenti (auto-generato)
```

---

## 🚀 Installazione e Avvio

### Requisiti
- Python 3.9+
- pip

### Installazione

```bash
# Clona o scarica il progetto nella tua cartella
cd beach_volley

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'app
streamlit run app.py
```

L'app si aprirà automaticamente nel browser su `http://localhost:8501`.

---

## 🗺️ Navigazione

La sidebar contiene il menu principale con 7 sezioni:

| Icona | Sezione | Descrizione |
|-------|---------|-------------|
| ⚙️ | **Setup** | Crea atleti, forma squadre, configura il torneo |
| 🔵 | **Gironi** | Gestisci la fase a gironi o girone unico |
| ⚡ | **Eliminazione** | Bracket playoff con semifinali e finali |
| 🏆 | **Proclamazione** | Podio finale e ranking globale |
| 🏅 | **Profili / Carte** | Carte FC26 di tutti gli atleti |
| 🔴 | **Segnapunti Live** | Segnapunti in tempo reale |
| 💰 | **Incassi** | Gestione pagamenti e report PDF |
| 🎨 | **Personalizza** | Temi, colori, stili scoreboard |

---

## ⚙️ Setup Torneo

### 1. Configura il Torneo
- **Nome torneo** e **data**
- **Formato set**: Set Unico, Best of 3, Best of 5
- **Punteggio massimo**: 11, 15, 21, 25 punti
- **Modalità torneo**:
  - `Gironi + Playoff` — fase gironi seguita da bracket eliminazione
  - `Girone Unico` — tutti giocano tra loro, podio dalla classifica finale
  - `Doppia Eliminazione` *(in sviluppo)*

### 2. Aggiungi Atleti
- Inserisci nome e clicca **Aggiungi Atleta**
- Ogni nuovo atleta parte con **OVR 40** (tier Bronzo Raro)
- Gli attributi (attacco, difesa, muro, ricezione, battuta, alzata) si aggiornano dopo ogni torneo

### 3. Forma le Squadre
- Seleziona 2 atleti dalla lista e assegna un nome alla squadra
- Le squadre ghost (👻) possono essere aggiunte manualmente o automaticamente per bilanciare i gironi

### 4. Configurazione Gironi
- Numero di gironi: 1–8
- Squadre che passano per girone: 1–4
- Sistema qualificazione: prime classificate o classifica avulsa

> 💡 Se le squadre non si dividono esattamente, l'app aggiunge automaticamente squadre ghost che perdono sempre a tavolino (0-21).

---

## 🔵 Fase Gironi

### Modalità Gironi + Playoff
- Le squadre vengono divise nei gironi configurati
- Ogni partita si gioca (o si inserisce il risultato manualmente)
- La classifica in tempo reale mostra chi è qualificato (🟢)
- Al termine di tutti i gironi si genera il bracket playoff

### Modalità Girone Unico
- Tutte le squadre giocano tra loro
- Il podio viene estratto direttamente dalla classifica finale (1°, 2°, 3°)
- Nessuna fase eliminatoria

### Inserimento Risultati
Per ogni partita puoi:
- Inserire il punteggio manualmente nei campi set
- Usare il **Segnapunti Live** per giocare punto a punto

---

## ⚡ Fase Eliminazione (Playoff)

Il bracket si genera automaticamente dai qualificati dei gironi.

### Struttura
```
Quarti di Finale
      ↓
Semifinali
      ↓
┌─────────────────────┐
│  Finale 3°/4° Posto │  ← perdenti semifinali
│  Finale 1°/2° Posto │  ← vincitori semifinali
└─────────────────────┘
```

- Il **3° posto** è determinato da una partita dedicata (non dalla sconfitta in semifinale)
- Il bracket avanza automaticamente quando tutti i match del round sono confermati
- È possibile usare il Segnapunti Live anche per le partite di bracket

---

## 🏅 Profili & Carte FC26

Le carte dei giocatori evolvono automaticamente in base all'overall (OVR).

### 11 Tier di Carte

| OVR | Tier | Stile |
|-----|------|-------|
| 40–44 | **Bronzo Comune** | Bronzo opaco |
| 45–49 | **Bronzo Raro** | Bronzo lucido con effetto shine |
| 50–54 | **Argento Comune** | Argento satinato |
| 55–59 | **Argento Raro** | Argento riflettente, bordi azzurri |
| 60–64 | **Oro Comune** | Oro con bagliore statico |
| 65–69 | **Oro Raro** | Oro riflettente, shine animato |
| 70–74 | **Eroe** | Viola/nero, fulmine animato, nastri dorati |
| 75–79 | **IF (In Form)** | Nero premium, forma angolata |
| 80–84 | **Leggenda** | Bianco perlaceo, ali d'angelo SVG |
| 85–89 | **TOTY** | Blu reale + oro, ali argento, forma barocca |
| 90–94 | **TOTY Evoluto** | TOTY + viola, colonne doriche, fulmini |
| 95–99 | **GOAT** | Infernale, ali nere fiammanti, forma irregolare |

### Calcolo Overall
```
OVR = weighted_avg(attacco×1.3, difesa×1.2, muro×1.0, ricezione×1.0, battuta×0.9, alzata×0.6) + bonus_vittorie
```
- Bonus vittorie: +2 per ogni torneo vinto (max +10)
- Minimo 40, massimo 99

### Evoluzione Attributi
Dopo ogni torneo gli attributi aumentano automaticamente:
- 1° posto: **+3** per attributo
- 2° posto: **+2** per attributo
- 3° posto: **+1** per attributo

---

## 🔴 Segnapunti Live

### Modalità Torneo
- Seleziona la partita dal dropdown
- Usa i pulsanti **➕ PUNTO** e **➖ Annulla** per ogni squadra
- Il pallone 🏐 indica chi sta battendo
- Al termine clicca **📤 INVIA AL TABELLONE** per registrare il risultato

### Modalità Libera
- Disponibile anche prima che inizi il torneo
- Inserisci i nomi delle squadre e gioca liberamente
- I risultati non vengono salvati nel tabellone

### Gestione Set
- Il set si chiude automaticamente quando una squadra raggiunge il punteggio massimo con 2 punti di vantaggio
- In Best of 3 il 3° set è il tiebreak a 15 punti

---

## 💰 Incassi

### Torneo Corrente
- Imposta la quota di iscrizione per squadra
- Spunta le squadre che hanno pagato
- Inserisci importi personalizzati e note per ogni squadra
- Clicca **Salva Incassi** per persistere i dati

### Storico
- Tabella con tutti i tornei precedenti
- Grafico a barre degli incassi mensili

### Export PDF
- Genera un PDF completo con tabella pagamenti e totali
- Opzione per includere lo storico di tutti i tornei

---

## 🎨 Personalizzazione

Il sistema temi permette di modificare:
- **Colori**: accent principale, secondario, sfondo
- **Font**: display e body
- **Header style**: grande con gradiente, compatto, solo testo
- **Sidebar width**: compatta, normale, larga
- **Scoreboard style**: 8 preset tra cui DAZN Live, ESPN, Sky Sport, Neon Arena, ecc.
- **Banner torneo**: posizione e visibilità

---

## 💾 Persistenza Dati

I dati vengono salvati automaticamente in due file JSON nella cartella del progetto:
- `beach_volley_data.json` — squadre, atleti, tornei, bracket, ranking
- `beach_volley_incassi.json` — storico pagamenti

Il file `beach_volley_data.json` è compatibile tra versioni: i campi mancanti vengono auto-migrati con valori di default.

### Nuovo Torneo
Dalla sezione **Proclamazione → Nuovo Torneo**:
- Atleti e ranking vengono preservati
- Squadre, gironi, bracket vengono azzerati
- Si può ricominciare subito con gli stessi giocatori

---

## 🔧 Risoluzione Problemi

| Problema | Soluzione |
|----------|-----------|
| App non si avvia | Verifica `pip install -r requirements.txt` |
| Errore `KeyError` su bracket | Aggiorna `app.py` con la versione più recente (gestisce `bracket_extra`) |
| Carte non si aggiornano | Clicca **Trasferisci al Ranking** nella fase Proclamazione |
| Pagina Personalizza crasha | Usa `theme_manager.py` versione aggiornata con validazione widget |
| PDF non si genera | Installa reportlab: `pip install reportlab` |

---

## 📋 Dipendenze

```
streamlit>=1.32.0    # Framework UI
pandas>=2.0.0        # Tabelle e grafici
reportlab>=4.0.0     # Generazione PDF incassi
```

---

## 📝 Note Tecniche

- Le animazioni CSS delle carte richiedono un browser moderno (Chrome 90+, Firefox 88+, Safari 15+)
- Il `clip-path` per le forme avanzate (IF, Leggenda, GOAT) potrebbe non renderizzare correttamente su browser datati
- I dati JSON vengono salvati in locale; per uso multi-dispositivo considera un database esterno o un file su cloud storage condiviso

---

*Beach Volley Tournament Manager Pro — v2.0 con sistema carte FC26*
