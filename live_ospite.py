"""
live_ospite.py — Pagina Live per Ospiti
Mostra in tempo reale: gironi, classifiche, partite, orari, campi e progressi.
Si aggiorna automaticamente ogni 30 secondi.
"""
import streamlit as st
from data_manager import get_squadra_by_id, get_atleta_by_id, classifica_girone


def render_live_ospite(state):
    """Entry point principale per la vista live ospite."""

    torneo = state.get("torneo", {})
    nome_torneo = torneo.get("nome", "Torneo in Corso")
    fase = state.get("fase", "setup")
    num_campi = int(torneo.get("num_campi", 1))
    orario_inizio = torneo.get("orario_inizio", "")
    data_torneo = torneo.get("data", "")

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a0a0f,#1a0a0f);
         border:2px solid #e8002d;border-radius:16px;padding:20px 24px;
         margin-bottom:20px;text-align:center">
        <div style="font-size:0.65rem;letter-spacing:4px;color:#e8002d;
             text-transform:uppercase;font-weight:700;margin-bottom:6px">
            🔴 LIVE
        </div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:2rem;
             font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:2px">
            {nome_torneo}
        </div>
        <div style="color:#888;font-size:0.8rem;margin-top:6px">
            {"📅 " + data_torneo if data_torneo else ""}
            {"  ·  ⏰ Inizio " + orario_inizio if orario_inizio else ""}
            {"  ·  🏖️ " + str(num_campi) + (" campo" if num_campi == 1 else " campi") if num_campi else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh ogni 30 secondi
    st.markdown("""
    <script>
    setTimeout(function(){ window.location.reload(); }, 30000);
    </script>
    """, unsafe_allow_html=True)

    if fase == "setup":
        st.info("⏳ Il torneo non è ancora iniziato. Torna presto!")
        return

    if fase == "proclamazione":
        _render_podio_live(state)
        return

    # ── Tabs vista ospite ────────────────────────────────────────────────────
    tabs = st.tabs(["📋 Programma", "🏐 Gironi", "⚡ Bracket", "📊 Classifiche"])

    with tabs[0]:
        _render_programma(state)
    with tabs[1]:
        _render_gironi_live(state)
    with tabs[2]:
        _render_bracket_live(state)
    with tabs[3]:
        _render_classifiche_live(state)


def _render_programma(state):
    """Mostra tutte le partite raggruppate per campo e orario."""
    torneo = state.get("torneo", {})
    num_campi = int(torneo.get("num_campi", 1))

    # Raccoglie tutte le partite
    tutte = []
    for girone in state.get("gironi", []):
        for p in girone.get("partite", []):
            tutte.append(("girone", girone.get("nome", ""), p))
    for p in state.get("bracket", []):
        tutte.append(("bracket", p.get("round", "Playoff"), p))
    for p in state.get("bracket_extra", []):
        tutte.append(("bracket", p.get("round", "Finale"), p))

    if not tutte:
        st.info("Nessuna partita programmata.")
        return

    # Separa confermate e non
    in_corso  = [(cat, lbl, p) for cat, lbl, p in tutte if not p.get("confermata") and not p.get("is_bye")]
    completate = [(cat, lbl, p) for cat, lbl, p in tutte if p.get("confermata") and not p.get("is_bye")]

    # ── Partite in programma ─────────────────────────────────────────────────
    if in_corso:
        st.markdown("### 🔴 Partite in Programma")
        # Raggruppa per campo
        for campo_n in range(1, num_campi + 1):
            partite_campo = [(cat, lbl, p) for cat, lbl, p in in_corso if p.get("campo") == campo_n]
            if not partite_campo:
                continue
            st.markdown(f"#### 🏖️ Campo {campo_n}")
            for cat, lbl, p in sorted(partite_campo, key=lambda x: x[2].get("orario_schedulato", "99:99")):
                _render_match_live_card(state, p, lbl, highlight=True)

        # Partite senza campo assegnato
        senza_campo = [(cat, lbl, p) for cat, lbl, p in in_corso if not p.get("campo")]
        if senza_campo:
            st.markdown("#### ⏳ Da Programmare")
            for cat, lbl, p in senza_campo:
                _render_match_live_card(state, p, lbl)

    # ── Partite completate ───────────────────────────────────────────────────
    if completate:
        with st.expander(f"✅ Risultati ({len(completate)} partite completate)", expanded=False):
            for cat, lbl, p in completate:
                _render_match_live_card(state, p, lbl, completed=True)


def _render_match_live_card(state, p, label="", highlight=False, completed=False):
    sq1 = get_squadra_by_id(state, p.get("sq1", ""))
    sq2 = get_squadra_by_id(state, p.get("sq2", ""))
    if not sq1 or not sq2:
        return

    nome1 = sq1.get("nome", "?")
    nome2 = sq2.get("nome", "?")
    set1  = p.get("set_sq1", 0)
    set2  = p.get("set_sq2", 0)
    campo  = p.get("campo")
    orario = p.get("orario_schedulato", "")
    punteggi = p.get("punteggi", [])
    parziali = " | ".join([f"{a}-{b}" for a, b in punteggi]) if punteggi else ""

    if completed:
        border = "#2a2a3a"
        status_html = f'<span style="color:#00c851;font-weight:700">✅ {set1}–{set2}</span>'
    elif highlight:
        border = "#e8002d"
        status_html = '<span style="color:#e8002d;font-weight:700;animation:blink 1s infinite">🔴 LIVE</span>'
    else:
        border = "#444"
        status_html = '<span style="color:#888">⏳ In attesa</span>'

    campo_str  = f"🏖️ Campo {campo}" if campo else ""
    orario_str = f"⏰ {orario}" if orario else ""
    info_str   = "  ·  ".join(filter(None, [campo_str, orario_str, label]))

    st.markdown(f"""
    <div style="background:#13131a;border:1px solid {border};border-radius:10px;
         padding:12px 16px;margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;align-items:center;
             font-size:0.65rem;color:#888;margin-bottom:8px">
            <span>{info_str}</span>
            {status_html}
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
            <div style="font-weight:800;font-size:0.95rem;color:#fff;flex:1">{nome1}</div>
            <div style="text-align:center;min-width:60px">
                <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.6rem;
                     font-weight:900;color:{'#ffd700' if completed else '#fff'}">
                    {set1 if completed else "–"}
                </div>
                {f'<div style="font-size:0.65rem;color:#555">{parziali}</div>' if parziali else ""}
            </div>
            <div style="font-weight:800;font-size:0.95rem;color:#fff;flex:1;text-align:right">{nome2}</div>
        </div>
        {f'<div style="text-align:center;font-size:1.2rem;font-weight:900;color:#ffd700;margin-top:4px">{set1}–{set2}</div>' if completed else ""}
    </div>
    """, unsafe_allow_html=True)


def _render_gironi_live(state):
    gironi = state.get("gironi", [])
    if not gironi:
        st.info("La fase a gironi non è ancora iniziata.")
        return

    passano = state["torneo"].get("squadre_per_girone_passano", 2)

    for girone in gironi:
        st.markdown(f"### {girone['nome']}")
        squadre_ord = classifica_girone(state, girone)

        html = """<table class="rank-table">
        <tr><th>#</th><th style="text-align:left">SQUADRA</th>
        <th>PTS</th><th>V</th><th>P</th><th>SV</th><th>SP</th></tr>"""

        for i, sq in enumerate(squadre_ord):
            qualif = "🟢" if i < passano else ""
            is_ghost = sq.get("is_ghost", False)
            style = "opacity:0.4" if is_ghost else ""
            color = "#00c851" if i < passano else "#ccc"
            html += f"""<tr style="{style}">
                <td><span style="font-weight:900;color:{color}">{i+1}</span></td>
                <td style="text-align:left;font-weight:700;color:{color}">{qualif} {sq['nome']}</td>
                <td style="font-weight:900;color:#ffd700">{sq['punti_classifica']}</td>
                <td style="color:#00c851">{sq['vittorie']}</td>
                <td style="color:#e8002d">{sq['sconfitte']}</td>
                <td>{sq['set_vinti']}</td><td>{sq['set_persi']}</td>
            </tr>"""
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        st.caption(f"🟢 Le prime {passano} si qualificano ai playoff")

        # Partite del girone
        with st.expander("🏐 Partite del girone", expanded=False):
            for p in girone.get("partite", []):
                if not p.get("is_bye"):
                    _render_match_live_card(state, p, girone["nome"], completed=p.get("confermata", False))
        st.markdown("---")


def _render_bracket_live(state):
    bracket = state.get("bracket", [])
    bracket_extra = state.get("bracket_extra", [])

    if not bracket and not bracket_extra:
        st.info("La fase eliminatoria non è ancora iniziata.")
        return

    # Raggruppa per round
    rounds = {}
    for p in bracket + bracket_extra:
        r = p.get("round", "Playoff")
        rounds.setdefault(r, []).append(p)

    round_order = [
        "⚡ Sessantaquattresimi di Finale", "⚡ Trentaduesimi di Finale",
        "⚡ Sedicesimi di Finale", "🏅 Ottavi di Finale",
        "🏅 Quarti di Finale", "🥇 Semifinali",
        "🥉 Finale 3°/4° Posto", "🏆 FINALE 1°/2° Posto", "⚡ Playoff"
    ]
    shown = [r for r in round_order if r in rounds]
    other = [r for r in rounds if r not in round_order]

    for rname in shown + other:
        st.markdown(f"### {rname}")
        for p in rounds[rname]:
            if not p.get("is_bye"):
                _render_match_live_card(state, p, rname, completed=p.get("confermata", False))


def _render_classifiche_live(state):
    """Classifica generale con tutte le squadre ordinate per punti."""
    squadre = [sq for sq in state.get("squadre", []) if not sq.get("is_ghost")]
    if not squadre:
        st.info("Nessuna squadra registrata.")
        return

    squadre_ord = sorted(
        squadre,
        key=lambda sq: (
            -sq.get("vittorie", 0),
            -sq.get("punti_classifica", 0),
            -(sq.get("set_vinti", 0) - sq.get("set_persi", 0))
        )
    )

    html = """<table class="rank-table">
    <tr>
        <th>#</th><th style="text-align:left">SQUADRA</th><th>ATLETI</th>
        <th>V</th><th>P</th><th>SV</th><th>SP</th><th>PTS</th>
    </tr>"""

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, sq in enumerate(squadre_ord):
        pos = i + 1
        med = medals.get(pos, str(pos))
        atleti_nomi = [
            a["nome"] for aid in sq.get("atleti", [])
            if (a := get_atleta_by_id(state, aid))
        ]
        html += f"""<tr>
            <td style="font-weight:900;color:#ffd700">{med}</td>
            <td style="text-align:left;font-weight:800;color:#fff">{sq['nome']}</td>
            <td style="color:#888;font-size:0.75rem">{" / ".join(atleti_nomi)}</td>
            <td style="color:#00c851;font-weight:700">{sq.get('vittorie',0)}</td>
            <td style="color:#e8002d">{sq.get('sconfitte',0)}</td>
            <td>{sq.get('set_vinti',0)}</td>
            <td>{sq.get('set_persi',0)}</td>
            <td style="font-weight:900;color:#ffd700">{sq.get('punti_classifica',0)}</td>
        </tr>"""

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


def _render_podio_live(state):
    podio = state.get("podio", [])
    if not podio:
        st.info("Torneo completato.")
        return

    st.markdown("## 🏆 Torneo Concluso!")
    medals = {1: ("🥇", "#ffd700"), 2: ("🥈", "#c0c0c0"), 3: ("🥉", "#cd7f32")}
    podio_sorted = sorted(podio, key=lambda x: x[0])

    cols = st.columns(len(podio_sorted))
    for col, (pos, sq_id) in zip(cols, podio_sorted):
        sq = get_squadra_by_id(state, sq_id)
        if not sq:
            continue
        med, color = medals.get(pos, ("", "#fff"))
        atleti_nomi = [
            a["nome"] for aid in sq.get("atleti", [])
            if (a := get_atleta_by_id(state, aid))
        ]
        with col:
            st.markdown(f"""
            <div style="background:#13131a;border:2px solid {color};border-radius:12px;
                 padding:20px;text-align:center">
                <div style="font-size:2.5rem">{med}</div>
                <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;
                     font-weight:900;color:{color}">{sq['nome']}</div>
                <div style="color:#888;font-size:0.75rem;margin-top:4px">
                    {" / ".join(atleti_nomi)}
                </div>
            </div>
            """, unsafe_allow_html=True)
