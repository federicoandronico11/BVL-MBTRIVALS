"""
fase_setup.py — Fase 1: Configurazione torneo v5
Aggiunge: Girone Unico all'italiana, scelta gironi, squadre per girone,
sistema qualificazione, auto-BYE, ghost squads.
"""
import streamlit as st
from data_manager import (
    new_atleta, new_squadra, get_atleta_by_id,
    save_state, genera_gironi
)


def render_setup(state):
    st.markdown("## ⚙️ Configurazione Torneo")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 📋 Impostazioni Generali")
        nome = st.text_input("Nome Torneo", value=state["torneo"]["nome"], placeholder="es. Summer Cup 2025")
        state["torneo"]["nome"] = nome

        # MODALITÀ TORNEO
        modalita_opts = ["Gironi + Playoff", "Girone Unico", "Doppia Eliminazione"]
        modalita_idx = modalita_opts.index(state["torneo"].get("modalita", "Gironi + Playoff"))
        modalita = st.selectbox("🏆 Modalità Torneo", modalita_opts, index=modalita_idx,
                                help="Gironi+Playoff = fase gironi + eliminazione diretta | Girone Unico = tutti contro tutti, classifica finale")
        state["torneo"]["modalita"] = modalita
        # Mantieni compatibilità con tipo_tabellone
        state["torneo"]["tipo_tabellone"] = modalita

        formato = st.selectbox("Formato Set", ["Set Unico", "Best of 3"],
                               index=["Set Unico", "Best of 3"].index(state["torneo"]["formato_set"]))
        state["torneo"]["formato_set"] = formato

        pmax = st.number_input("Punteggio Massimo Set", min_value=11, max_value=30,
                               value=state["torneo"]["punteggio_max"])
        state["torneo"]["punteggio_max"] = pmax

        data = st.date_input("Data Torneo")
        state["torneo"]["data"] = str(data)

        with st.expander("⚙️ Impostazioni Avanzate", expanded=False):
            st.markdown("#### Formato di Gioco")
            tipo_gioco = st.selectbox(
                "Giocatori per Squadra",
                ["2x2", "3x3", "4x4"],
                index=["2x2", "3x3", "4x4"].index(state["torneo"].get("tipo_gioco", "2x2")),
            )
            state["torneo"]["tipo_gioco"] = tipo_gioco

            st.markdown("#### Configurazione Gironi")
            n_squadre_real = len([sq for sq in state["squadre"] if not sq.get("is_ghost")])

            if modalita == "Girone Unico":
                state["torneo"]["num_gironi"] = 1
                st.info("Girone Unico: tutte le squadre in un unico girone all'italiana.")
            else:
                max_gironi = max(2, n_squadre_real // 2) if n_squadre_real >= 4 else 4
                num_gironi_val = state["torneo"].get("num_gironi", 2)
                num_gironi_val = min(num_gironi_val, max_gironi)
                num_gironi = st.select_slider(
                    "Numero di Gironi",
                    options=list(range(1, min(max_gironi+1, 9))),
                    value=max(1, min(num_gironi_val, 8)),
                    help="Quanti gironi dividere le squadre"
                )
                state["torneo"]["num_gironi"] = num_gironi

                passano_opts = [1, 2, 3, 4]
                passano_val = state["torneo"].get("squadre_per_girone_passano", 2)
                if passano_val not in passano_opts: passano_val = 2
                squadre_passano = st.selectbox(
                    "Squadre qualificate per girone",
                    passano_opts,
                    index=passano_opts.index(passano_val),
                    help="Quante squadre avanzano dai gironi ai playoff"
                )
                state["torneo"]["squadre_per_girone_passano"] = squadre_passano

                sistema_opts = ["Prime classificate", "Classifica avulsa tra pari"]
                sistema_idx = sistema_opts.index(state["torneo"].get("sistema_qualificazione", "Prime classificate"))
                sistema = st.selectbox("Sistema qualificazione", sistema_opts, index=sistema_idx)
                state["torneo"]["sistema_qualificazione"] = sistema

            st.markdown("#### Numero Minimo Squadre")
            min_sq_options = [2, 4, 6, 8, 12, 16]
            min_sq_val = state["torneo"].get("min_squadre", 4)
            if min_sq_val not in min_sq_options:
                min_sq_options = sorted(set(min_sq_options + [min_sq_val]))
            state["torneo"]["min_squadre"] = st.select_slider(
                "Squadre minime per avviare",
                options=min_sq_options,
                value=min_sq_val,
            )
            st.caption("💡 Puoi aggiungere squadre GHOST per i BYE — perdono automaticamente.")

            usa_ranking = st.toggle(
                "🏅 Usa Ranking in-app per Teste di Serie",
                value=state["torneo"].get("usa_ranking_teste_serie", False),
            )
            state["torneo"]["usa_ranking_teste_serie"] = usa_ranking
            if usa_ranking:
                st.info("✅ Le squadre saranno distribuite nei gironi secondo il ranking globale.")

    with col2:
        st.markdown("### 👤 Gestione Atleti")
        _render_atleti_manager(state)

    st.divider()
    st.markdown("### 🏐 Iscrizione Squadre")
    _render_squadre_manager(state)

    if state["squadre"] and len(state["squadre"]) >= 2:
        st.divider()
        with st.expander("📋 Ordina Squadre nel Tabellone", expanded=False):
            st.caption("Modifica l'ordine — influenza la distribuzione nei gironi")
            _render_squadre_ordine(state)

    st.divider()
    n_squadre = len(state["squadre"])
    tipo_gioco = state["torneo"].get("tipo_gioco", "2x2")
    min_sq = state["torneo"].get("min_squadre", 4)

    ghost_count = sum(1 for sq in state["squadre"] if sq.get("is_ghost"))
    real_count = n_squadre - ghost_count

    if real_count > 0 and real_count < min_sq:
        needed = min_sq - real_count
        with st.expander(f"👻 Aggiungi Squadre Ghost ({ghost_count} presenti)", expanded=False):
            st.info(f"Servono {needed} squadre in più per raggiungere il minimo di {min_sq}. Le Ghost perdono automaticamente.")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if st.button(f"➕ Aggiungi {needed} Ghost", key="add_ghost"):
                    for i in range(needed):
                        ghost_sq = new_squadra(f"👻 Ghost {ghost_count+i+1}", [], quota_pagata=0.0, is_ghost=True)
                        state["squadre"].append(ghost_sq)
                    save_state(state)
                    st.rerun()
            with col_g2:
                if ghost_count > 0:
                    if st.button("🗑️ Rimuovi Tutte le Ghost", key="rm_ghost"):
                        state["squadre"] = [sq for sq in state["squadre"] if not sq.get("is_ghost")]
                        save_state(state)
                        st.rerun()

    # Anteprima struttura gironi
    if real_count >= 2:
        num_gironi = state["torneo"].get("num_gironi", 2) if state["torneo"].get("modalita") != "Girone Unico" else 1
        sq_per_girone = real_count // num_gironi if num_gironi > 0 else real_count
        passano = state["torneo"].get("squadre_per_girone_passano", 2)
        qualificate_totali = passano * num_gironi

        st.markdown(f"""
        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;font-size:0.82rem;color:var(--text-secondary)">
            📐 <strong>Struttura prevista:</strong>
            {num_gironi} girone/i da ~{sq_per_girone} squadre
            {"· " + str(qualificate_totali) + " qualificate ai playoff" if state["torneo"].get("modalita") != "Girone Unico" else "· Classifica finale diretta"}
        </div>
        """, unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if n_squadre < min_sq:
            st.warning(f"⚠️ Servono almeno {min_sq} squadre ({n_squadre}/{min_sq})")
        elif not nome:
            st.warning("⚠️ Inserisci il nome del torneo.")
        else:
            ghost_note = f" (incluse {ghost_count} 👻)" if ghost_count > 0 else ""
            st.success(f"✅ {n_squadre} squadre iscritte ({tipo_gioco}){ghost_note}. Pronto!")

    with col_b:
        if n_squadre >= min_sq and nome:
            if st.button("🚀 AVVIA TORNEO →", use_container_width=True):
                ids = [s["id"] for s in state["squadre"]]
                modalita_corrente = state["torneo"].get("modalita", "Gironi + Playoff")
                if modalita_corrente == "Girone Unico":
                    num_gironi = 1
                else:
                    num_gironi = state["torneo"].get("num_gironi", max(2, n_squadre // 4))
                use_ranking = state["torneo"].get("usa_ranking_teste_serie", False)
                state["gironi"] = genera_gironi(ids, num_gironi, use_ranking=use_ranking, state=state)
                state["bracket"] = []
                state["bracket_extra"] = []
                state["fase"] = "gironi"
                save_state(state)
                st.rerun()


def _render_atleti_manager(state):
    nomi_esistenti = [a["nome"] for a in state["atleti"]]
    with st.expander("➕ Aggiungi Nuovo Atleta", expanded=False):
        col_n1, col_n2, col_foto = st.columns([2, 2, 1])
        with col_n1:
            nuovo_nome = st.text_input("Nome", key="new_atleta_nome", placeholder="Nome")
        with col_n2:
            nuovo_cognome = st.text_input("Cognome", key="new_atleta_cognome", placeholder="Cognome")
        with col_foto:
            foto_file = st.file_uploader("Foto (opz.)", type=["png","jpg","jpeg"], key="new_atleta_foto")

        if st.button("Aggiungi Atleta", key="btn_add_atleta"):
            full = f"{nuovo_nome.strip()} {nuovo_cognome.strip()}".strip()
            if full and full not in nomi_esistenti:
                nuovo = new_atleta(nuovo_nome.strip(), nuovo_cognome.strip())
                if foto_file:
                    import base64
                    nuovo["foto_b64"] = base64.b64encode(foto_file.read()).decode()
                state["atleti"].append(nuovo)
                save_state(state)
                st.success(f"✅ {full} aggiunto! (OVR 40 — Bronzo Raro)")
                st.rerun()
            elif full in nomi_esistenti:
                st.error("Atleta già presente.")
            else:
                st.error("Inserisci almeno il nome.")

    if state["atleti"]:
        st.markdown(f"**Atleti registrati:** {len(state['atleti'])}")
        for a in state["atleti"][:6]:
            col_a, col_del = st.columns([4, 1])
            with col_a:
                foto_html = ""
                if a.get("foto_b64"):
                    foto_html = f'<img src="data:image/png;base64,{a["foto_b64"]}" style="height:20px;width:20px;border-radius:50%;object-fit:cover;margin-right:6px;vertical-align:middle">'
                from data_manager import calcola_overall_fifa, get_card_type
                ovr = calcola_overall_fifa(a)
                ct = get_card_type(ovr)
                st.markdown(f"<span style='font-size:0.85rem'>{foto_html}• {a['nome']} <span style='color:var(--accent-gold);font-size:0.72rem'>OVR {ovr}</span></span>", unsafe_allow_html=True)
            with col_del:
                if st.button("✕", key=f"del_a_{a['id']}"):
                    state["atleti"] = [x for x in state["atleti"] if x["id"] != a["id"]]
                    save_state(state); st.rerun()
        if len(state["atleti"]) > 6:
            st.caption(f"... e altri {len(state['atleti'])-6}")


def _render_squadre_manager(state):
    atleti_nomi = [a["nome"] for a in state["atleti"]]
    tipo_gioco = state["torneo"].get("tipo_gioco", "2x2")
    n_giocatori = int(tipo_gioco[0])

    if len(state["atleti"]) < n_giocatori:
        st.info(f"Aggiungi almeno {n_giocatori} atleti per creare una squadra {tipo_gioco}.")
        return

    cols = st.columns(n_giocatori)
    atleti_selezionati = []
    for i in range(n_giocatori):
        with cols[i]:
            disponibili = [n for n in atleti_nomi if n not in atleti_selezionati]
            sel = st.selectbox(f"Atleta {i+1}", disponibili, key=f"sq_a{i}")
            atleti_selezionati.append(sel)

    col_nome_tog, col_quota = st.columns([2, 1])
    with col_nome_tog:
        nome_automatico = st.toggle("Nome automatico squadra", value=True, key="toggle_nome_auto")
        if nome_automatico:
            nome_sq = "/".join([a.split()[0] for a in atleti_selezionati])
            st.text_input("Nome Squadra (auto)", value=nome_sq, disabled=True, key="sq_nome_auto")
        else:
            nome_sq = st.text_input("Nome Squadra", placeholder="es. Team Sabbia", key="sq_nome_manual")
    with col_quota:
        quota_pagata = st.number_input("💶 Quota Pagata (€)", min_value=0.0, max_value=10000.0,
                                        value=0.0, step=5.0, key="sq_quota")

    if st.button("➕ Iscrive Squadra", key="btn_add_squadra"):
        atleti_objs = [next((a for a in state["atleti"] if a["nome"] == n), None) for n in atleti_selezionati]
        if any(a is None for a in atleti_objs):
            st.error("Atleti non trovati.")
        elif not nome_sq:
            st.error("Inserisci il nome della squadra.")
        else:
            atleti_in_squadra = [aid for sq in state["squadre"] for aid in sq["atleti"]]
            conflitti = [a for a in atleti_objs if a["id"] in atleti_in_squadra]
            if conflitti:
                st.warning(f"⚠️ {conflitti[0]['nome']} è già in un'altra squadra.")
            else:
                sq = new_squadra(nome_sq, [a["id"] for a in atleti_objs], quota_pagata=quota_pagata)
                state["squadre"].append(sq)
                save_state(state)
                st.success(f"✅ Squadra '{nome_sq}' iscritta! Quota: €{quota_pagata:.2f}")
                st.rerun()

    if state["squadre"]:
        st.markdown(f"#### Squadre Iscritte ({len(state['squadre'])})")
        real_squads = [sq for sq in state["squadre"] if not sq.get("is_ghost")]
        totale_quote = sum(sq.get("quota_pagata", 0.0) for sq in real_squads)
        st.caption(f"💰 Totale quote raccolte: **€{totale_quote:.2f}**")
        for i, sq in enumerate(state["squadre"]):
            a_names = [get_atleta_by_id(state, aid)["nome"] for aid in sq["atleti"] if get_atleta_by_id(state, aid)]
            quota = sq.get("quota_pagata", 0.0)
            is_ghost = sq.get("is_ghost", False)
            col_s, col_q, col_btn = st.columns([4, 1, 1])
            with col_s:
                ghost_tag = " 👻 <span style='color:#888;font-size:0.75rem'>GHOST</span>" if is_ghost else ""
                names_str = "Perde automaticamente" if is_ghost else " / ".join(a_names)
                st.markdown(f"**{sq['nome']}**{ghost_tag} — <span style='color:var(--text-secondary)'>{names_str}</span>", unsafe_allow_html=True)
            with col_q:
                if not is_ghost:
                    st.markdown(f"<div style='padding-top:8px;color:var(--accent-gold,#ffd700);font-weight:700'>€{quota:.0f}</div>", unsafe_allow_html=True)
            with col_btn:
                if st.button("🗑️", key=f"del_sq_{i}"):
                    state["squadre"].pop(i)
                    save_state(state); st.rerun()


def _render_squadre_ordine(state):
    squadre = state["squadre"]
    for i, sq in enumerate(squadre):
        a_names = [get_atleta_by_id(state, aid)["nome"] for aid in sq["atleti"] if get_atleta_by_id(state, aid)]
        col_pos, col_nome, col_up, col_down = st.columns([1, 4, 1, 1])
        with col_pos:
            st.markdown(f"<div style='padding-top:8px;color:var(--text-secondary);font-weight:700'>#{i+1}</div>", unsafe_allow_html=True)
        with col_nome:
            st.markdown(f"<div style='padding-top:8px'><strong>{sq['nome']}</strong> <span style='color:var(--text-secondary);font-size:0.8rem'>{' / '.join(a_names)}</span></div>", unsafe_allow_html=True)
        with col_up:
            if i > 0 and st.button("↑", key=f"up_{i}"):
                state["squadre"][i], state["squadre"][i-1] = state["squadre"][i-1], state["squadre"][i]
                save_state(state); st.rerun()
        with col_down:
            if i < len(squadre)-1 and st.button("↓", key=f"down_{i}"):
                state["squadre"][i], state["squadre"][i+1] = state["squadre"][i+1], state["squadre"][i]
                save_state(state); st.rerun()
