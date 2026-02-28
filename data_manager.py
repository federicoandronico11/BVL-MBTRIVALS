"""
data_manager.py — Gestione persistenza JSON e modelli dati v5
Nuovi atleti partono con overall 40 (bronzo_raro) anche senza tornei.
"""
import json, os, random
from datetime import datetime
from pathlib import Path

DATA_FILE = "beach_volley_data.json"

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

def load_state():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
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
    return empty_state()

def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

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

def trasferisci_al_ranking(state, podio):
    nome_torneo = state["torneo"]["nome"]
    n_squadre = len(state["squadre"])
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
        for aid in sq["atleti"]:
            atleta = get_atleta_by_id(state, aid)
            if not atleta: continue
            s = atleta["stats"]
            s["tornei"] += 1
            s["storico_posizioni"].append((nome_torneo, pos, n_squadre))
            if pos == 1: s["vittorie"] += 1
            else: s["sconfitte"] += 1
            _aggiorna_attributi_fifa(atleta, pos)
    podio_atleti = {aid for _, sq_id in podio for aid in (get_squadra_by_id(state, sq_id) or {"atleti":[]})["atleti"]}
    for sq in state["squadre"]:
        if sq.get("is_ghost"): continue
        for aid in sq["atleti"]:
            if aid not in podio_atleti:
                atleta = get_atleta_by_id(state, aid)
                if atleta:
                    atleta["stats"]["tornei"] += 1
                    atleta["stats"]["sconfitte"] += 1
                    atleta["stats"]["storico_posizioni"].append((nome_torneo, n_squadre // 2, n_squadre))

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
        "check": lambda s: any(pos <= 3 for _, pos, *_ in s.get("storico_posizioni", []))
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
        "check": lambda s: sum(1 for _, pos, *_ in s.get("storico_posizioni", []) if pos <= 3) >= 20
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


def genera_bracket_da_gironi(gironi, state=None, squadre_per_girone_passano=2):
    """
    Genera il bracket dai gironi.
    Supporta configurazione: quante squadre passano per girone.
    Genera automaticamente: Quarti/Semifinali + Finale 1-2 + Finale 3-4.
    """
    qualificate = []
    for g in gironi:
        if state:
            classifica = classifica_girone(state, g)
            top = [sq["id"] for sq in classifica[:squadre_per_girone_passano] if not sq.get("is_ghost")]
        else:
            top = g["squadre"][:squadre_per_girone_passano]
        qualificate.extend(top)

    # Rimuovi duplicati mantenendo ordine
    seen = set()
    qualificate_unique = []
    for q in qualificate:
        if q not in seen:
            seen.add(q)
            qualificate_unique.append(q)

    # Assicura numero pari con ghost se necessario
    if state is not None:
        while len(qualificate_unique) % 2 != 0 and len(qualificate_unique) > 1:
            ghost_num = sum(1 for sq in state["squadre"] if sq.get("is_ghost"))
            ghost_sq = new_squadra(f"👻 BYE-PO {ghost_num+1}", [], quota_pagata=0.0, is_ghost=True)
            state["squadre"].append(ghost_sq)
            qualificate_unique.append(ghost_sq["id"])

    bracket = []
    # Genera partite incrociando teste di serie (1° girone A vs 2° girone B, ecc.)
    n = len(qualificate_unique)
    # Cerca di fare un bracket sensato
    metà = n // 2
    for i in range(metà):
        sq1 = qualificate_unique[i]
        sq2 = qualificate_unique[n - 1 - i]
        bracket.append(new_partita(sq1, sq2, "eliminazione"))

    return bracket
