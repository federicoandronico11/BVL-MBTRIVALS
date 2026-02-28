"""
fase_gironi.py — Fase 2: Fase a Gironi v5
Supporta: configurazione gironi, girone unico all'italiana, squadre per girone, 
auto-BYE, classifica avulsa, scelta quante squadre passano.
"""
import streamlit as st
from data_manager import (
    save_state, simula_partita, aggiorna_classifica_squadra,
    get_squadra_by_id, nome_squadra, genera_bracket_da_gironi,
    classifica_girone
)
from ui_components import render_match_card


def render_gironi(state):
    modalita = state["torneo"].get("modalita", "Gironi + Playoff")

    if modalita == "Girone Unico":
        st.markdown("## 🏆 Girone Unico All'Italiana")
        _render_configurazione_girone_unico(state)
    else:
        st.markdown("## 🔵 Fase a Gironi")
        _render_configurazione_gironi(state)

    st.divider()
    _render_body_gironi(state)


def _render_configurazione_girone_unico(state):
    """Configurazione per modalità girone unico all'italiana."""
    col_a, col_b = st.columns([2, 2])
    with col_a:
        state["simulazione_al_ranking"] = st.toggle(
            "📊 Invia dati simulati al Ranking",
            value=state["simulazione_al_ranking"]
        )
    with col_b:
        if st.button("🎲 Simula TUTTI i Risultati", use_container_width=True):
            _simula_tutti(state)

    # In girone unico la classifica finale decide tutto
    tutti_confermati = all(
        p["confermata"]
        for g in state["gironi"]
        for p in g["partite"]
    )

    col_c, col_d = st.columns([2, 2])
    with col_c:
        if tutti_confermati:
            if st.button("🏆 PROCLAMA VINCITORE →", use_container_width=True):
                _proclama_da_girone_unico(state)
        else:
            completate = sum(1 for g in state["gironi"] for p in g["partite"] if p["confermata"])
            totali = sum(len(g["partite"]) for g in state["gironi"])
            st.info(f"Partite completate: {completate}/{totali}")


def _render_configurazione_gironi(state):
    """Configurazione gironi normali con controlli avanzati."""
    col_a, col_b, col_c = st.columns([2, 2, 2])
    with col_a:
        state["simulazione_al_ranking"] = st.toggle(
            "📊 Invia dati simulati al Ranking",
            value=state["simulazione_al_ranking"],
            help="Se OFF, la simulazione non aggiorna statistiche atleti"
        )
    with col_b:
        if st.button("🎲 Simula TUTTI i Risultati", use_container_width=True):
            _simula_tutti(state)
    with col_c:
        tutti_confermati = all(
            p["confermata"]
            for g in state["gironi"]
            for p in g["partite"]
        )
        if tutti_confermati:
            if st.button("⚡ AVANZA ALL'ELIMINAZIONE →", use_container_width=True):
                _genera_e_avanza(state)
        else:
            completate = sum(1 for g in state["gironi"] for p in g["partite"] if p["confermata"])
            totali = sum(len(g["partite"]) for g in state["gironi"])
            st.info(f"Completate: {completate}/{totali}")

    # Impostazioni avanzate playoff
    with st.expander("⚙️ Impostazioni Passaggio Turno", expanded=False):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            num_passano = st.selectbox(
                "Squadre che passano per girone",
                [1, 2, 3, 4],
                index=[1,2,3,4].index(state["torneo"].get("squadre_per_girone_passano", 2)),
                help="Quante squadre qualificate per ogni girone"
            )
            state["torneo"]["squadre_per_girone_passano"] = num_passano
        with col_s2:
            sistema = st.selectbox(
                "Sistema di qualificazione",
                ["Prime classificate", "Classifica avulsa tra pari"],
                index=["Prime classificate", "Classifica avulsa tra pari"].index(
                    state["torneo"].get("sistema_qualificazione", "Prime classificate")
                )
            )
            state["torneo"]["sistema_qualificazione"] = sistema

        # Ricalcola gironi se si cambia numero gironi (da setup)
        n_gironi_correnti = len(state["gironi"])
        st.caption(f"💡 Gironi attuali: {n_gironi_correnti}. Per modificare il numero di gironi, torna al Setup.")


def _genera_e_avanza(state):
    """Genera il bracket e avanza alla fase eliminazione."""
    squadre_passano = state["torneo"].get("squadre_per_girone_passano", 2)
    bracket = genera_bracket_da_gironi(state["gironi"], state=state, squadre_per_girone_passano=squadre_passano)

    # Assegna round iniziale al bracket
    n = len(bracket)
    if n >= 4:
        round_name = "🏅 Quarti di Finale"
    elif n >= 2:
        round_name = "🥇 Semifinali"
    else:
        round_name = "🏆 FINALE 1°/2° Posto"

    for p in bracket:
        p["round"] = round_name

    state["bracket"] = bracket
    state["bracket_extra"] = []
    state["fase"] = "eliminazione"
    save_state(state)
    st.rerun()


def _render_body_gironi(state):
    """Render principale tabs gironi + classifiche."""
    nomi_gironi = [g["nome"] for g in state["gironi"]]
    nomi_gironi.append("📊 Classifiche")
    tabs = st.tabs(nomi_gironi)

    for i, g in enumerate(state["gironi"]):
        with tabs[i]:
            _render_girone(state, g, i)

    with tabs[-1]:
        _render_classifiche_gironi(state)


def _render_girone(state, girone, girone_idx):
    st.markdown(f"### {girone['nome']}")

    # Header classifica mini sopra le partite
    squadre_ord = classifica_girone(state, girone)
    passano = state["torneo"].get("squadre_per_girone_passano", 2)
    html = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">'
    for idx, sq in enumerate(squadre_ord):
        is_ghost = sq.get("is_ghost", False)
        color = "#00c851" if idx < passano else "#888"
        marker = "🟢" if idx < passano else ""
        html += f'<span style="background:var(--bg-card2);border:1px solid {color};border-radius:6px;padding:3px 8px;font-size:0.72rem;font-weight:700;color:{color}">{marker} {idx+1}. {sq["nome"]} <span style="color:var(--accent-gold)">{sq["punti_classifica"]}pt</span></span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    for j, partita in enumerate(girone["partite"]):
        sq1 = get_squadra_by_id(state, partita["sq1"])
        sq2 = get_squadra_by_id(state, partita["sq2"])
        if not sq1 or not sq2:
            continue
        render_match_card(state, partita, label=f"{girone['nome']} · Match {j+1}")
        if not partita["confermata"]:
            _render_scoreboard_live(state, partita, f"g{girone_idx}_p{j}")
        st.markdown("---")


def _render_scoreboard_live(state, partita, key_prefix):
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
                p1 = st.number_input(f"Set {s+1} — {sq1['nome']}", 0, 50, 0,
                                     key=f"{key_prefix}_s{s}_p1")
            with col2:
                st.markdown("<div style='text-align:center;padding-top:28px;color:#666'>vs</div>", unsafe_allow_html=True)
            with col3:
                p2 = st.number_input(f"Set {s+1} — {sq2['nome']}", 0, 50, 0,
                                     key=f"{key_prefix}_s{s}_p2")
            punteggi_inseriti.append((p1, p2))

        battuta = st.radio(
            "🏐 In battuta",
            [sq1["nome"], sq2["nome"]],
            horizontal=True,
            key=f"{key_prefix}_battuta"
        )
        partita["in_battuta"] = 1 if battuta == sq1["nome"] else 2

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
                    st.error("Inserisci almeno un set con punteggio.")
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


def _render_classifiche_gironi(state):
    passano = state["torneo"].get("squadre_per_girone_passano", 2)

    for girone in state["gironi"]:
        st.markdown(f"### 📊 Classifica {girone['nome']}")
        squadre_ord = classifica_girone(state, girone)

        html = """
        <table class="rank-table">
        <tr>
            <th>#</th><th>SQUADRA</th><th>PTS</th><th>V</th><th>P</th>
            <th>SV</th><th>SP</th><th>PF</th><th>PS</th>
        </tr>"""

        pos_cls = {1: "gold", 2: "silver", 3: "bronze"}
        for i, sq in enumerate(squadre_ord):
            pos = i + 1
            cls = pos_cls.get(pos, "")
            qualif = "🟢" if pos <= passano else ""
            is_ghost = sq.get("is_ghost", False)
            row_style = "opacity:0.5;" if is_ghost else ""
            html += f"""
            <tr style="{row_style}">
                <td><span class="rank-pos {cls}">{pos}</span></td>
                <td style="text-align:left;font-weight:600">{qualif} {sq['nome']}</td>
                <td style="font-weight:700;color:var(--accent-gold)">{sq['punti_classifica']}</td>
                <td style="color:var(--green)">{sq['vittorie']}</td>
                <td style="color:var(--accent-red)">{sq['sconfitte']}</td>
                <td>{sq['set_vinti']}</td><td>{sq['set_persi']}</td>
                <td>{sq['punti_fatti']}</td><td>{sq['punti_subiti']}</td>
            </tr>"""

        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        st.caption(f"🟢 Le prime {passano} qualificate ai Playoff")
        st.markdown("---")


def _simula_tutti(state):
    for girone in state["gironi"]:
        for partita in girone["partite"]:
            if not partita["confermata"]:
                simula_partita(state, partita)
                if state["simulazione_al_ranking"]:
                    aggiorna_classifica_squadra(state, partita)
    save_state(state)
    st.rerun()


def _proclama_da_girone_unico(state):
    """In modalità girone unico, la classifica finale decide il podio."""
    if not state["gironi"]:
        return
    girone = state["gironi"][0]
    squadre_ord = classifica_girone(state, girone)
    squadre_reali = [sq for sq in squadre_ord if not sq.get("is_ghost")]

    if not squadre_reali:
        st.error("Nessuna squadra reale trovata.")
        return

    podio = []
    for i, sq in enumerate(squadre_reali[:3]):
        podio.append((i+1, sq["id"]))

    state["vincitore"] = squadre_reali[0]["id"] if squadre_reali else None
    state["podio"] = podio
    state["bracket"] = []
    state["bracket_extra"] = []

    if state["simulazione_al_ranking"]:
        from data_manager import trasferisci_al_ranking
        trasferisci_al_ranking(state, podio)

    state["fase"] = "proclamazione"
    save_state(state)
    st.rerun()
