"""
data_manager.py — Gestione persistenza Google Sheets v6
Nuovi atleti partono con overall 40 (bronzo_raro) anche senza tornei.
Salvataggio automatico su Google Sheets invece di file JSON locale.
"""
import json, os, random
import streamlit as st
from datetime import datetime
from pathlib import Path

DATA_FILE = "beach_volley_data.json"  # fallback locale se Sheets non disponibile

SHEET_ID = "180VldT6RUNEYAo-N4EVkJouzChFTGcdJe5c8RazFUEg"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def _get_gsheet():
    """Connessione al Google Sheet (cached per tutta la sessione)."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.warning(f"⚠️ Google Sheets non disponibile, uso file locale. ({e})")
        return None

def empty_state():
    return {
        "fase": "setup",
        "torneo": {
            "nome": "", "tipo_tabellone": "Gironi + Playoff",
            "formato_set": "Set Unico", "punteggio_max": 21,
            "data": str(datetime.today().date()),
            "tipo_gioco": "2x2",
            "usa_ranking_teste_serie": False,
            "min_squadre": 4,
            "num_gironi": 2,
            "squadre_per_girone_passano": 2,
            "sistema_qualificazione": "Prime classificate",
            "modalita": "Gironi + Playoff",
        },
        "atleti": [], "squadre": [], "gironi": [], "bracket": [],
        "ranking_globale": [], "vincitore": None,
        "simulazione_al_ranking": True,
        "podio": [],
    }

def _migrate(data):
    """Aggiunge campi mancanti per compatibilità tra versioni."""
    base = empty_state()
    for k, v in base.items():
        data.setdefault(k, v)
    t = data.get("torneo", {})
    if "tipo_gioco" not in t: t["tipo_gioco"] = "2x2"
    if "usa_ranking_teste_serie" not in t: t["usa_ranking_teste_serie"] = False
    if "min_squadre" not in t: t["min_squadre"] = 4
    if "num_gironi" not in t: t["num_gironi"] = 2
    if "squadre_per_girone_passano" not in t: t["squadre_per_girone_passano"] = 2
    if "sistema_qualificazione" not in t: t["sistema_qualificazione"] = "Prime classificate"
    if "modalita" not in t: t["modalita"] = "Gironi + Playoff"
    return data

# ─────────────────────────────────────────────────────────────────────────────
# SISTEMA PERSISTENZA A RIGHE CHIAVE-VALORE
# Il foglio Google Sheets ha due colonne: A=chiave, B=valore
# Ogni dato occupa una riga propria → nessuna cella supera mai 50k caratteri
# Struttura righe:
#   main_data          → dati torneo beach volley (senza immagini)
#   incassi            → dati incassi
#   cover:<tid>        → copertina torneo (una riga per torneo)
#   foto_atleta:<aid>  → foto atleta (una riga per atleta)
#   rivals_data        → dati giocatore Rivals
#   cards_db_meta      → carte Rivals senza foto
#   foto_card:<id>     → foto di una carta Rivals (una riga per carta)
#   draft_db_meta      → carte Draft/Limited senza foto
# ─────────────────────────────────────────────────────────────────────────────

import copy as _copy

def _sheet_read_all(sheet):
    """Legge tutte le righe e ritorna un dict {chiave: valore}."""
    try:
        rows = sheet.get_all_values()
        result = {}
        for row in rows:
            if len(row) >= 2 and row[0] and row[1]:
                result[row[0]] = row[1]
        return result
    except Exception:
        return {}


def _sheet_write(sheet, updates: dict):
    """
    Scrive un dict {chiave: valore} nel foglio.
    Aggiorna le righe esistenti, aggiunge quelle nuove.
    updates = { "main_data": "..json..", "cover:tp_123": "..b64.." }
    """
    if not updates:
        return
    try:
        rows = sheet.get_all_values()
        # Mappa chiave -> numero riga (1-based)
        key_to_row = {}
        for i, row in enumerate(rows, start=1):
            if row and row[0]:
                key_to_row[row[0]] = i

        # Prepara le celle da aggiornare o appendere
        to_update = []   # (row_num, key, value)
        to_append = []   # [key, value]

        for key, value in updates.items():
            if key in key_to_row:
                to_update.append((key_to_row[key], key, value))
            else:
                to_append.append([key, value])

        # Aggiorna celle esistenti in batch
        if to_update:
            cell_updates = []
            for row_num, key, value in to_update:
                cell_updates.append({
                    "range": f"A{row_num}:B{row_num}",
                    "values": [[key, value]]
                })
            sheet.batch_update(cell_updates)

        # Appendi nuove righe
        if to_append:
            sheet.append_rows(to_append, value_input_option="RAW")

    except Exception as e:
        raise e


def _save_local(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _strip_images_state(state):
    """Rimuove immagini dal state e le ritorna separate come dict {chiave: b64}."""
    s = _copy.deepcopy(state)
    imgs = {}
    for t in s.get("tornei_programmati", []):
        tid = t.get("id", "")
        if t.get("copertina_b64"):
            imgs[f"cover:{tid}"] = t["copertina_b64"]
            t["copertina_b64"] = None
    for a in s.get("atleti", []):
        aid = a.get("id", "")
        if a.get("foto_b64"):
            imgs[f"foto_atleta:{aid}"] = a["foto_b64"]
            a["foto_b64"] = None
    return s, imgs


def _restore_images_state(state, store):
    """Reinserisce immagini nel state leggendo dal dict del foglio."""
    for t in state.get("tornei_programmati", []):
        tid = t.get("id", "")
        k = f"cover:{tid}"
        if k in store:
            t["copertina_b64"] = store[k]
    for a in state.get("atleti", []):
        aid = a.get("id", "")
        k = f"foto_atleta:{aid}"
        if k in store:
            a["foto_b64"] = store[k]
    return state


def load_state():
    sheet = _get_gsheet()
    if sheet is not None:
        try:
            store = _sheet_read_all(sheet)
            val = store.get("main_data")
            if val:
                data = json.loads(val)
                data = _restore_images_state(data, store)
                return _migrate(data)
        except Exception as e:
            st.warning(f"⚠️ Errore lettura Sheets, uso file locale. ({e})")

    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _migrate(data)
    return empty_state()


def save_state(state):
    sheet = _get_gsheet()
    if sheet is not None:
        try:
            s_light, imgs = _strip_images_state(state)
            updates = {"main_data": json.dumps(s_light, ensure_ascii=False)}
            updates.update({k: v for k, v in imgs.items()})
            _sheet_write(sheet, updates)
            _save_local(state)
            return
        except Exception as e:
            st.warning(f"⚠️ Errore salvataggio Sheets, salvo in locale. ({e})")
    _save_local(state)


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER CAMPI E ORARI
# Calcola automaticamente campo e orario per ogni partita.
# Ogni set dura ~20 min. Le partite si distribuiscono sui campi disponibili.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime as _dt, timedelta as _td

def _minuti_per_partita(formato_set):
    """Stima durata partita in minuti in base al formato."""
    if formato_set == "Best of 3":
        return 60   # 3 set × 20 min
    if formato_set == "Best of 5":
        return 100  # 5 set × 20 min
    return 20       # Set Unico


def calcola_schedule(state):
    """
    Assegna campo e orario a tutte le partite non ancora confermate.
    Chiama questa funzione ogni volta che viene confermato un risultato
    per ricalcolare gli orari delle partite successive.
    """
    torneo = state.get("torneo", {})
    num_campi     = int(torneo.get("num_campi", 1))
    orario_inizio = torneo.get("orario_inizio", "09:00")
    formato_set   = torneo.get("formato_set", "Set Unico")
    data_str      = torneo.get("data", str(_dt.today().date()))
    durata        = _minuti_per_partita(formato_set)

    try:
        base_dt = _dt.strptime(f"{data_str} {orario_inizio}", "%Y-%m-%d %H:%M")
    except Exception:
        base_dt = _dt.now().replace(hour=9, minute=0, second=0, microsecond=0)

    # Raccoglie tutte le partite in ordine
    tutte = []
    for girone in state.get("gironi", []):
        for p in girone.get("partite", []):
            tutte.append(p)
    for p in state.get("bracket", []):
        tutte.append(p)
    for p in state.get("bracket_extra", []):
        tutte.append(p)

    # Dividi in confermate (usate per calcolare il tempo trascorso)
    # e non confermate (da schedulare)
    confermate     = [p for p in tutte if p.get("confermata")]
    non_confermate = [p for p in tutte if not p.get("confermata")]

    # Tieni il cursore orario per ogni campo
    # Partiamo dalla fine delle partite già confermate
    cursori = [base_dt] * num_campi

    # Avanza i cursori per le partite già confermate
    for p in confermate:
        campo = p.get("campo", 1)
        if 1 <= campo <= num_campi:
            idx = campo - 1
            orario_p = p.get("orario_schedulato", "")
            if orario_p:
                try:
                    p_dt = _dt.strptime(f"{data_str} {orario_p}", "%Y-%m-%d %H:%M")
                    fine = p_dt + _td(minutes=durata)
                    if fine > cursori[idx]:
                        cursori[idx] = fine
                except Exception:
                    cursori[idx] += _td(minutes=durata)
            else:
                cursori[idx] += _td(minutes=durata)

    # Assegna campo e orario alle partite non confermate
    for p in non_confermate:
        # Skip BYE
        if p.get("is_bye"):
            continue
        # Trova il campo disponibile prima (quello con cursore più basso)
        campo_idx  = cursori.index(min(cursori))
        orario_dt  = cursori[campo_idx]
        p["campo"]              = campo_idx + 1
        p["orario_schedulato"]  = orario_dt.strftime("%H:%M")
        cursori[campo_idx]     += _td(minutes=durata)

    return state


def new_atleta(nome, cognome=""):
    full_name = f"{nome} {cognome}".strip() if cognome else nome
    return {
        "id": f"a_{full_name.lower().replace(' ','_')}_{random.randint(1000,9999)}",
        "nome": full_name,
        "nome_proprio": nome,
        "cognome": cognome,
        "foto_b64": None,
        "stats": {
            "tornei": 0, "vittorie": 0, "sconfitte": 0,
            "set_vinti": 0, "set_persi": 0,
            "punti_fatti": 0, "punti_subiti": 0,
            "storico_posizioni": [],
            # Attributi di partenza al minimo (overall ~40)
            "attacco": 40,
            "difesa": 40,
            "muro": 40,
            "ricezione": 40,
            "battuta": 40,
            "alzata": 40,
        }
    }

def get_atleta_by_id(state, aid):
    for a in state["atleti"]:
        if a["id"] == aid:
            return a
    return None

def new_squadra(nome, atleta_ids, quota_pagata=0.0, is_ghost=False):
    return {
        "id": f"sq_{random.randint(10000,99999)}",
        "nome": nome, "atleti": atleta_ids,
        "punti_classifica": 0, "set_vinti": 0, "set_persi": 0,
        "punti_fatti": 0, "punti_subiti": 0, "vittorie": 0, "sconfitte": 0,
        "quota_pagata": quota_pagata,
        "is_ghost": is_ghost,
    }

def get_squadra_by_id(state, sid):
    for s in state["squadre"]:
        if s["id"] == sid:
            return s
    return None

def nome_squadra(state, sid):
    s = get_squadra_by_id(state, sid)
    return s["nome"] if s else "?"

def new_partita(sq1_id, sq2_id, fase="girone", girone=None):
    return {
        "id": f"p_{random.randint(100000,999999)}",
        "sq1": sq1_id, "sq2": sq2_id, "fase": fase, "girone": girone,
        "set_sq1": 0, "set_sq2": 0, "punteggi": [],
        "in_battuta": 1, "confermata": False, "vincitore": None,
    }

def simula_set(pmax, tie_break=False):
    limit = 15 if tie_break else pmax
    a, b = 0, 0
    while True:
        if random.random() > 0.5: a += 1
        else: b += 1
        if a >= limit or b >= limit:
            if abs(a - b) >= 2: return a, b
            if a > limit + 6 or b > limit + 6:
                return (a, b) if a > b else (b, a)

def simula_partita(state, partita):
    sq1 = get_squadra_by_id(state, partita["sq1"])
    sq2 = get_squadra_by_id(state, partita["sq2"])
    pmax = state["torneo"]["punteggio_max"]
    formato = state["torneo"]["formato_set"]

    if sq1 and sq1.get("is_ghost"):
        partita["punteggi"] = [(0, pmax)]
        partita["set_sq1"] = 0; partita["set_sq2"] = 1
        partita["vincitore"] = partita["sq2"]
        partita["confermata"] = True
        return partita
    if sq2 and sq2.get("is_ghost"):
        partita["punteggi"] = [(pmax, 0)]
        partita["set_sq1"] = 1; partita["set_sq2"] = 0
        partita["vincitore"] = partita["sq1"]
        partita["confermata"] = True
        return partita

    if formato == "Set Unico":
        p1, p2 = simula_set(pmax)
        partita["punteggi"] = [(p1, p2)]
        partita["set_sq1"] = 1 if p1 > p2 else 0
        partita["set_sq2"] = 1 if p2 > p1 else 0
    else:
        sets_1, sets_2, punteggi = 0, 0, []
        while sets_1 < 2 and sets_2 < 2:
            tie = (sets_1 == 1 and sets_2 == 1)
            p1, p2 = simula_set(pmax, tie_break=tie)
            punteggi.append((p1, p2))
            if p1 > p2: sets_1 += 1
            else: sets_2 += 1
        partita["punteggi"] = punteggi
        partita["set_sq1"] = sets_1; partita["set_sq2"] = sets_2
    partita["vincitore"] = partita["sq1"] if partita["set_sq1"] > partita["set_sq2"] else partita["sq2"]
    partita["confermata"] = True
    return partita

def aggiorna_classifica_squadra(state, partita):
    sq1 = get_squadra_by_id(state, partita["sq1"])
    sq2 = get_squadra_by_id(state, partita["sq2"])
    if not sq1 or not sq2: return
    s1v, s2v = partita["set_sq1"], partita["set_sq2"]
    p1_tot = sum(p[0] for p in partita["punteggi"])
    p2_tot = sum(p[1] for p in partita["punteggi"])
    sq1["set_vinti"] += s1v; sq1["set_persi"] += s2v
    sq2["set_vinti"] += s2v; sq2["set_persi"] += s1v
    sq1["punti_fatti"] += p1_tot; sq1["punti_subiti"] += p2_tot
    sq2["punti_fatti"] += p2_tot; sq2["punti_subiti"] += p1_tot
    if partita["vincitore"] == partita["sq1"]:
        sq1["vittorie"] += 1; sq1["punti_classifica"] += 3
        sq2["sconfitte"] += 1; sq2["punti_classifica"] += 1
    else:
        sq2["vittorie"] += 1; sq2["punti_classifica"] += 3
        sq1["sconfitte"] += 1; sq1["punti_classifica"] += 1


def _parse_storico_entry(entry):
    """
    Legge un entry dello storico_posizioni in modo backward-compatible.
    Formato vecchio: (nome, pos, n_sq)  oppure  (nome, pos)
    Formato nuovo:   dict con chiavi nome/pos/n_squadre/luogo/data/...
    Restituisce sempre un dict normalizzato.
    """
    if isinstance(entry, dict):
        return entry
    # Tupla legacy
    if len(entry) >= 3:
        return {"nome": entry[0], "pos": entry[1], "n_squadre": entry[2],
                "luogo": "", "data": "", "formato_set": "", "tipo": "",
                "tipo_gioco": "", "num_campi": 1, "punteggio_max": 21,
                "compagni": [], "set_vinti": 0, "set_persi": 0,
                "punti_fatti": 0, "punti_subiti": 0}
    return {"nome": entry[0], "pos": entry[1], "n_squadre": 8,
            "luogo": "", "data": "", "formato_set": "", "tipo": "",
            "tipo_gioco": "", "num_campi": 1, "punteggio_max": 21,
            "compagni": [], "set_vinti": 0, "set_persi": 0,
            "punti_fatti": 0, "punti_subiti": 0}

def trasferisci_al_ranking(state, podio):
    t = state["torneo"]
    nome_torneo  = t.get("nome", "Torneo")
    n_squadre    = len([sq for sq in state["squadre"] if not sq.get("is_ghost")])
    # Metadati ricchi del torneo — salvati nello storico per ranking/profili/carte/dashboard
    meta_torneo = {
        "nome":         nome_torneo,
        "luogo":        t.get("luogo", ""),
        "data":         t.get("data", ""),
        "formato_set":  t.get("formato_set", ""),
        "tipo":         t.get("modalita", t.get("tipo_tabellone", "")),
        "tipo_gioco":   t.get("tipo_gioco", "2x2"),
        "num_campi":    t.get("num_campi", 1),
        "orario":       t.get("orario_inizio", ""),
        "punteggio_max":t.get("punteggio_max", 21),
        "num_gironi":   t.get("num_gironi", 2),
        "n_squadre":    n_squadre,
    }
    atleti_aggiornati = set()
    for sq in state["squadre"]:
        if sq.get("is_ghost"): continue
        for aid in sq["atleti"]:
            atleta = get_atleta_by_id(state, aid)
            if not atleta or aid in atleti_aggiornati: continue
            s = atleta["stats"]
            s["set_vinti"] += sq["set_vinti"]; s["set_persi"] += sq["set_persi"]
            s["punti_fatti"] += sq["punti_fatti"]; s["punti_subiti"] += sq["punti_subiti"]
            atleti_aggiornati.add(aid)
    for pos, sq_id in podio:
        sq = get_squadra_by_id(state, sq_id)
        if not sq or sq.get("is_ghost"): continue
        # Compagno di squadra per questo torneo
        compagni = [get_atleta_by_id(state, aid) for aid in sq["atleti"]]
        for aid in sq["atleti"]:
            atleta = get_atleta_by_id(state, aid)
            if not atleta: continue
            s = atleta["stats"]
            s["tornei"] += 1
            # Storico ricco: dict con tutti i metadati + compagni
            comp_nomi = [c["nome"] for c in compagni if c and c["id"] != aid]
            entry_storico = {
                "nome":       nome_torneo,
                "pos":        pos,
                "n_squadre":  n_squadre,
                "luogo":      meta_torneo["luogo"],
                "data":       meta_torneo["data"],
                "formato_set":meta_torneo["formato_set"],
                "tipo":       meta_torneo["tipo"],
                "tipo_gioco": meta_torneo["tipo_gioco"],
                "num_campi":  meta_torneo["num_campi"],
                "punteggio_max": meta_torneo["punteggio_max"],
                "compagni":   comp_nomi,
                "set_vinti":  sq.get("set_vinti", 0),
                "set_persi":  sq.get("set_persi", 0),
                "punti_fatti":sq.get("punti_fatti", 0),
                "punti_subiti":sq.get("punti_subiti", 0),
            }
            s["storico_posizioni"].append(entry_storico)
            if pos == 1: s["vittorie"] += 1
            else: s["sconfitte"] += 1
            _aggiorna_attributi_fifa(atleta, pos)
    podio_atleti = {aid for _, sq_id in podio for aid in (get_squadra_by_id(state, sq_id) or {"atleti":[]})["atleti"]}
    for sq in state["squadre"]:
        if sq.get("is_ghost"): continue
        comp_nomi_sq = [get_atleta_by_id(state, a)["nome"] for a in sq["atleti"] if get_atleta_by_id(state, a)]
        for aid in sq["atleti"]:
            if aid not in podio_atleti:
                atleta = get_atleta_by_id(state, aid)
                if atleta:
                    comp_nomi = [c for c in comp_nomi_sq if c != atleta["nome"]]
                    atleta["stats"]["tornei"] += 1
                    atleta["stats"]["sconfitte"] += 1
                    atleta["stats"]["storico_posizioni"].append({
                        "nome":       nome_torneo,
                        "pos":        n_squadre // 2,
                        "n_squadre":  n_squadre,
                        "luogo":      meta_torneo["luogo"],
                        "data":       meta_torneo["data"],
                        "formato_set":meta_torneo["formato_set"],
                        "tipo":       meta_torneo["tipo"],
                        "tipo_gioco": meta_torneo["tipo_gioco"],
                        "num_campi":  meta_torneo["num_campi"],
                        "punteggio_max": meta_torneo["punteggio_max"],
                        "compagni":   comp_nomi,
                        "set_vinti":  sq.get("set_vinti", 0),
                        "set_persi":  sq.get("set_persi", 0),
                        "punti_fatti":sq.get("punti_fatti", 0),
                        "punti_subiti":sq.get("punti_subiti", 0),
                    })

def _aggiorna_attributi_fifa(atleta, posizione):
    s = atleta["stats"]
    boost = {1: 3, 2: 2, 3: 1}.get(posizione, 0)
    if boost == 0: return
    for attr in ["attacco","difesa","muro","ricezione","battuta","alzata"]:
        if attr in s:
            s[attr] = min(99, s[attr] + random.randint(0, boost))

def calcola_overall_fifa(atleta):
    """
    Calcola overall FIFA per un atleta.
    Nuovi atleti (0 tornei, attributi 40) → overall 40.
    """
    s = atleta["stats"]
    attrs = ["attacco","difesa","muro","ricezione","battuta","alzata"]
    vals = [s.get(a, 40) for a in attrs]
    pesi = [1.3, 1.2, 1.0, 1.0, 0.9, 0.6]
    weighted = sum(v * p for v, p in zip(vals, pesi)) / sum(pesi)
    vittorie = s.get("vittorie", 0)
    bonus = min(10, vittorie * 2)
    return min(99, max(40, int(weighted + bonus)))

def get_card_type(overall, tornei=0, vittorie=0):
    """
    Tier sistema v5 — allineato con ranking_page.get_card_style()
    40-44: bronzo_comune | 45-49: bronzo_raro
    50-54: argento_comune | 55-59: argento_raro
    60-64: oro_comune | 65-69: oro_raro
    70-74: eroe | 75-79: if_card | 80-84: leggenda
    85-89: toty | 90-94: toty_evoluto | 95-99: goat
    """
    if overall >= 95: return "goat"
    if overall >= 90: return "toty_evoluto"
    if overall >= 85: return "toty"
    if overall >= 80: return "leggenda"
    if overall >= 75: return "if_card"
    if overall >= 70: return "eroe"
    if overall >= 65: return "oro_raro"
    if overall >= 60: return "oro_comune"
    if overall >= 55: return "argento_raro"
    if overall >= 50: return "argento_comune"
    if overall >= 45: return "bronzo_raro"
    return "bronzo_comune"


TROFEI_DEFINIZIONE = [
    {
        "id": "principiante", "nome": "Principiante", "icona": "🏆",
        "descrizione": "Disputa il tuo primo torneo", "colore": "#cd7f32",
        "sfondo": "linear-gradient(135deg,#5C3317,#CD853F)",
        "rarità": "comune",
        "check": lambda s: s["tornei"] >= 1
    },
    {
        "id": "dilettante", "nome": "Dilettante", "icona": "🥋",
        "descrizione": "Disputa 5 tornei", "colore": "#a0a0a0",
        "sfondo": "linear-gradient(135deg,#555,#aaa)",
        "rarità": "comune",
        "check": lambda s: s["tornei"] >= 5
    },
    {
        "id": "esordiente", "nome": "Esordiente", "icona": "🥉",
        "descrizione": "Conquista 1 podio (top 3)", "colore": "#cd7f32",
        "sfondo": "linear-gradient(135deg,#8b4513,#cd7f32)",
        "rarità": "non comune",
        "check": lambda s: any(_parse_storico_entry(e)["pos"] <= 3 for e in s.get("storico_posizioni", []))
    },
    {
        "id": "esperto", "nome": "Esperto", "icona": "🎖️",
        "descrizione": "Vinci il tuo primo torneo", "colore": "#c0c0c0",
        "sfondo": "linear-gradient(135deg,#696969,#C0C0C0)",
        "rarità": "non comune",
        "check": lambda s: s["vittorie"] >= 1
    },
    {
        "id": "campione", "nome": "Campione", "icona": "🏅",
        "descrizione": "Vinci 3 tornei", "colore": "#ffd700",
        "sfondo": "linear-gradient(135deg,#8B6914,#FFD700)",
        "rarità": "raro",
        "check": lambda s: s["vittorie"] >= 3
    },
    {
        "id": "eroe", "nome": "Eroe", "icona": "⭐",
        "descrizione": "Vinci 5 tornei", "colore": "#ffd700",
        "sfondo": "linear-gradient(135deg,#B8860B,#FFD700,#B8860B)",
        "rarità": "raro",
        "check": lambda s: s["vittorie"] >= 5
    },
    {
        "id": "leggenda", "nome": "Leggenda", "icona": "👑",
        "descrizione": "Vinci 10 tornei", "colore": "#e040fb",
        "sfondo": "linear-gradient(135deg,#6A0DAD,#E040FB,#6A0DAD)",
        "rarità": "epico",
        "check": lambda s: s["vittorie"] >= 10
    },
    {
        "id": "olimpo", "nome": "Nell'Olimpo", "icona": "🌟",
        "descrizione": "Conquista 20 medaglie totali", "colore": "#00f5ff",
        "sfondo": "linear-gradient(135deg,#003366,#00c8ff,#003366)",
        "rarità": "leggendario",
        "check": lambda s: sum(1 for e in s.get("storico_posizioni", []) if _parse_storico_entry(e)["pos"] <= 3) >= 20
    },
    {
        "id": "iron_man", "nome": "Iron Man", "icona": "💪",
        "descrizione": "Vinci 50 set in carriera", "colore": "#ff6600",
        "sfondo": "linear-gradient(135deg,#8B2500,#FF6600,#8B2500)",
        "rarità": "raro",
        "check": lambda s: s.get("set_vinti", 0) >= 50
    },
    {
        "id": "cecchino", "nome": "Cecchino", "icona": "🎯",
        "descrizione": "Quoziente punti > 2.0 (min 10 set)", "colore": "#00ff88",
        "sfondo": "linear-gradient(135deg,#004422,#00FF88,#004422)",
        "rarità": "non comune",
        "check": lambda s: (s.get("punti_fatti", 0) / max(s.get("set_vinti", 0) + s.get("set_persi", 0), 1)) > 2.0 and (s.get("set_vinti", 0) + s.get("set_persi", 0)) >= 10
    },
    {
        "id": "veterano", "nome": "Veterano", "icona": "🦅",
        "descrizione": "Disputa 10 tornei", "colore": "#8888ff",
        "sfondo": "linear-gradient(135deg,#1a1a66,#8888FF,#1a1a66)",
        "rarità": "raro",
        "check": lambda s: s["tornei"] >= 10
    },
    {
        "id": "dominatore", "nome": "Dominatore", "icona": "🔥",
        "descrizione": "Win rate > 80% con almeno 5 tornei", "colore": "#ff4400",
        "sfondo": "linear-gradient(135deg,#660000,#FF4400,#660000)",
        "rarità": "epico",
        "check": lambda s: s["tornei"] >= 5 and (s["vittorie"] / s["tornei"] * 100) > 80
    },
]

def get_trofei_atleta(atleta):
    s = atleta["stats"]
    return [(t, t["check"](s)) for t in TROFEI_DEFINIZIONE]

def genera_gironi(squadre_ids, num_gironi=2, use_ranking=False, state=None):
    """
    Genera i gironi. Supporta girone unico (num_gironi=1).
    Gestisce automaticamente BYE con squadre ghost se il numero non è divisibile.
    """
    if use_ranking and state:
        from ranking_page import build_ranking_data
        try:
            ranking = build_ranking_data(state)
            ranking_ids = [a["id"] for a in ranking]
            def rank_key(sid):
                sq = get_squadra_by_id(state, sid)
                if not sq: return 9999
                for aid in sq["atleti"]:
                    for i, r in enumerate(ranking_ids):
                        if r == aid: return i
                return 9999
            squadre_ids = sorted(squadre_ids, key=rank_key)
        except:
            random.shuffle(squadre_ids)
    else:
        random.shuffle(squadre_ids)

    # Auto-BYE: se il numero di squadre non è divisibile per num_gironi, aggiungi ghost
    if state is not None:
        while len(squadre_ids) % num_gironi != 0:
            ghost_num = sum(1 for sq in state["squadre"] if sq.get("is_ghost"))
            ghost_sq = new_squadra(f"👻 BYE {ghost_num+1}", [], quota_pagata=0.0, is_ghost=True)
            state["squadre"].append(ghost_sq)
            squadre_ids.append(ghost_sq["id"])

    gironi = []
    for i in range(num_gironi):
        squadre_girone = squadre_ids[i::num_gironi]
        partite = []
        for j in range(len(squadre_girone)):
            for k in range(j+1, len(squadre_girone)):
                partite.append(new_partita(squadre_girone[j], squadre_girone[k], "girone", i))
        gironi.append({"nome": f"Girone {'ABCDEFGH'[i]}", "squadre": squadre_girone, "partite": partite})
    return gironi


def classifica_girone(state, girone):
    """Ordina le squadre di un girone per classifica."""
    squadre_dati = []
    for sid in girone["squadre"]:
        sq = get_squadra_by_id(state, sid)
        if sq:
            squadre_dati.append(sq)
    return sorted(squadre_dati, key=lambda s: (
        -s["punti_classifica"], -s["vittorie"],
        -(s["set_vinti"] - s["set_persi"]),
        -(s["punti_fatti"] - s["punti_subiti"])
    ))


def _bracket_size_from_n(n):
    """
    Restituisce la potenza di 2 minima >= n tra i tabelloni standard federali.
    Tabelloni: 2 (finale), 4 (semifinali), 8 (quarti), 16 (ottavi),
               32 (sedicesimi), 64 (trentaduesimi), 128 (sessantaquattresimi).
    """
    SIZES = [2, 4, 8, 16, 32, 64, 128]
    for s in SIZES:
        if s >= n:
            return s
    return SIZES[-1]


BRACKET_ROUND_NAMES = {
    128: "⚡ Sessantaquattresimi di Finale",
    64:  "⚡ Trentaduesimi di Finale",
    32:  "⚡ Sedicesimi di Finale",
    16:  "🏅 Ottavi di Finale",
    8:   "🏅 Quarti di Finale",
    4:   "🥇 Semifinali",
    2:   "🏆 FINALE 1°/2° Posto",
}


def genera_bracket_da_gironi(gironi, state=None, squadre_per_girone_passano=2):
    """
    Genera il bracket dai gironi con tabelloni federali standard.

    Logica BYE:
    - Si calcola il numero di squadre qualificate reali.
    - Si trova il tabellone standard (potenza di 2) più piccolo >= qualificate.
    - Si aggiungono BYE per completare il tabellone.
    - I BYE vengono assegnati alle migliori squadre per ranking (top seeds),
      così le prime classificate avanzano automaticamente al turno successivo
      come avviene nelle competizioni federali FIPAV/FIVB.
    """
    # 1. Raccogli qualificate ordinate per ranking di girone
    #    (prima la prima del girone A, poi la prima del girone B, ecc.
    #     poi le seconde, poi le terze...)
    max_passano = squadre_per_girone_passano
    posizioni_per_rango = {}  # rango (0=prima, 1=seconda...) -> lista squadre in ordine
    for pos in range(max_passano):
        posizioni_per_rango[pos] = []
        for g in gironi:
            if state:
                classifica = classifica_girone(state, g)
                reali = [sq for sq in classifica if not sq.get("is_ghost")]
                if pos < len(reali):
                    posizioni_per_rango[pos].append(reali[pos]["id"])
            else:
                if pos < len(g["squadre"]):
                    posizioni_per_rango[pos].append(g["squadre"][pos])

    # Lista finale qualificate: prima tutte le prime, poi tutte le seconde, ecc.
    qualificate = []
    seen = set()
    for pos in range(max_passano):
        for sid in posizioni_per_rango[pos]:
            if sid not in seen:
                seen.add(sid)
                qualificate.append(sid)

    n_reali = len(qualificate)
    if n_reali == 0:
        return []

    # 2. Calcola bracket size e numero BYE necessari
    bracket_size = _bracket_size_from_n(n_reali)
    n_bye = bracket_size - n_reali

    # 3. Crea squadre BYE (ghost) e aggiungile allo state
    bye_ids = []
    if state is not None and n_bye > 0:
        # Rimuovi eventuali vecchi BYE-playoff
        state["squadre"] = [sq for sq in state["squadre"]
                            if not (sq.get("is_ghost") and "BYE-PO" in sq.get("nome",""))]
        for i in range(n_bye):
            ghost_sq = new_squadra(f"👻 BYE {i+1}", [], quota_pagata=0.0, is_ghost=True)
            ghost_sq["nome"] = f"👻 BYE {i+1}"
            state["squadre"].append(ghost_sq)
            bye_ids.append(ghost_sq["id"])

    # 4. Costruisci il tabellone incrociato (seeding federale):
    #    I BYE vengono assegnati alle prime squadre del ranking (top seeds).
    #    Posizione 1 (top seed) affronta BYE → avanza senza giocare.
    #    Schema: seed 1 vs BYE, seed 2 vs BYE, ..., poi le restanti si sfidano.
    #
    #    Il tabellone ha bracket_size // 2 partite al primo turno.
    #    Costruiamo il seeding: interleave qualificate e BYE in modo che
    #    i BYE cadano sulle posizioni alte del bracket (top seeds).
    #
    #    seeded_list: [sq1, sq2, ..., sqN, BYE1, BYE2, ...]
    #    ma distribuiamo i BYE nelle posizioni basse del bracket
    #    (le squadre in fondo affrontano i BYE, non i top seed).
    #
    #    Convenzione FIVB: i BYE si mettono in fondo al seeding,
    #    quindi le ultime posizioni del bracket affrontano i BYE.
    #    I top seed affrontano le squadre peggiori (o BYE).
    #
    #    Bracket standard a eliminazione singola:
    #    partita 1: seed 1 vs seed (bracket_size)
    #    partita 2: seed 2 vs seed (bracket_size - 1)  ...ecc.
    #
    seeded = qualificate + bye_ids  # qualificate prima (meglio ranked), BYE in fondo
    # Assicura esattamente bracket_size squadre
    while len(seeded) < bracket_size:
        if state is not None:
            ghost_sq = new_squadra(f"👻 BYE X", [], quota_pagata=0.0, is_ghost=True)
            state["squadre"].append(ghost_sq)
            seeded.append(ghost_sq["id"])
        else:
            seeded.append(None)

    seeded = seeded[:bracket_size]

    # 5. Genera le partite del primo turno
    #    seed 1 vs seed N, seed 2 vs seed N-1, ...
    bracket = []
    half = bracket_size // 2
    for i in range(half):
        sq1 = seeded[i]
        sq2 = seeded[bracket_size - 1 - i]
        if sq1 and sq2:
            p = new_partita(sq1, sq2, "eliminazione")
            # Se una delle due è BYE, marca come auto-win
            sq1_data = get_squadra_by_id(state, sq1) if state else None
            sq2_data = get_squadra_by_id(state, sq2) if state else None
            if sq2_data and sq2_data.get("is_ghost"):
                p["squadra1_score"] = 1
                p["squadra2_score"] = 0
                p["vincitore"]  = sq1
                p["perdente"]   = sq2
                p["confermata"] = True
                p["is_bye"]     = True
            elif sq1_data and sq1_data.get("is_ghost"):
                p["squadra1_score"] = 0
                p["squadra2_score"] = 1
                p["vincitore"]  = sq2
                p["perdente"]   = sq1
                p["confermata"] = True
                p["is_bye"]     = True
            bracket.append(p)

    # 6. Salva metadati bracket nello state
    if state is not None:
        state["torneo"]["bracket_size"]     = bracket_size
        state["torneo"]["n_bye_playoff"]    = n_bye
        state["torneo"]["n_qualificate_playoff"] = n_reali

    return bracket
