"""
tornei_programmati.py - MBT-BVL 2.0
"""
import streamlit as st
import base64
import random
from datetime import datetime
from data_manager import save_state


def render_admin_tornei_programmati(state):
    st.markdown("## Gestione Tornei in Programma")
    st.caption("Crea tornei futuri. Gli atleti potranno iscriversi dall'app.")
    state.setdefault("tornei_programmati", [])
    tab_crea, tab_gestisci = st.tabs(["Crea Nuovo Torneo", "Gestisci Tornei"])
    with tab_crea:
        _render_form_crea_torneo(state)
    with tab_gestisci:
        _render_lista_tornei_admin(state)


def _render_form_crea_torneo(state):
    st.markdown("### Nuovo Torneo in Programma")
    col1, col2 = st.columns(2)
    with col1:
        nome  = st.text_input("Nome del Torneo *", key="tp_nome", placeholder="Es. MBT Summer Open 2025")
        data_t = st.text_input("Data del Torneo *", key="tp_data", value=datetime.today().strftime("%d/%m/%Y"))
        luogo = st.text_input("Luogo *", key="tp_luogo", placeholder="Es. Catania, Lido La Playa")
    with col2:
        formato   = st.selectbox("Formato Set", ["Set Unico","Best of 3","Best of 5"], key="tp_formato")
        punteggio = st.selectbox("Punteggio Massimo", [11,15,21,25], index=2, key="tp_punteggio")
        tipo      = st.selectbox("Tipo Tabellone", ["Gironi + Playoff","Girone Unico","Eliminazione Diretta"], key="tp_tipo")
    desc  = st.text_area("Descrizione / Regolamento", key="tp_desc", height=100)
    quota = st.number_input("Quota iscrizione (euro)", min_value=0.0, value=20.0, step=5.0, key="tp_quota")

    st.markdown("#### Copertina del Torneo")
    st.caption("Trascina un'immagine nell'area qui sotto oppure clicca per sfogliare.")
    if "tp_cover_b64" not in st.session_state:
        st.session_state.tp_cover_b64 = None
        st.session_state.tp_cover_ext = "jpeg"
    copertina_file = st.file_uploader("Trascina la copertina qui oppure clicca per sfogliare",
                                       type=["jpg","jpeg","png","webp"], key="tp_copertina")
    if copertina_file:
        raw = copertina_file.read()
        st.session_state.tp_cover_b64 = base64.b64encode(raw).decode()
        st.session_state.tp_cover_ext = copertina_file.type.split("/")[-1]
    if st.session_state.tp_cover_b64:
        ext = st.session_state.tp_cover_ext
        st.markdown('<img src="data:image/' + ext + ';base64,' + st.session_state.tp_cover_b64 + '" style="width:100%;max-height:220px;object-fit:cover;border-radius:10px;margin-top:8px;border:2px solid #e8002d">', unsafe_allow_html=True)
        if st.button("Rimuovi copertina", key="btn_rm_cover"):
            st.session_state.tp_cover_b64 = None
            st.rerun()

    st.markdown("---")
    if st.button("CREA TORNEO IN PROGRAMMA", use_container_width=True, type="primary", key="btn_crea_torneo_prog"):
        errors = []
        if not nome.strip():   errors.append("Inserisci il nome.")
        if not data_t.strip(): errors.append("Inserisci la data.")
        if not luogo.strip():  errors.append("Inserisci il luogo.")
        for e in errors: st.error(e)
        if not errors:
            nuovo = {
                "id": "tp_" + str(random.randint(10000,99999)),
                "nome_programmato": nome.strip(),
                "data_programmata": data_t.strip(),
                "luogo": luogo.strip(),
                "formato_set": formato,
                "punteggio_max": punteggio,
                "tipo_tabellone": tipo,
                "descrizione": desc.strip(),
                "quota": quota,
                "copertina_b64": st.session_state.tp_cover_b64,
                "cover_pos_x": 50,
                "cover_pos_y": 50,
                "iscritti": [],
                "creato_il": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "attivo": True,
            }
            state["tornei_programmati"].append(nuovo)
            save_state(state)
            st.session_state.tp_cover_b64 = None
            st.success("Torneo " + nome.strip() + " creato con successo!")
            st.rerun()


def _render_lista_tornei_admin(state):
    tornei = state.get("tornei_programmati", [])
    if not tornei:
        st.info("Nessun torneo. Creane uno dalla tab Crea Nuovo Torneo.")
        return

    # Se c'e' un torneo in editing, mostra l'editor
    tid_edit = st.session_state.get("admin_edit_torneo_id")
    if tid_edit:
        torneo_edit = next((t for t in tornei if t["id"] == tid_edit), None)
        if torneo_edit:
            _render_editor_torneo(torneo_edit, state)
            return
        else:
            st.session_state.admin_edit_torneo_id = None

    st.markdown("#### Tornei Esistenti")
    for torneo in tornei:
        nome     = torneo.get("nome_programmato","")
        data_t   = torneo.get("data_programmata","")
        luogo    = torneo.get("luogo","")
        iscritti = torneo.get("iscritti",[])
        attivo   = torneo.get("attivo",True)
        n_iscr   = len(iscritti)
        tid      = torneo.get("id","")

        col_a, col_b, col_c, col_d, col_e, col_f = st.columns([3,2,1,1,1,1])
        with col_a:
            icon = "🟢" if attivo else "🔴"
            st.markdown(icon + " **" + nome + "**  \n" + "📅 " + data_t + "  ·  👥 " + str(n_iscr) + " iscritti")
        with col_b:
            st.markdown("📍 " + luogo + "  \n💶 €" + str(torneo.get("quota",0)))
        with col_c:
            if st.button("✏️", key="edit_" + tid, use_container_width=True, type="primary", help="Modifica torneo"):
                st.session_state.admin_edit_torneo_id = tid
                st.rerun()
        with col_d:
            tog_lbl = "👁️ Off" if attivo else "👁️ On"
            if st.button(tog_lbl, key="tog_" + tid, use_container_width=True, help="Attiva/disattiva visibilità"):
                torneo["attivo"] = not attivo
                save_state(state)
                st.rerun()
        with col_e:
            if st.button("🚀 Avvia", key="avvia_" + tid, use_container_width=True, help="Avvia il torneo nel Setup"):
                _avvia_torneo(state, torneo)
        with col_f:
            if st.button("🗑️", key="del_lista_" + tid, use_container_width=True, help="Elimina torneo"):
                st.session_state["conferma_del_" + tid] = True
                st.rerun()

        # Conferma eliminazione
        if st.session_state.get("conferma_del_" + tid):
            st.warning("⚠️ Sei sicuro di voler eliminare **" + nome + "**? Questa operazione non è reversibile.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Sì, elimina", key="yes_del_" + tid, use_container_width=True):
                    state["tornei_programmati"].remove(torneo)
                    save_state(state)
                    st.session_state.pop("conferma_del_" + tid, None)
                    st.success("Torneo eliminato.")
                    st.rerun()
            with col_no:
                if st.button("❌ Annulla", key="no_del_" + tid, use_container_width=True):
                    st.session_state.pop("conferma_del_" + tid, None)
                    st.rerun()

        st.markdown('<hr style="border-color:#1a1a2a;margin:6px 0">', unsafe_allow_html=True)



def _avvia_torneo(state, torneo):
    """Copia i dati del torneo programmato nel setup e porta alla fase setup."""
    from data_manager import empty_state
    
    # Preleva dati dal torneo programmato
    t = state["torneo"]
    t["nome"]             = torneo.get("nome_programmato", "")
    t["data"]             = _converti_data(torneo.get("data_programmata", ""))
    t["formato_set"]      = torneo.get("formato_set", "Set Unico")
    t["punteggio_max"]    = torneo.get("punteggio_max", 21)
    t["modalita"]         = torneo.get("tipo_tabellone", "Gironi + Playoff")
    t["tipo_tabellone"]   = torneo.get("tipo_tabellone", "Gironi + Playoff")

    # Precarica iscritti come atleti se non esistono già
    iscritti = torneo.get("iscritti", [])
    atleti_esistenti = {a["nome"].lower() for a in state.get("atleti", [])}
    for entry in iscritti:
        if isinstance(entry, dict):
            nome_atl = entry.get("nome", "").strip()
            if nome_atl and nome_atl.lower() not in atleti_esistenti:
                from data_manager import new_atleta
                state["atleti"].append(new_atleta(nome_atl))
                atleti_esistenti.add(nome_atl.lower())

    # Porta alla fase setup
    state["fase"] = "setup"
    state["gironi"] = []
    state["bracket"] = []
    state["bracket_extra"] = []
    state["squadre"] = []
    state["vincitore"] = None
    state["podio"] = []

    # Segnale per il setup: mostra banner di avvio torneo
    st.session_state["torneo_avviato_da"] = torneo.get("nome_programmato", "")
    st.session_state["avvia_torneo_mode"] = True

    from data_manager import save_state
    save_state(state)
    st.success("🚀 Torneo **" + torneo.get("nome_programmato","") + "** caricato nel Setup! Puoi fare ulteriori modifiche prima di iniziare.")
    st.rerun()


def _converti_data(data_str):
    """Converte data da dd/mm/yyyy a yyyy-mm-dd per il campo data del torneo."""
    try:
        return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return data_str



def _render_tab_squadre_admin(torneo, state, tid):
    """Gestione completa squadre iscritte al torneo programmato."""
    torneo.setdefault("squadre_programmate", [])
    squadre = torneo["squadre_programmate"]
    tutti_atleti = state.get("atleti", [])

    st.markdown("### 🏐 Squadre Iscritte  (" + str(len(squadre)) + ")")

    # ── Lista squadre esistenti ───────────────────────────────────────────────
    if not squadre:
        st.info("Nessuna squadra iscritta. Aggiungine una qui sotto.")
    else:
        for idx, sq in enumerate(squadre):
            nomi = sq.get("nomi_atleti", [])
            quota = sq.get("quota", 0.0)
            pagato = sq.get("pagato", False)
            nome_sq = sq.get("nome", "Squadra " + str(idx+1))
            border = "#00c851" if pagato else "#e8002d"
            stato_lbl = "✅ Pagato" if pagato else "⏳ Da pagare"

            with st.expander(
                f"#{idx+1}  {nome_sq}  —  {' / '.join(nomi)}  —  €{quota:.0f}  {stato_lbl}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                with col1:
                    atl_options = [a["nome"] for a in tutti_atleti]
                    sel_atl = []
                    for i_atl in range(2):
                        cur = nomi[i_atl] if i_atl < len(nomi) else (atl_options[0] if atl_options else "")
                        idx_cur = atl_options.index(cur) if cur in atl_options else 0
                        chosen = st.selectbox(
                            f"Atleta {i_atl+1}",
                            atl_options,
                            index=idx_cur,
                            key=f"sq_atl_{tid}_{idx}_{i_atl}"
                        )
                        sel_atl.append(chosen)
                    nome_auto = " / ".join(sel_atl)
                    nome_man = st.text_input("Nome Squadra", value=nome_sq, key=f"sq_nome_{tid}_{idx}", placeholder=nome_auto)

                with col2:
                    new_quota = st.number_input("💶 Quota (€)", min_value=0.0, value=float(quota), step=5.0, key=f"sq_quota_{tid}_{idx}")
                    new_pagato = st.checkbox("✅ Pagato", value=pagato, key=f"sq_pag_{tid}_{idx}")
                    note = st.text_input("Note", value=sq.get("note",""), key=f"sq_note_{tid}_{idx}", placeholder="es. bonifico")

                col_sv, col_rm = st.columns(2)
                with col_sv:
                    if st.button("💾 Salva", key=f"sq_save_{tid}_{idx}", use_container_width=True, type="primary"):
                        sq["nomi_atleti"] = sel_atl
                        sq["nome"] = nome_man.strip() or nome_auto
                        sq["quota"] = new_quota
                        sq["pagato"] = new_pagato
                        sq["note"] = note
                        # aggiorna anche IDs
                        sq["atleti_ids"] = [a["id"] for a in tutti_atleti if a["nome"] in sel_atl]
                        save_state(state)
                        st.success("Squadra aggiornata!")
                        st.rerun()
                with col_rm:
                    if st.button("🗑️ Rimuovi", key=f"sq_rm_{tid}_{idx}", use_container_width=True):
                        squadre.pop(idx)
                        save_state(state)
                        st.rerun()

    st.divider()

    # ── Aggiungi nuova squadra ────────────────────────────────────────────────
    st.markdown("#### ➕ Aggiungi Squadra")
    if not tutti_atleti:
        st.warning("Nessun atleta registrato nell'app. Aggiungili prima dal Setup Torneo.")
        return

    atl_options = [a["nome"] for a in tutti_atleti]

    col1, col2 = st.columns(2)
    with col1:
        atl1 = st.selectbox("Atleta 1 *", atl_options, key=f"new_sq_a1_{tid}")
        atl2_opts = [n for n in atl_options if n != atl1]
        atl2 = st.selectbox("Atleta 2 *", atl2_opts, key=f"new_sq_a2_{tid}") if atl2_opts else None
        nome_auto_new = f"{atl1} / {atl2}" if atl2 else atl1
        nome_sq_new = st.text_input("Nome Squadra", placeholder=nome_auto_new, key=f"new_sq_nome_{tid}")
    with col2:
        quota_new = st.number_input("💶 Quota (€)", min_value=0.0, value=float(torneo.get("quota", 20.0)), step=5.0, key=f"new_sq_quota_{tid}")
        pagato_new = st.checkbox("✅ Già pagato", value=False, key=f"new_sq_pag_{tid}")
        note_new = st.text_input("Note", placeholder="es. bonifico", key=f"new_sq_note_{tid}")

    if st.button("➕ AGGIUNGI SQUADRA", key=f"btn_add_sq_{tid}", use_container_width=True, type="primary"):
        if not atl2:
            st.error("Seleziona 2 atleti diversi.")
        else:
            atleti_ids = [a["id"] for a in tutti_atleti if a["nome"] in [atl1, atl2]]
            torneo["squadre_programmate"].append({
                "id": "sqp_" + str(random.randint(10000,99999)),
                "nome": nome_sq_new.strip() or nome_auto_new,
                "nomi_atleti": [atl1, atl2],
                "atleti_ids": atleti_ids,
                "quota": quota_new,
                "pagato": pagato_new,
                "note": note_new,
                "data_iscrizione": datetime.now().strftime("%d/%m/%Y %H:%M"),
            })
            save_state(state)
            st.success(f"Squadra **{nome_sq_new or nome_auto_new}** aggiunta!")
            st.rerun()

    # ── Riepilogo incassi ─────────────────────────────────────────────────────
    if squadre:
        st.divider()
        tot_atteso  = sum(s.get("quota", 0) for s in squadre)
        tot_pagato  = sum(s.get("quota", 0) for s in squadre if s.get("pagato"))
        tot_pending = tot_atteso - tot_pagato
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("💰 Totale Atteso",   f"€ {tot_atteso:.2f}")
        col_b.metric("✅ Incassato",        f"€ {tot_pagato:.2f}", f"{sum(1 for s in squadre if s.get('pagato'))} sq")
        col_c.metric("⏳ Da Incassare",     f"€ {tot_pending:.2f}", f"{sum(1 for s in squadre if not s.get('pagato'))} sq")


def _render_editor_torneo(torneo, state):
    tid = torneo.get("id","")

    if st.button("← Torna alla lista tornei", key="back_edit_list"):
        st.session_state.admin_edit_torneo_id = None
        st.rerun()

    st.markdown('<div style="font-family:Barlow Condensed,sans-serif;font-size:1.8rem;font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px">Modifica Torneo</div>', unsafe_allow_html=True)
    st.caption("Creato il: " + torneo.get("creato_il","") + "  |  ID: " + tid)
    st.markdown("---")

    tab_info, tab_cover, tab_iscritti = st.tabs(["Informazioni", "Copertina", "Iscritti e Squadre"])

    # ── TAB INFO ─────────────────────────────────────────────────────────────
    with tab_info:
        col1, col2 = st.columns(2)
        with col1:
            new_nome  = st.text_input("Nome del Torneo *", value=torneo.get("nome_programmato",""), key="ed_nome_"+tid)
            new_data  = st.text_input("Data *", value=torneo.get("data_programmata",""), key="ed_data_"+tid)
            new_luogo = st.text_input("Luogo *", value=torneo.get("luogo",""), key="ed_luogo_"+tid)
        with col2:
            fmt_opts  = ["Set Unico","Best of 3","Best of 5"]
            fmt_cur   = torneo.get("formato_set","Set Unico")
            fmt_idx   = fmt_opts.index(fmt_cur) if fmt_cur in fmt_opts else 0
            new_fmt   = st.selectbox("Formato Set", fmt_opts, index=fmt_idx, key="ed_fmt_"+tid)

            pmax_opts = [11,15,21,25]
            pmax_cur  = torneo.get("punteggio_max",21)
            pmax_idx  = pmax_opts.index(pmax_cur) if pmax_cur in pmax_opts else 2
            new_pmax  = st.selectbox("Punteggio Max", pmax_opts, index=pmax_idx, key="ed_pmax_"+tid)

            tipo_opts = ["Gironi + Playoff","Girone Unico","Eliminazione Diretta"]
            tipo_cur  = torneo.get("tipo_tabellone","Gironi + Playoff")
            tipo_idx  = tipo_opts.index(tipo_cur) if tipo_cur in tipo_opts else 0
            new_tipo  = st.selectbox("Tipo Tabellone", tipo_opts, index=tipo_idx, key="ed_tipo_"+tid)

        new_desc  = st.text_area("Descrizione / Regolamento", value=torneo.get("descrizione",""), key="ed_desc_"+tid, height=120)
        new_quota = st.number_input("Quota (euro)", min_value=0.0, value=float(torneo.get("quota",0.0)), step=5.0, key="ed_quota_"+tid)
        new_att   = st.toggle("Torneo visibile agli utenti", value=torneo.get("attivo",True), key="ed_att_"+tid)

        col_sv, col_del = st.columns([3,1])
        with col_sv:
            if st.button("Salva Modifiche", key="save_info_"+tid, use_container_width=True, type="primary"):
                errs = []
                if not new_nome.strip():  errs.append("Nome obbligatorio.")
                if not new_data.strip():  errs.append("Data obbligatoria.")
                if not new_luogo.strip(): errs.append("Luogo obbligatorio.")
                for e in errs: st.error(e)
                if not errs:
                    torneo["nome_programmato"] = new_nome.strip()
                    torneo["data_programmata"] = new_data.strip()
                    torneo["luogo"]            = new_luogo.strip()
                    torneo["formato_set"]      = new_fmt
                    torneo["punteggio_max"]    = new_pmax
                    torneo["tipo_tabellone"]   = new_tipo
                    torneo["descrizione"]      = new_desc.strip()
                    torneo["quota"]            = new_quota
                    torneo["attivo"]           = new_att
                    save_state(state)
                    st.success("Modifiche salvate!")
                    st.rerun()
        with col_del:
            if st.button("Elimina Torneo", key="del_"+tid, use_container_width=True):
                state["tornei_programmati"].remove(torneo)
                save_state(state)
                st.session_state.admin_edit_torneo_id = None
                st.success("Torneo eliminato.")
                st.rerun()

    # ── TAB COPERTINA ─────────────────────────────────────────────────────────
    with tab_cover:
        st.markdown("### Gestione Copertina")
        st.caption("Carica o trascina un'immagine. Usa i cursori per posizionare il punto focale visibile nella card.")

        cover_stg_key = "ed_cover_stg_" + tid
        cover_ext_key = "ed_cover_ext_" + tid
        px_key        = "ed_px_" + tid
        py_key        = "ed_py_" + tid

        if cover_stg_key not in st.session_state:
            st.session_state[cover_stg_key] = None
        if cover_ext_key not in st.session_state:
            st.session_state[cover_ext_key] = "jpeg"
        if px_key not in st.session_state:
            st.session_state[px_key] = int(torneo.get("cover_pos_x", 50))
        if py_key not in st.session_state:
            st.session_state[py_key] = int(torneo.get("cover_pos_y", 50))

        current_cover = torneo.get("copertina_b64")

        new_file = st.file_uploader(
            "Trascina qui la copertina oppure clicca per sfogliare",
            type=["jpg","jpeg","png","webp"],
            key="fu_cover_"+tid,
        )
        if new_file:
            raw = new_file.read()
            st.session_state[cover_stg_key] = base64.b64encode(raw).decode()
            st.session_state[cover_ext_key] = new_file.type.split("/")[-1]

        preview_b64 = st.session_state[cover_stg_key] or current_cover
        preview_ext = st.session_state[cover_ext_key] if st.session_state[cover_stg_key] else "jpeg"

        if preview_b64:
            st.markdown("#### Posizionamento del Punto Focale")
            st.caption("Muovi i cursori per scegliere quale parte dell'immagine e' al centro. L'anteprima si aggiorna in tempo reale.")

            col_sl1, col_sl2 = st.columns(2)
            with col_sl1:
                px = st.slider("Orizzontale (%) — 0=sinistra  100=destra", 0, 100,
                               st.session_state[px_key], key="sl_px_"+tid)
                st.session_state[px_key] = px
            with col_sl2:
                py = st.slider("Verticale (%) — 0=alto  100=basso", 0, 100,
                               st.session_state[py_key], key="sl_py_"+tid)
                st.session_state[py_key] = py

            pos_css = str(px) + "% " + str(py) + "%"
            img_src  = "data:image/" + preview_ext + ";base64," + preview_b64

            col_prev1, col_prev2 = st.columns(2)
            with col_prev1:
                st.caption("Anteprima Card (180px)")
                st.markdown(
                    '<div style="border-radius:12px 12px 0 0;overflow:hidden;height:180px;border:2px solid #e8002d">'
                    '<img src="' + img_src + '" style="width:100%;height:100%;object-fit:cover;object-position:' + pos_css + '">'
                    '</div>'
                    '<div style="background:#13131a;border:2px solid #e8002d;border-top:none;border-radius:0 0 12px 12px;padding:10px 14px">'
                    '<div style="font-weight:900;color:#fff;font-size:1rem">' + torneo.get("nome_programmato","Torneo") + '</div>'
                    '<div style="color:#888;font-size:0.75rem;margin-top:3px">📅 ' + torneo.get("data_programmata","") + ' · 📍 ' + torneo.get("luogo","") + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
            with col_prev2:
                st.caption("Anteprima Hero (pagina dettaglio)")
                st.markdown(
                    '<div style="border-radius:12px;overflow:hidden;height:220px;border:2px solid #333">'
                    '<img src="' + img_src + '" style="width:100%;height:100%;object-fit:cover;object-position:' + pos_css + '">'
                    '</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                if st.button("Salva Copertina e Posizione", key="save_cover_"+tid,
                             use_container_width=True, type="primary"):
                    if st.session_state[cover_stg_key]:
                        torneo["copertina_b64"] = st.session_state[cover_stg_key]
                    torneo["cover_pos_x"] = px
                    torneo["cover_pos_y"] = py
                    save_state(state)
                    st.session_state[cover_stg_key] = None
                    st.success("Copertina e posizione salvate!")
                    st.rerun()
            with col_s2:
                if st.session_state[cover_stg_key]:
                    if st.button("Annulla nuova immagine", key="cancel_cover_"+tid, use_container_width=True):
                        st.session_state[cover_stg_key] = None
                        st.rerun()
            with col_s3:
                if current_cover:
                    if st.button("Rimuovi Copertina", key="rm_cover_"+tid, use_container_width=True):
                        torneo["copertina_b64"] = None
                        torneo["cover_pos_x"]   = 50
                        torneo["cover_pos_y"]   = 50
                        save_state(state)
                        st.session_state[cover_stg_key] = None
                        st.session_state[px_key] = 50
                        st.session_state[py_key] = 50
                        st.success("Copertina rimossa.")
                        st.rerun()
        else:
            st.info("Nessuna copertina. Carica o trascina un'immagine sopra.")

    # ── TAB ISCRITTI ─────────────────────────────────────────────────────────
    with tab_iscritti:
        _render_tab_squadre_admin(torneo, state, tid)


# ─── UTENTI: Griglia card cliccabili ─────────────────────────────────────────

def render_tornei_in_programma(state, user=None):
    state.setdefault("tornei_programmati", [])

    tid_sel = st.session_state.get("torneo_dettaglio_id")
    if tid_sel:
        torneo_sel = next((t for t in state["tornei_programmati"] if t["id"] == tid_sel), None)
        if torneo_sel:
            _render_dettaglio_torneo(torneo_sel, user, state)
            return
        else:
            st.session_state.torneo_dettaglio_id = None

    st.markdown("## Tornei in Programma")
    tornei_attivi = [t for t in state["tornei_programmati"] if t.get("attivo", True)]

    if not tornei_attivi:
        st.markdown('<div style="background:#13131a;border:2px dashed #2a2a3a;border-radius:12px;padding:48px;text-align:center"><div style="font-size:3rem;margin-bottom:12px">🏐</div><div style="font-size:1.1rem;font-weight:700;color:#888">Nessun torneo in programma</div><div style="font-size:0.8rem;color:#555;margin-top:8px">Controlla piu tardi!</div></div>', unsafe_allow_html=True)
        return

    def _parse_date(t):
        try: return datetime.strptime(t.get("data_programmata","01/01/2099"), "%d/%m/%Y")
        except: return datetime(2099,1,1)

    tornei_ord = sorted(tornei_attivi, key=_parse_date)
    cols_per_row = 2
    for row_start in range(0, len(tornei_ord), cols_per_row):
        chunk = tornei_ord[row_start:row_start+cols_per_row]
        cols  = st.columns(len(chunk))
        for col, torneo in zip(cols, chunk):
            with col:
                _render_card_cliccabile(torneo, user, state)


def _is_user_iscritto(iscritti, user_email):
    for e in iscritti:
        if isinstance(e, dict) and e.get("email") == user_email: return True
        if isinstance(e, str) and e == user_email: return True
    return False


def _render_card_cliccabile(torneo, user, state):
    nome      = torneo.get("nome_programmato","Torneo")
    data_t    = torneo.get("data_programmata","")
    luogo     = torneo.get("luogo","")
    formato   = torneo.get("formato_set","")
    quota     = torneo.get("quota",0)
    copertina = torneo.get("copertina_b64")
    iscritti  = torneo.get("iscritti",[])
    tid       = torneo.get("id","")
    pos_x     = torneo.get("cover_pos_x", 50)
    pos_y     = torneo.get("cover_pos_y", 50)

    user_email   = user.get("email","") if user else ""
    gia_iscritto = _is_user_iscritto(iscritti, user_email)
    n_iscr       = len(iscritti)
    border_color = "#00c851" if gia_iscritto else "#e8002d"
    n_label      = str(n_iscr) + (" iscritto" if n_iscr == 1 else " iscritti")
    badge        = ' &nbsp;&middot;&nbsp; <span style="color:#00c851;font-weight:700">Sei iscritto/a</span>' if gia_iscritto else ""

    if copertina:
        pos_css = str(pos_x) + "% " + str(pos_y) + "%"
        st.markdown(
            '<img src="data:image/jpeg;base64,' + copertina + '" '
            'style="width:100%;height:180px;object-fit:cover;object-position:' + pos_css + ';'
            'border-radius:12px 12px 0 0;display:block">',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div style="background:#13131a;border:2px solid ' + border_color + ';'
        'border-radius:' + ("0 0 12px 12px" if copertina else "12px") + ';padding:16px 18px 12px">'
        '<div style="font-family:Barlow Condensed,sans-serif;font-size:1.2rem;font-weight:900;'
        'color:#fff;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">' + nome + '</div>'
        '<div style="font-size:0.8rem;color:#888;line-height:1.9;margin-bottom:8px">'
        '&#128197; <strong style="color:#ccc">' + data_t + '</strong><br>'
        '&#128205; <strong style="color:#ccc">' + luogo + '</strong><br>'
        '&#127944; ' + formato + ' &nbsp;&middot;&nbsp; '
        '&#128182; <strong style="color:#ffd700">&euro;' + str(quota) + '</strong>'
        '</div>'
        '<div style="font-size:0.72rem;color:#555;border-top:1px solid #2a2a3a;padding-top:8px">'
        '&#128101; ' + n_label + badge + '</div></div>',
        unsafe_allow_html=True
    )

    btn_lbl = "Vedi dettagli" + (" · Sei iscritto/a" if gia_iscritto else " e iscriviti")
    if st.button(btn_lbl, key="open_"+tid, use_container_width=True):
        st.session_state.torneo_dettaglio_id = tid
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)


def _render_dettaglio_torneo(torneo, user, state):
    nome      = torneo.get("nome_programmato","Torneo")
    data_t    = torneo.get("data_programmata","")
    luogo     = torneo.get("luogo","")
    formato   = torneo.get("formato_set","")
    punteggio = torneo.get("punteggio_max","")
    tipo      = torneo.get("tipo_tabellone","")
    desc      = torneo.get("descrizione","")
    quota     = torneo.get("quota",0)
    copertina = torneo.get("copertina_b64")
    iscritti  = torneo.get("iscritti",[])
    tid       = torneo.get("id","")
    pos_x     = torneo.get("cover_pos_x", 50)
    pos_y     = torneo.get("cover_pos_y", 50)

    user_email   = user.get("email","") if user else ""
    gia_iscritto = _is_user_iscritto(iscritti, user_email)
    entry_utente = None
    if gia_iscritto and user:
        for e in iscritti:
            if isinstance(e, dict) and e.get("email") == user_email:
                entry_utente = e; break
            if isinstance(e, str) and e == user_email:
                entry_utente = {"email": user_email, "compagno_nome": "Da definire"}; break

    if st.button("← Torna ai tornei", key="btn_back_tornei"):
        st.session_state.torneo_dettaglio_id = None
        st.rerun()

    if copertina:
        pos_css = str(pos_x) + "% " + str(pos_y) + "%"
        st.markdown(
            '<img src="data:image/jpeg;base64,' + copertina + '" '
            'style="width:100%;max-height:340px;object-fit:cover;object-position:' + pos_css + ';'
            'border-radius:16px;margin-bottom:20px;box-shadow:0 8px 40px rgba(232,0,45,0.3)">',
            unsafe_allow_html=True
        )

    badge = ""
    if gia_iscritto:
        badge = ' <span style="background:#00c851;color:#000;font-size:0.7rem;font-weight:800;padding:4px 12px;border-radius:20px;letter-spacing:1px;vertical-align:middle;margin-left:10px">ISCRITTO/A</span>'
    st.markdown('<div style="font-family:Barlow Condensed,sans-serif;font-size:2.2rem;font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;line-height:1.2">🏐 ' + nome + badge + '</div>', unsafe_allow_html=True)

    col_i1, col_i2, col_i3 = st.columns(3)
    _info_box(col_i1, "📅", "Data",  data_t)
    _info_box(col_i2, "📍", "Luogo", luogo)
    _info_box_gold(col_i3, "💶", "Quota", "€" + str(quota))
    st.markdown("<br>", unsafe_allow_html=True)

    # ── METEO ────────────────────────────────────────────────────────────────
    _render_meteo(luogo, data_t)

    st.markdown("<br>", unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px">'
            '<div style="color:#e8002d;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:10px">Dettagli Gara</div>'
            '<div style="font-size:0.85rem;color:#ccc;line-height:2">'
            '🏐 Formato: <strong>' + formato + '</strong><br>'
            '🎯 Punteggio max: <strong>' + str(punteggio) + ' pt</strong><br>'
            '📊 Tabellone: <strong>' + tipo + '</strong><br>'
            '👥 Iscritti: <strong>' + str(len(iscritti)) + '</strong></div></div>',
            unsafe_allow_html=True
        )
    with col_d2:
        if desc:
            st.markdown(
                '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px">'
                '<div style="color:#e8002d;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:10px">Regolamento e Note</div>'
                '<div style="font-size:0.85rem;color:#aaa;line-height:1.6">' + desc + '</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    if not user:
        st.markdown('<div style="background:#13131a;border:2px dashed #e8002d;border-radius:12px;padding:24px;text-align:center"><div style="font-size:1.5rem;margin-bottom:8px">🔐</div><div style="color:#fff;font-weight:700;margin-bottom:4px">Accedi o registrati per iscriverti</div><div style="color:#888;font-size:0.82rem">Usa il tab Atleta nella schermata di login.</div></div>', unsafe_allow_html=True)
        _render_lista_iscritti(iscritti)
        return

    if gia_iscritto:
        comp_nome = entry_utente.get("compagno_nome","Da definire") if entry_utente else "Da definire"
        st.markdown(
            '<div style="background:#0a2a0a;border:2px solid #00c851;border-radius:12px;padding:20px 24px;margin-bottom:16px">'
            '<div style="font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;color:#00c851;font-weight:700;margin-bottom:8px">Sei iscritto/a</div>'
            '<div style="font-size:0.9rem;color:#ccc">Compagno: <strong style="color:#fff">' + comp_nome + '</strong></div></div>',
            unsafe_allow_html=True
        )
        if st.button("Annulla la mia iscrizione", key="disiscrivi_"+tid, use_container_width=True):
            torneo["iscritti"] = [
                e for e in iscritti
                if not (isinstance(e,dict) and e.get("email") == user_email)
                and not (isinstance(e,str) and e == user_email)
            ]
            save_state(state)
            _send_email_annullamento(user, torneo)
            st.success("Iscrizione annullata.")
            st.rerun()
    else:
        st.markdown("### 🏐 Iscriviti al Torneo")
        tutti_atleti = state.get("atleti",[])
        nome_utente  = (user.get("nome","") + " " + user.get("cognome","")).strip().lower()
        atleti_disp  = [a for a in tutti_atleti if a["nome"].lower() != nome_utente]
        opzioni      = ["Senza compagno / da definire"] + [a["nome"] for a in atleti_disp]

        scelta = st.selectbox("Scegli il tuo compagno di squadra", options=opzioni, key="comp_sel_"+tid,
                               help="Puoi scegliere tra gli atleti registrati nell'app.")
        compagno_nome   = scelta if scelta != "Senza compagno / da definire" else None
        compagno_atleta = next((a for a in atleti_disp if a["nome"] == compagno_nome), None) if compagno_nome else None

        if st.button("CONFERMA ISCRIZIONE", key="iscr_"+tid+"_"+user_email,
                     use_container_width=True, type="primary"):
            entry = {
                "email":           user_email,
                "nome":            (user.get("nome","") + " " + user.get("cognome","")).strip(),
                "compagno_nome":   compagno_nome or "Da definire",
                "compagno_id":     compagno_atleta["id"] if compagno_atleta else None,
                "data_iscrizione": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            torneo["iscritti"].append(entry)
            save_state(state)
            try:
                from auth_manager import _email_iscrizione_torneo
                _email_iscrizione_torneo(user, {"nome": nome, "data": data_t, "luogo": luogo,
                    "formato_set": formato, "punteggio_max": punteggio, "tipo_tabellone": tipo})
            except Exception:
                pass
            st.success("Iscrizione confermata! Compagno: " + (compagno_nome or "Da definire"))
            st.info("Riceverai una email di conferma a breve.")
            st.rerun()

    _render_lista_iscritti(iscritti)



def _render_meteo(luogo, data_torneo):
    """Mostra meteo reale tramite Open-Meteo (gratuito, no API key)."""
    import urllib.request
    import urllib.parse
    import json as _json
    from datetime import datetime as _dt

    st.markdown(
        '<div style="color:#e8002d;font-size:0.65rem;letter-spacing:2px;'
        'text-transform:uppercase;font-weight:700;margin-bottom:8px">🌤️ Meteo</div>',
        unsafe_allow_html=True
    )

    try:
        # 1. Geocoding: converti nome luogo in coordinate tramite Open-Meteo geocoding
        luogo_enc = urllib.parse.quote(luogo.split(",")[0].strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={luogo_enc}&count=1&language=it&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as resp:
            geo_data = _json.loads(resp.read())

        results = geo_data.get("results", [])
        if not results:
            st.caption("📍 Luogo non trovato per il meteo.")
            return

        lat  = results[0]["latitude"]
        lon  = results[0]["longitude"]
        city = results[0].get("name", luogo)

        # 2. Meteo attuale + previsioni
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,weathercode,windspeed_10m,relativehumidity_2m"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&timezone=Europe%2FRome&forecast_days=7"
        )
        with urllib.request.urlopen(weather_url, timeout=5) as resp:
            w = _json.loads(resp.read())

        cur  = w.get("current", {})
        daily = w.get("daily", {})

        temp     = cur.get("temperature_2m", "—")
        wcode    = cur.get("weathercode", 0)
        wind     = cur.get("windspeed_10m", "—")
        humidity = cur.get("relativehumidity_2m", "—")

        def wcode_to_emoji(c):
            if c == 0:   return "☀️", "Sereno"
            if c <= 3:   return "🌤️", "Poco nuvoloso"
            if c <= 48:  return "☁️", "Nuvoloso/Nebbia"
            if c <= 67:  return "🌧️", "Pioggia"
            if c <= 77:  return "🌨️", "Neve"
            if c <= 82:  return "🌦️", "Rovesci"
            return "⛈️", "Temporale"

        emoji, desc = wcode_to_emoji(wcode)

        # Card meteo attuale
        st.markdown(
            f'<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:12px;padding:16px 20px;margin-bottom:10px">'
            f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
            f'<div style="font-size:3rem">{emoji}</div>'
            f'<div>'
            f'<div style="font-size:1.6rem;font-weight:900;color:#fff">{temp}°C</div>'
            f'<div style="color:#888;font-size:0.8rem">{desc} · 📍 {city}</div>'
            f'</div>'
            f'<div style="margin-left:auto;text-align:right;font-size:0.78rem;color:#888;line-height:2">'
            f'💨 Vento: <strong style="color:#ccc">{wind} km/h</strong><br>'
            f'💧 Umidità: <strong style="color:#ccc">{humidity}%</strong>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        # Previsioni 5 giorni
        dates   = daily.get("time", [])[:5]
        codes   = daily.get("weathercode", [])[:5]
        t_max   = daily.get("temperature_2m_max", [])[:5]
        t_min   = daily.get("temperature_2m_min", [])[:5]
        precip  = daily.get("precipitation_sum", [])[:5]

        # Evidenzia il giorno del torneo se possibile
        try:
            data_torneo_fmt = _dt.strptime(data_torneo, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            data_torneo_fmt = None

        giorni_ita = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]
        cols = st.columns(len(dates))
        for i, (d, c, tmax, tmin, pr) in enumerate(zip(dates, codes, t_max, t_min, precip)):
            em, _ = wcode_to_emoji(c)
            try:
                dt_obj = _dt.strptime(d, "%Y-%m-%d")
                giorno = giorni_ita[dt_obj.weekday()] + " " + dt_obj.strftime("%d/%m")
            except Exception:
                giorno = d
            is_torneo = (d == data_torneo_fmt)
            border = "2px solid #e8002d" if is_torneo else "1px solid #2a2a3a"
            badge  = '<div style="font-size:0.6rem;color:#e8002d;font-weight:700;text-transform:uppercase;letter-spacing:1px">🏐 Torneo</div>' if is_torneo else ""
            with cols[i]:
                st.markdown(
                    f'<div style="background:#13131a;border:{border};border-radius:10px;'
                    f'padding:10px 6px;text-align:center">'
                    f'{badge}'
                    f'<div style="font-size:0.7rem;color:#888;margin-bottom:4px">{giorno}</div>'
                    f'<div style="font-size:1.4rem">{em}</div>'
                    f'<div style="font-size:0.8rem;font-weight:700;color:#fff">{tmax:.0f}°</div>'
                    f'<div style="font-size:0.7rem;color:#888">{tmin:.0f}°</div>'
                    + (f'<div style="font-size:0.65rem;color:#4af">💧{pr:.1f}mm</div>' if pr and pr > 0 else '')
                    + '</div>',
                    unsafe_allow_html=True
                )

        st.caption("Dati meteo: Open-Meteo.com · Aggiornati in tempo reale")

    except Exception as e:
        st.caption(f"⚠️ Meteo non disponibile al momento. ({e})")


def _render_lista_iscritti(iscritti):
    if not iscritti: return
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 👥 Iscritti al Torneo")
    for idx, entry in enumerate(iscritti, 1):
        if isinstance(entry, dict):
            en = entry.get("nome", entry.get("email",""))
            comp = entry.get("compagno_nome","Da definire")
            data_i = entry.get("data_iscrizione","")
        else:
            en = str(entry); comp = ""; data_i = ""
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:8px;'
            'padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;'
            'align-items:center;font-size:0.82rem">'
            '<span style="color:#fff;font-weight:600">#' + str(idx) + ' ' + en + '</span>'
            + ('<span style="color:#888">🤝 ' + comp + '</span>' if comp else '')
            + ('<span style="color:#555;font-size:0.7rem">' + data_i + '</span>' if data_i else '')
            + '</div>',
            unsafe_allow_html=True
        )


def _info_box(col, icon, label, value):
    with col:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px;text-align:center">'
            '<div style="font-size:1.8rem">' + icon + '</div>'
            '<div style="color:#888;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;margin:4px 0">' + label + '</div>'
            '<div style="font-weight:800;color:#fff;font-size:0.95rem">' + str(value) + '</div></div>',
            unsafe_allow_html=True
        )


def _info_box_gold(col, icon, label, value):
    with col:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px;text-align:center">'
            '<div style="font-size:1.8rem">' + icon + '</div>'
            '<div style="color:#888;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;margin:4px 0">' + label + '</div>'
            '<div style="font-weight:800;color:#ffd700;font-size:1.1rem">' + str(value) + '</div></div>',
            unsafe_allow_html=True
        )


def _send_email_annullamento(user, torneo):
    try:
        from auth_manager import _send_email, ADMIN_EMAIL
        nome_u = user.get("nome","") + " " + user.get("cognome","")
        nome_t = torneo.get("nome_programmato","Torneo")
        html = "<h2>Iscrizione Annullata</h2><p><strong>" + nome_u + "</strong> ha annullato da <strong>" + nome_t + "</strong>.<br>Data: " + datetime.now().strftime("%d/%m/%Y %H:%M") + "</p>"
        _send_email(ADMIN_EMAIL, "Disiscrizione: " + nome_u + " da " + nome_t, html)
    except Exception:
        pass
