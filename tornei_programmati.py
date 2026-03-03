"""
tornei_programmati.py — MBT-BVL 2.0
Gestione tornei in programma: l'admin li crea con copertina,
gli utenti li vedono e si iscrivono.
"""
import streamlit as st
import base64
import random
from datetime import datetime
from data_manager import save_state


# ─── ADMIN: Crea Torneo Programmato ──────────────────────────────────────────

def render_admin_tornei_programmati(state):
    """Pagina admin per creare e gestire tornei programmati."""
    st.markdown("## 📅 Tornei in Programma")
    st.caption("Crea tornei futuri con copertina e dettagli. Gli atleti potranno iscriversi dall'app.")

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
        nome = st.text_input("Nome del Torneo *", key="tp_nome",
                              placeholder="Es. MBT Summer Open 2025")
        data = st.text_input("Data del Torneo *", key="tp_data",
                              placeholder="GG/MM/AAAA",
                              value=datetime.today().strftime("%d/%m/%Y"))
        luogo = st.text_input("Luogo *", key="tp_luogo",
                               placeholder="Es. Catania, Lido La Playa")
    with col2:
        formato = st.selectbox("Formato Set", ["Set Unico", "Best of 3", "Best of 5"],
                                key="tp_formato")
        punteggio = st.selectbox("Punteggio Massimo", [11, 15, 21, 25], index=2,
                                  key="tp_punteggio")
        tipo = st.selectbox("Tipo Tabellone",
                             ["Gironi + Playoff", "Girone Unico", "Eliminazione Diretta"],
                             key="tp_tipo")

    desc = st.text_area("Descrizione / Regolamento", key="tp_desc",
                         placeholder="Inserisci informazioni aggiuntive sul torneo, premi, regole speciali...",
                         height=100)
    quota = st.number_input("Quota di iscrizione (€)", min_value=0.0, value=20.0,
                             step=5.0, key="tp_quota")

    st.markdown("#### 🖼️ Copertina del Torneo")
    copertina_file = st.file_uploader("Carica copertina (JPG, PNG)",
                                       type=["jpg", "jpeg", "png", "webp"],
                                       key="tp_copertina")
    copertina_b64 = None
    if copertina_file:
        copertina_b64 = base64.b64encode(copertina_file.read()).decode()
        ext = copertina_file.type.split("/")[-1]
        st.markdown(f'<img src="data:image/{ext};base64,{copertina_b64}" '
                    f'style="width:100%;max-height:220px;object-fit:cover;border-radius:10px;margin-top:8px">',
                    unsafe_allow_html=True)

    st.markdown("---")
    if st.button("➕ CREA TORNEO IN PROGRAMMA", use_container_width=True,
                 type="primary", key="btn_crea_torneo_prog"):
        if not nome.strip():
            st.error("Inserisci il nome del torneo.")
            return
        if not data.strip():
            st.error("Inserisci la data del torneo.")
            return
        if not luogo.strip():
            st.error("Inserisci il luogo del torneo.")
            return

        nuovo_torneo = {
            "id": f"tp_{random.randint(10000,99999)}",
            "nome_programmato": nome.strip(),
            "data_programmata": data.strip(),
            "luogo": luogo.strip(),
            "formato_set": formato,
            "punteggio_max": punteggio,
            "tipo_tabellone": tipo,
            "descrizione": desc.strip(),
            "quota": quota,
            "copertina_b64": copertina_b64,
            "iscritti": [],
            "creato_il": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "attivo": True,
        }
        state["tornei_programmati"].append(nuovo_torneo)
        save_state(state)
        st.success(f"✅ Torneo **{nome}** creato con successo!")
        st.rerun()


def _render_lista_tornei_admin(state):
    tornei = state.get("tornei_programmati", [])
    if not tornei:
        st.info("Nessun torneo in programma. Crea il primo dalla tab '➕ Crea Nuovo Torneo'.")
        return

    for i, torneo in enumerate(tornei):
        nome = torneo.get("nome_programmato", "—")
        data = torneo.get("data_programmata", "—")
        luogo = torneo.get("luogo", "—")
        iscritti = torneo.get("iscritti", [])
        attivo = torneo.get("attivo", True)

        with st.expander(f"{'🟢' if attivo else '🔴'} {nome} — {data} · {len(iscritti)} iscritti",
                         expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**📍 Luogo:** {luogo}")
                st.markdown(f"**🏐 Formato:** {torneo.get('formato_set','—')} · {torneo.get('punteggio_max','—')} pt")
                st.markdown(f"**📊 Tabellone:** {torneo.get('tipo_tabellone','—')}")
                st.markdown(f"**💶 Quota:** €{torneo.get('quota', 0):.2f}")
                st.markdown(f"**📝 Creato il:** {torneo.get('creato_il','—')}")
            with col2:
                st.markdown(f"**👥 Iscritti ({len(iscritti)}):**")
                if iscritti:
                    for email in iscritti:
                        st.markdown(f"• {email}")
                else:
                    st.caption("Nessun iscritto ancora.")
            with col3:
                # Toggle attivo/disattivo
                label_toggle = "🔴 Disattiva" if attivo else "🟢 Attiva"
                if st.button(label_toggle, key=f"toggle_tp_{torneo['id']}", use_container_width=True):
                    torneo["attivo"] = not attivo
                    save_state(state)
                    st.rerun()
                if st.button("🗑️ Elimina", key=f"del_tp_{torneo['id']}", use_container_width=True):
                    state["tornei_programmati"].remove(torneo)
                    save_state(state)
                    st.rerun()

            if torneo.get("copertina_b64"):
                st.markdown('<div style="margin-top:10px">', unsafe_allow_html=True)
                st.markdown(f'<img src="data:image/jpeg;base64,{torneo["copertina_b64"]}" '
                            f'style="width:100%;max-height:180px;object-fit:cover;border-radius:8px">',
                            unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)


# ─── UTENTI: Visualizza Tornei in Programma ──────────────────────────────────

def render_tornei_in_programma(state, user=None):
    """Pagina pubblica — mostra tutti i tornei in programma agli utenti."""
    st.markdown("## 📅 Tornei in Programma")

    state.setdefault("tornei_programmati", [])
    tornei_attivi = [t for t in state["tornei_programmati"] if t.get("attivo", True)]

    if not tornei_attivi:
        st.markdown("""
        <div style="background:#13131a;border:2px dashed #2a2a3a;border-radius:12px;
            padding:48px;text-align:center;color:#555">
            <div style="font-size:3rem;margin-bottom:12px">🏐</div>
            <div style="font-size:1.1rem;font-weight:700;color:#888">Nessun torneo in programma</div>
            <div style="font-size:0.8rem;margin-top:8px">Controlla più tardi per nuovi tornei!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Ordina per data
    def _parse_date(t):
        try:
            return datetime.strptime(t.get("data_programmata", "01/01/2099"), "%d/%m/%Y")
        except Exception:
            return datetime(2099, 1, 1)

    tornei_ordinati = sorted(tornei_attivi, key=_parse_date)

    # Griglia card
    cols_per_row = 2
    for row_start in range(0, len(tornei_ordinati), cols_per_row):
        chunk = tornei_ordinati[row_start:row_start + cols_per_row]
        cols = st.columns(len(chunk))
        for col, torneo in zip(cols, chunk):
            with col:
                _render_card_utente(torneo, user, state)


def _render_card_utente(torneo: dict, user, state):
    """Card singola torneo per utente."""
    nome    = torneo.get("nome_programmato", "Torneo")
    data    = torneo.get("data_programmata", "—")
    luogo   = torneo.get("luogo", "—")
    formato = torneo.get("formato_set", "—")
    desc    = torneo.get("descrizione", "")
    quota   = torneo.get("quota", 0)
    copertina = torneo.get("copertina_b64")
    iscritti  = torneo.get("iscritti", [])
    tid       = torneo.get("id", "")

    user_email    = user.get("email", "") if user else ""
    gia_iscritto  = user_email in iscritti
    border_color  = "#00c851" if gia_iscritto else "#e8002d"

    # Copertina
    if copertina:
        st.markdown(
            f'<img src="data:image/jpeg;base64,{copertina}" '
            f'style="width:100%;height:180px;object-fit:cover;'
            f'border-radius:12px 12px 0 0;display:block;margin-bottom:-4px">',
            unsafe_allow_html=True
        )

    st.markdown(f"""
    <div style="background:#13131a;border:2px solid {border_color};
        border-radius:{'0 0 12px 12px' if copertina else '12px'};
        padding:18px 20px;margin-bottom:4px">
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;
            font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:1px;
            margin-bottom:8px">{nome}</div>
        <div style="display:flex;flex-direction:column;gap:4px;font-size:0.8rem;color:#888;margin-bottom:10px">
            <span>📅 <strong style="color:#ccc">{data}</strong></span>
            <span>📍 <strong style="color:#ccc">{luogo}</strong></span>
            <span>🏐 {formato}</span>
            <span>💶 Quota: <strong style="color:#ffd700">€{quota:.2f}</strong></span>
        </div>
        {f'<div style="font-size:0.78rem;color:#aaa;margin-bottom:10px;line-height:1.5">{desc}</div>' if desc else ''}
        <div style="font-size:0.72rem;color:#555;border-top:1px solid #2a2a3a;padding-top:8px;margin-top:4px">
            👥 {len(iscritti)} iscritti
            {' · <span style="color:#00c851;font-weight:700">✅ Sei iscritto/a</span>' if gia_iscritto else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pulsante iscrizione
    if user:
        if not gia_iscritto:
            if st.button(f"✅ Iscriviti", key=f"iscr_{tid}_{user_email}",
                          use_container_width=True, type="primary"):
                from auth_manager import _iscrivi_utente_torneo
                _iscrivi_utente_torneo(torneo, user, state)
        else:
            if st.button(f"❌ Annulla iscrizione", key=f"disiscr_{tid}_{user_email}",
                          use_container_width=True):
                from auth_manager import _disiscr_utente_torneo
                _disiscr_utente_torneo(torneo, user, state)
    else:
        st.markdown("""
        <div style="background:#1a1a1a;border:1px solid #333;border-radius:8px;
            padding:10px;text-align:center;font-size:0.78rem;color:#666;margin-top:4px">
            👁️ Accedi o registrati per iscriverti
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
