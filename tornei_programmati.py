"""
tornei_programmati.py — MBT-BVL 2.0
Tornei in programma: admin crea con copertina drag&drop,
utenti vedono card cliccabili → schermata dettaglio con iscrizione + scelta compagno.
"""
import streamlit as st
import base64
import random
from datetime import datetime
from data_manager import save_state


# ─── ADMIN: Crea Torneo Programmato ──────────────────────────────────────────

def render_admin_tornei_programmati(state):
    st.markdown("## 📅 Gestione Tornei in Programma")
    st.caption("Crea tornei futuri con copertina. Gli atleti potranno iscriversi dall'app.")
    state.setdefault("tornei_programmati", [])

    tab_crea, tab_gestisci = st.tabs(["➕ Crea Nuovo Torneo", "📋 Gestisci Tornei"])
    with tab_crea:
        _render_form_crea_torneo(state)
    with tab_gestisci:
        _render_lista_tornei_admin(state)


def _render_form_crea_torneo(state):
    st.markdown("### ➕ Nuovo Torneo in Programma")

    col1, col2 = st.columns(2)
    with col1:
        nome      = st.text_input("Nome del Torneo *", key="tp_nome",
                                   placeholder="Es. MBT Summer Open 2025")
        data_t    = st.text_input("Data del Torneo *", key="tp_data",
                                   placeholder="GG/MM/AAAA",
                                   value=datetime.today().strftime("%d/%m/%Y"))
        luogo     = st.text_input("Luogo *", key="tp_luogo",
                                   placeholder="Es. Catania, Lido La Playa")
    with col2:
        formato   = st.selectbox("Formato Set",
                                  ["Set Unico", "Best of 3", "Best of 5"], key="tp_formato")
        punteggio = st.selectbox("Punteggio Massimo",
                                  [11, 15, 21, 25], index=2, key="tp_punteggio")
        tipo      = st.selectbox("Tipo Tabellone",
                                  ["Gironi + Playoff", "Girone Unico", "Eliminazione Diretta"],
                                  key="tp_tipo")

    desc  = st.text_area("Descrizione / Regolamento", key="tp_desc",
                          placeholder="Regole speciali, premi, informazioni aggiuntive...",
                          height=100)
    quota = st.number_input("Quota di iscrizione (€)", min_value=0.0,
                             value=20.0, step=5.0, key="tp_quota")

    # Copertina con drag & drop nativo Streamlit
    st.markdown("#### Copertina del Torneo")
    st.caption("Trascina un'immagine nell'area qui sotto oppure clicca per sfogliare dal dispositivo.")

    if "tp_cover_b64" not in st.session_state:
        st.session_state.tp_cover_b64 = None
        st.session_state.tp_cover_ext = "jpeg"

    copertina_file = st.file_uploader(
        "Trascina la copertina qui oppure clicca per sfogliare",
        type=["jpg", "jpeg", "png", "webp"],
        key="tp_copertina",
    )
    if copertina_file:
        raw = copertina_file.read()
        st.session_state.tp_cover_b64 = base64.b64encode(raw).decode()
        st.session_state.tp_cover_ext = copertina_file.type.split("/")[-1]

    if st.session_state.tp_cover_b64:
        ext = st.session_state.tp_cover_ext
        st.markdown(
            '<img src="data:image/' + ext + ';base64,' + st.session_state.tp_cover_b64 + '" '
            'style="width:100%;max-height:260px;object-fit:cover;'
            'border-radius:12px;margin-top:10px;border:2px solid #e8002d">',
            unsafe_allow_html=True
        )
        if st.button("Rimuovi copertina", key="btn_rm_cover"):
            st.session_state.tp_cover_b64 = None
            st.rerun()

    st.markdown("---")
    if st.button("CREA TORNEO IN PROGRAMMA", use_container_width=True,
                 type="primary", key="btn_crea_torneo_prog"):
        errors = []
        if not nome.strip():   errors.append("Inserisci il nome del torneo.")
        if not data_t.strip(): errors.append("Inserisci la data del torneo.")
        if not luogo.strip():  errors.append("Inserisci il luogo.")
        for e in errors:
            st.error(e)
        if not errors:
            nuovo = {
                "id":               "tp_" + str(random.randint(10000, 99999)),
                "nome_programmato": nome.strip(),
                "data_programmata": data_t.strip(),
                "luogo":            luogo.strip(),
                "formato_set":      formato,
                "punteggio_max":    punteggio,
                "tipo_tabellone":   tipo,
                "descrizione":      desc.strip(),
                "quota":            quota,
                "copertina_b64":    st.session_state.tp_cover_b64,
                "iscritti":         [],
                "creato_il":        datetime.now().strftime("%d/%m/%Y %H:%M"),
                "attivo":           True,
            }
            state["tornei_programmati"].append(nuovo)
            save_state(state)
            st.session_state.tp_cover_b64 = None
            st.success("Torneo " + nome.strip() + " creato con successo!")
            st.rerun()


def _render_lista_tornei_admin(state):
    tornei = state.get("tornei_programmati", [])
    if not tornei:
        st.info("Nessun torneo in programma. Creane uno dalla tab Crea Nuovo Torneo.")
        return

    for torneo in tornei:
        nome     = torneo.get("nome_programmato", "")
        data_t   = torneo.get("data_programmata", "")
        luogo    = torneo.get("luogo", "")
        iscritti = torneo.get("iscritti", [])
        attivo   = torneo.get("attivo", True)
        n_iscr   = len(iscritti)
        tid      = torneo.get("id", "")

        stato_icon = "verde" if attivo else "rosso"
        with st.expander(
            ("🟢 " if attivo else "🔴 ") + nome + " — " + data_t + " · " + str(n_iscr) + " iscritti",
            expanded=False
        ):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown("**Luogo:** " + luogo)
                st.markdown("**Formato:** " + torneo.get("formato_set","") + " · " + str(torneo.get("punteggio_max","")) + " pt")
                st.markdown("**Tabellone:** " + torneo.get("tipo_tabellone",""))
                st.markdown("**Quota:** €" + str(torneo.get("quota", 0)))
                st.markdown("**Creato il:** " + torneo.get("creato_il",""))
            with col2:
                st.markdown("**Iscritti (" + str(n_iscr) + "):**")
                if iscritti:
                    for entry in iscritti:
                        if isinstance(entry, dict):
                            comp = entry.get("compagno_nome", "—")
                            st.markdown("• " + entry.get("email","") + "  *(compagno: " + comp + ")*")
                        else:
                            st.markdown("• " + str(entry))
                else:
                    st.caption("Nessun iscritto ancora.")
            with col3:
                label_tog = "Disattiva" if attivo else "Attiva"
                if st.button(label_tog, key="tog_" + tid, use_container_width=True):
                    torneo["attivo"] = not attivo
                    save_state(state)
                    st.rerun()
                if st.button("Elimina", key="del_" + tid, use_container_width=True):
                    state["tornei_programmati"].remove(torneo)
                    save_state(state)
                    st.rerun()

            if torneo.get("copertina_b64"):
                st.markdown(
                    '<img src="data:image/jpeg;base64,' + torneo["copertina_b64"] + '" '
                    'style="width:100%;max-height:180px;object-fit:cover;'
                    'border-radius:8px;margin-top:12px">',
                    unsafe_allow_html=True
                )


# ─── UTENTI: Griglia card cliccabili ─────────────────────────────────────────

def render_tornei_in_programma(state, user=None):
    """Pagina pubblica con griglia di card cliccabili."""
    state.setdefault("tornei_programmati", [])

    # Se c'e' un torneo selezionato mostra il dettaglio
    tid_sel = st.session_state.get("torneo_dettaglio_id")
    if tid_sel:
        torneo_sel = next(
            (t for t in state["tornei_programmati"] if t["id"] == tid_sel), None
        )
        if torneo_sel:
            _render_dettaglio_torneo(torneo_sel, user, state)
            return
        else:
            st.session_state.torneo_dettaglio_id = None

    st.markdown("## Tornei in Programma")

    tornei_attivi = [t for t in state["tornei_programmati"] if t.get("attivo", True)]

    if not tornei_attivi:
        st.markdown("""
        <div style="background:#13131a;border:2px dashed #2a2a3a;border-radius:12px;
            padding:48px;text-align:center">
            <div style="font-size:3rem;margin-bottom:12px">🏐</div>
            <div style="font-size:1.1rem;font-weight:700;color:#888">Nessun torneo in programma</div>
            <div style="font-size:0.8rem;color:#555;margin-top:8px">Controlla piu tardi!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    def _parse_date(t):
        try:
            return datetime.strptime(t.get("data_programmata", "01/01/2099"), "%d/%m/%Y")
        except Exception:
            return datetime(2099, 1, 1)

    tornei_ord = sorted(tornei_attivi, key=_parse_date)

    cols_per_row = 2
    for row_start in range(0, len(tornei_ord), cols_per_row):
        chunk = tornei_ord[row_start:row_start + cols_per_row]
        cols  = st.columns(len(chunk))
        for col, torneo in zip(cols, chunk):
            with col:
                _render_card_cliccabile(torneo, user, state)


def _is_user_iscritto(iscritti, user_email):
    for e in iscritti:
        if isinstance(e, dict) and e.get("email") == user_email:
            return True
        if isinstance(e, str) and e == user_email:
            return True
    return False


def _render_card_cliccabile(torneo, user, state):
    """Card torneo cliccabile che apre la schermata dettaglio."""
    nome      = torneo.get("nome_programmato", "Torneo")
    data_t    = torneo.get("data_programmata", "")
    luogo     = torneo.get("luogo", "")
    formato   = torneo.get("formato_set", "")
    quota     = torneo.get("quota", 0)
    copertina = torneo.get("copertina_b64")
    iscritti  = torneo.get("iscritti", [])
    tid       = torneo.get("id", "")

    user_email   = user.get("email", "") if user else ""
    gia_iscritto = _is_user_iscritto(iscritti, user_email)
    n_iscr       = len(iscritti)
    border_color = "#00c851" if gia_iscritto else "#e8002d"

    if copertina:
        st.markdown(
            '<img src="data:image/jpeg;base64,' + copertina + '" '
            'style="width:100%;height:180px;object-fit:cover;'
            'border-radius:12px 12px 0 0;display:block">',
            unsafe_allow_html=True
        )

    n_label = str(n_iscr) + (" iscritto" if n_iscr == 1 else " iscritti")
    iscr_badge = ' &nbsp;·&nbsp; <span style="color:#00c851;font-weight:700">Sei iscritto/a</span>' if gia_iscritto else ""

    st.markdown(
        '<div style="background:#13131a;border:2px solid ' + border_color + ';'
        'border-radius:' + ('0 0 12px 12px' if copertina else '12px') + ';'
        'padding:16px 18px 12px">'
        '<div style="font-family:Barlow Condensed,sans-serif;font-size:1.2rem;'
        'font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:1px;'
        'margin-bottom:8px">' + nome + '</div>'
        '<div style="font-size:0.8rem;color:#888;line-height:1.9;margin-bottom:8px">'
        '&#128197; <strong style="color:#ccc">' + data_t + '</strong><br>'
        '&#128205; <strong style="color:#ccc">' + luogo + '</strong><br>'
        '&#127944; ' + formato + ' &nbsp;&middot;&nbsp; '
        '&#128182; <strong style="color:#ffd700">&euro;' + str(quota) + '</strong>'
        '</div>'
        '<div style="font-size:0.72rem;color:#555;border-top:1px solid #2a2a3a;padding-top:8px">'
        '&#128101; ' + n_label + iscr_badge +
        '</div></div>',
        unsafe_allow_html=True
    )

    btn_lbl = "Vedi dettagli" + (" · Sei iscritto/a" if gia_iscritto else " e iscriviti")
    if st.button(btn_lbl, key="open_" + tid, use_container_width=True):
        st.session_state.torneo_dettaglio_id = tid
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


# ─── Schermata dettaglio torneo ───────────────────────────────────────────────

def _render_dettaglio_torneo(torneo, user, state):
    nome      = torneo.get("nome_programmato", "Torneo")
    data_t    = torneo.get("data_programmata", "")
    luogo     = torneo.get("luogo", "")
    formato   = torneo.get("formato_set", "")
    punteggio = torneo.get("punteggio_max", "")
    tipo      = torneo.get("tipo_tabellone", "")
    desc      = torneo.get("descrizione", "")
    quota     = torneo.get("quota", 0)
    copertina = torneo.get("copertina_b64")
    iscritti  = torneo.get("iscritti", [])
    tid       = torneo.get("id", "")

    user_email   = user.get("email", "") if user else ""
    gia_iscritto = _is_user_iscritto(iscritti, user_email)
    entry_utente = None
    if gia_iscritto and user:
        for e in iscritti:
            if isinstance(e, dict) and e.get("email") == user_email:
                entry_utente = e
                break
            if isinstance(e, str) and e == user_email:
                entry_utente = {"email": user_email, "compagno_nome": "Da definire"}
                break

    if st.button("← Torna ai tornei", key="btn_back_tornei"):
        st.session_state.torneo_dettaglio_id = None
        st.rerun()

    # Copertina hero
    if copertina:
        st.markdown(
            '<img src="data:image/jpeg;base64,' + copertina + '" '
            'style="width:100%;max-height:340px;object-fit:cover;'
            'border-radius:16px;margin-bottom:20px;'
            'box-shadow:0 8px 40px rgba(232,0,45,0.3)">',
            unsafe_allow_html=True
        )

    # Titolo + badge
    badge = ""
    if gia_iscritto:
        badge = (' <span style="background:#00c851;color:#000;font-size:0.7rem;'
                 'font-weight:800;padding:4px 12px;border-radius:20px;'
                 'letter-spacing:1px;vertical-align:middle;margin-left:10px">ISCRITTO/A</span>')

    st.markdown(
        '<div style="font-family:Barlow Condensed,sans-serif;font-size:2.2rem;'
        'font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:2px;'
        'margin-bottom:20px;line-height:1.2">'
        '🏐 ' + nome + badge + '</div>',
        unsafe_allow_html=True
    )

    # Griglia info
    col_i1, col_i2, col_i3 = st.columns(3)
    _info_box(col_i1, "📅", "Data",  data_t)
    _info_box(col_i2, "📍", "Luogo", luogo)
    _info_box_gold(col_i3, "💶", "Quota", "€" + str(quota))

    st.markdown("<br>", unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px">'
            '<div style="color:#e8002d;font-size:0.65rem;letter-spacing:2px;'
            'text-transform:uppercase;font-weight:700;margin-bottom:10px">Dettagli Gara</div>'
            '<div style="font-size:0.85rem;color:#ccc;line-height:2">'
            '🏐 Formato: <strong>' + formato + '</strong><br>'
            '🎯 Punteggio max: <strong>' + str(punteggio) + ' pt</strong><br>'
            '📊 Tabellone: <strong>' + tipo + '</strong><br>'
            '👥 Iscritti: <strong>' + str(len(iscritti)) + '</strong>'
            '</div></div>',
            unsafe_allow_html=True
        )
    with col_d2:
        if desc:
            st.markdown(
                '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;padding:16px">'
                '<div style="color:#e8002d;font-size:0.65rem;letter-spacing:2px;'
                'text-transform:uppercase;font-weight:700;margin-bottom:10px">Regolamento e Note</div>'
                '<div style="font-size:0.85rem;color:#aaa;line-height:1.6">' + desc + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Blocco iscrizione ─────────────────────────────────────────────────────
    if not user:
        st.markdown(
            '<div style="background:#13131a;border:2px dashed #e8002d;border-radius:12px;'
            'padding:24px;text-align:center">'
            '<div style="font-size:1.5rem;margin-bottom:8px">🔐</div>'
            '<div style="color:#fff;font-weight:700;margin-bottom:4px">'
            'Accedi o registrati per iscriverti</div>'
            '<div style="color:#888;font-size:0.82rem">'
            'Usa il tab Atleta nella schermata di login.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        _render_lista_iscritti(iscritti)
        return

    if gia_iscritto:
        comp_nome = entry_utente.get("compagno_nome", "Da definire") if entry_utente else "Da definire"
        st.markdown(
            '<div style="background:#0a2a0a;border:2px solid #00c851;border-radius:12px;'
            'padding:20px 24px;margin-bottom:16px">'
            '<div style="font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;'
            'color:#00c851;font-weight:700;margin-bottom:8px">Sei iscritto/a</div>'
            '<div style="font-size:0.9rem;color:#ccc">'
            'Compagno di squadra: <strong style="color:#fff">' + comp_nome + '</strong>'
            '</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Annulla la mia iscrizione", key="disiscrivi_" + tid, use_container_width=True):
            torneo["iscritti"] = [
                e for e in iscritti
                if not (isinstance(e, dict) and e.get("email") == user_email)
                and not (isinstance(e, str) and e == user_email)
            ]
            save_state(state)
            _send_email_annullamento(user, torneo)
            st.success("Iscrizione annullata.")
            st.rerun()
    else:
        st.markdown("### 🏐 Iscriviti al Torneo")

        tutti_atleti = state.get("atleti", [])
        nome_utente  = (user.get("nome","") + " " + user.get("cognome","")).strip().lower()
        atleti_disp  = [a for a in tutti_atleti if a["nome"].lower() != nome_utente]

        opzioni = ["— Senza compagno / da definire —"] + [a["nome"] for a in atleti_disp]

        scelta = st.selectbox(
            "Scegli il tuo compagno di squadra",
            options=opzioni,
            key="compagno_sel_" + tid,
            help="Puoi scegliere tra gli atleti registrati nell'app."
        )

        compagno_nome   = scelta if scelta != "— Senza compagno / da definire —" else None
        compagno_atleta = next((a for a in atleti_disp if a["nome"] == compagno_nome), None) if compagno_nome else None

        if st.button("CONFERMA ISCRIZIONE", key="iscr_" + tid + "_" + user_email,
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
                _email_iscrizione_torneo(user, {
                    "nome": nome, "data": data_t, "luogo": luogo,
                    "formato_set": formato, "punteggio_max": punteggio,
                    "tipo_tabellone": tipo,
                })
            except Exception:
                pass
            st.success("Iscrizione confermata! Compagno: " + (compagno_nome or "Da definire"))
            st.info("Riceverai una email di conferma a breve.")
            st.rerun()

    _render_lista_iscritti(iscritti)


def _render_lista_iscritti(iscritti):
    if not iscritti:
        return
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 👥 Iscritti al Torneo")
    for idx, entry in enumerate(iscritti, 1):
        if isinstance(entry, dict):
            en     = entry.get("nome", entry.get("email", ""))
            comp   = entry.get("compagno_nome", "Da definire")
            data_i = entry.get("data_iscrizione", "")
        else:
            en     = str(entry)
            comp   = ""
            data_i = ""

        row = (
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:8px;'
            'padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;'
            'align-items:center;font-size:0.82rem">'
            '<span style="color:#fff;font-weight:600">#' + str(idx) + ' ' + en + '</span>'
            + ('<span style="color:#888">🤝 ' + comp + '</span>' if comp else '')
            + ('<span style="color:#555;font-size:0.7rem">' + data_i + '</span>' if data_i else '')
            + '</div>'
        )
        st.markdown(row, unsafe_allow_html=True)


def _info_box(col, icon, label, value):
    with col:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;'
            'padding:16px;text-align:center">'
            '<div style="font-size:1.8rem">' + icon + '</div>'
            '<div style="color:#888;font-size:0.65rem;letter-spacing:2px;'
            'text-transform:uppercase;margin:4px 0">' + label + '</div>'
            '<div style="font-weight:800;color:#fff;font-size:0.95rem">' + str(value) + '</div>'
            '</div>',
            unsafe_allow_html=True
        )


def _info_box_gold(col, icon, label, value):
    with col:
        st.markdown(
            '<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;'
            'padding:16px;text-align:center">'
            '<div style="font-size:1.8rem">' + icon + '</div>'
            '<div style="color:#888;font-size:0.65rem;letter-spacing:2px;'
            'text-transform:uppercase;margin:4px 0">' + label + '</div>'
            '<div style="font-weight:800;color:#ffd700;font-size:1.1rem">' + str(value) + '</div>'
            '</div>',
            unsafe_allow_html=True
        )


def _send_email_annullamento(user, torneo):
    try:
        from auth_manager import _send_email, ADMIN_EMAIL
        nome_utente = user.get("nome","") + " " + user.get("cognome","")
        nome_torneo = torneo.get("nome_programmato", "Torneo")
        html = ("<h2>Iscrizione Annullata</h2>"
                "<p><strong>" + nome_utente + "</strong> ha annullato l'iscrizione a "
                "<strong>" + nome_torneo + "</strong>.</p>"
                "<p>Data: " + datetime.now().strftime("%d/%m/%Y %H:%M") + "</p>")
        _send_email(ADMIN_EMAIL, "Disiscrizione: " + nome_utente + " da " + nome_torneo, html)
    except Exception:
        pass
