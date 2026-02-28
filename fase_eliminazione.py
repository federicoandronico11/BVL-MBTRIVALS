"""
fase_eliminazione.py — Fase 3: Eliminazione Diretta / Playoffs v5
Include: Quarti → Semifinali → Finale 3°/4° + Finale 1°/2°
"""
import streamlit as st
from data_manager import (
    save_state, simula_partita, aggiorna_classifica_squadra,
    get_squadra_by_id, new_partita
)
from ui_components import render_match_card


def render_eliminazione(state):
    st.markdown("## ⚡ Eliminazione Diretta")

    col_a, col_b = st.columns([2, 2])
    with col_a:
        state["simulazione_al_ranking"] = st.toggle(
            "📊 Invia dati simulati al Ranking",
            value=state["simulazione_al_ranking"]
        )
    with col_b:
        if st.button("🎲 Simula TUTTI i Playoff", use_container_width=True):
            _simula_tutti_playoff(state)

    st.divider()

    bracket = state["bracket"]
    bracket_extra = state.get("bracket_extra", [])  # finale 3-4 e finale 1-2

    if not bracket and not bracket_extra:
        st.info("Nessuna partita di playoff disponibile.")
        return

    # Raggruppa per round in base al tag "round"
    rounds = {}
    for p in bracket:
        r = p.get("round", "Playoff")
        rounds.setdefault(r, []).append(p)
    for p in bracket_extra:
        r = p.get("round", "Finale")
        rounds.setdefault(r, []).append(p)

    # Ordine visualizzazione round
    round_order = ["🏅 Quarti di Finale", "🥇 Semifinali", "🥉 Finale 3°/4° Posto", "🏆 FINALE 1°/2° Posto", "⚡ Playoff"]
    shown_rounds = [r for r in round_order if r in rounds]
    other_rounds = [r for r in rounds if r not in round_order]

    for round_name in shown_rounds + other_rounds:
        if round_name not in rounds:
            continue
        partite = rounds[round_name]
        st.markdown(f"### {round_name}")

        for partita in partite:
            render_match_card(state, partita, label=round_name)
            if not partita["confermata"]:
                _render_scoreboard_playoff(state, partita, f"pl_{partita['id']}")
            else:
                sq = get_squadra_by_id(state, partita["vincitore"])
                if sq:
                    if "Finale" in round_name and "3" in round_name:
                        st.success(f"🥉 3° Posto: **{sq['nome']}**")
                    elif "FINALE" in round_name:
                        st.success(f"🏆 Vincitore: **{sq['nome']}**")
                    else:
                        st.success(f"✅ Vincitore: **{sq['nome']}** → avanza")
            st.markdown("---")

    # Controlla avanzamento e genera prossimi round
    _check_e_genera_prossimi_round(state)
    _check_finale(state)


def _render_scoreboard_playoff(state, partita, key_prefix):
    sq1 = get_squadra_by_id(state, partita["sq1"])
    sq2 = get_squadra_by_id(state, partita["sq2"])
    if not sq1 or not sq2:
        return
    torneo = state["torneo"]
    formato = torneo["formato_set"]

    with st.expander("📝 Inserisci Risultato", expanded=False):
        n_set = 1 if formato == "Set Unico" else 3

        punteggi_inseriti = []
        for s in range(n_set):
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                p1 = st.number_input(f"Set {s+1} — {sq1['nome']}", 0, 50, 0, key=f"{key_prefix}_s{s}_p1")
            with col2:
                st.markdown("<div style='text-align:center;padding-top:28px;color:#666'>vs</div>", unsafe_allow_html=True)
            with col3:
                p2 = st.number_input(f"Set {s+1} — {sq2['nome']}", 0, 50, 0, key=f"{key_prefix}_s{s}_p2")
            punteggi_inseriti.append((p1, p2))

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ CONFERMA RISULTATO", key=f"{key_prefix}_confirm", use_container_width=True):
                s1v, s2v = 0, 0
                punteggi_validi = []
                for p1, p2 in punteggi_inseriti:
                    if p1 > 0 or p2 > 0:
                        if p1 > p2: s1v += 1
                        else: s2v += 1
                        punteggi_validi.append((p1, p2))
                if not punteggi_validi:
                    st.error("Inserisci almeno un set.")
                    return
                partita["punteggi"] = punteggi_validi
                partita["set_sq1"] = s1v
                partita["set_sq2"] = s2v
                partita["vincitore"] = partita["sq1"] if s1v > s2v else partita["sq2"]
                partita["confermata"] = True
                aggiorna_classifica_squadra(state, partita)
                save_state(state)
                st.rerun()
        with col_btn2:
            if st.button("🎲 Simula", key=f"{key_prefix}_sim"):
                simula_partita(state, partita)
                if state["simulazione_al_ranking"]:
                    aggiorna_classifica_squadra(state, partita)
                save_state(state)
                st.rerun()


def _check_e_genera_prossimi_round(state):
    """
    Dopo ogni round completato, genera automaticamente il round successivo.
    Logica: Quarti → Semifinali → [Finale 3-4 + Finale 1-2]
    """
    bracket = state["bracket"]
    if not bracket:
        return

    bracket_extra = state.get("bracket_extra", [])
    state["bracket_extra"] = bracket_extra

    # Raggruppa bracket principale per round
    rounds = {}
    for p in bracket:
        r = p.get("round", "⚡ Playoff")
        rounds.setdefault(r, []).append(p)

    round_order = ["🏅 Quarti di Finale", "🥇 Semifinali", "⚡ Playoff"]

    for i, r_name in enumerate(round_order):
        if r_name not in rounds:
            continue
        partite_round = rounds[r_name]
        tutti_confermati = all(p["confermata"] for p in partite_round)
        if not tutti_confermati:
            break

        # Controlla se esiste già il round successivo
        next_round = None
        if r_name == "🏅 Quarti di Finale":
            next_round = "🥇 Semifinali"
        elif r_name == "🥇 Semifinali" or r_name == "⚡ Playoff":
            # Genera finale 3-4 e finale 1-2 se non esistono ancora
            _genera_finali_da_semifinali(state, partite_round)
            return

        if next_round and next_round not in rounds:
            vincitori = [p["vincitore"] for p in partite_round]
            nuove_partite = []
            for j in range(0, len(vincitori), 2):
                if j + 1 < len(vincitori):
                    np = new_partita(vincitori[j], vincitori[j+1], "eliminazione")
                    np["round"] = next_round
                    nuove_partite.append(np)
            bracket.extend(nuove_partite)
            save_state(state)
            st.rerun()


def _genera_finali_da_semifinali(state, partite_semifinali):
    """Genera finale 3°/4° e finale 1°/2° dalle semifinali completate."""
    bracket_extra = state.get("bracket_extra", [])
    state["bracket_extra"] = bracket_extra

    # Controlla se le finali esistono già
    round_esistenti = {p.get("round") for p in bracket_extra}
    if "🏆 FINALE 1°/2° Posto" in round_esistenti:
        return  # già generate

    vincitori = [p["vincitore"] for p in partite_semifinali if p["confermata"]]
    perdenti = []
    for p in partite_semifinali:
        if p["confermata"]:
            perdente = p["sq1"] if p["vincitore"] == p["sq2"] else p["sq2"]
            perdenti.append(perdente)

    if len(vincitori) >= 2:
        # Finale 1°/2°
        finale_1_2 = new_partita(vincitori[0], vincitori[1], "eliminazione")
        finale_1_2["round"] = "🏆 FINALE 1°/2° Posto"
        bracket_extra.append(finale_1_2)

    if len(perdenti) >= 2:
        # Finale 3°/4°
        finale_3_4 = new_partita(perdenti[0], perdenti[1], "eliminazione")
        finale_3_4["round"] = "🥉 Finale 3°/4° Posto"
        bracket_extra.append(finale_3_4)

    save_state(state)
    st.rerun()


def _simula_tutti_playoff(state):
    for partita in state["bracket"]:
        if not partita["confermata"]:
            simula_partita(state, partita)
            if state["simulazione_al_ranking"]:
                aggiorna_classifica_squadra(state, partita)
    for partita in state.get("bracket_extra", []):
        if not partita["confermata"]:
            simula_partita(state, partita)
            if state["simulazione_al_ranking"]:
                aggiorna_classifica_squadra(state, partita)
    # Genera prossimi round se servono
    _check_e_genera_prossimi_round(state)
    save_state(state)
    st.rerun()


def _check_finale(state):
    """Se finale 1-2 è completata, vai alla proclamazione."""
    bracket_extra = state.get("bracket_extra", [])
    all_bracket = state["bracket"] + bracket_extra

    if not all_bracket:
        return

    # Cerca finale 1-2
    finale_1_2 = next((p for p in bracket_extra if p.get("round") == "🏆 FINALE 1°/2° Posto"), None)

    # Fallback: usa l'ultima partita del bracket principale se non c'è bracket_extra
    if not finale_1_2 and not bracket_extra:
        tutti_confermati = all(p["confermata"] for p in state["bracket"])
        if tutti_confermati and state["bracket"]:
            finale_1_2 = state["bracket"][-1]

    if not finale_1_2 or not finale_1_2.get("confermata"):
        return

    st.divider()

    vincitore_id = finale_1_2["vincitore"]
    perdente_id = finale_1_2["sq1"] if vincitore_id == finale_1_2["sq2"] else finale_1_2["sq2"]

    # Terzo posto
    finale_3_4 = next((p for p in bracket_extra if p.get("round") == "🥉 Finale 3°/4° Posto" and p.get("confermata")), None)
    terzo_id = finale_3_4["vincitore"] if finale_3_4 else None

    sq_vincitore = get_squadra_by_id(state, vincitore_id)

    col1, col2 = st.columns([3, 1])
    with col1:
        if sq_vincitore:
            st.success(f"🏆 **{sq_vincitore['nome']}** ha vinto il torneo!")

    with col2:
        if st.button("🏆 PROCLAMAZIONE →", use_container_width=True):
            state["vincitore"] = vincitore_id
            podio = [(1, vincitore_id), (2, perdente_id)]
            if terzo_id:
                podio.append((3, terzo_id))

            state["podio"] = podio
            if state["simulazione_al_ranking"]:
                from data_manager import trasferisci_al_ranking
                trasferisci_al_ranking(state, podio)

            state["fase"] = "proclamazione"
            save_state(state)
            st.rerun()
