"""
live_ospite.py — Vista Live SOLO LETTURA per Ospiti
Mostra in tempo reale: programma, gironi, bracket, classifiche.
NESSUN bottone, input o widget interattivo — solo visione.
Auto-refresh ogni 30 secondi.
"""
import streamlit as st
from data_manager import get_squadra_by_id, get_atleta_by_id, classifica_girone


def render_live_ospite(state):
    torneo        = state.get("torneo", {})
    nome_torneo   = torneo.get("nome", "Torneo in Corso")
    fase          = state.get("fase", "setup")
    num_campi     = max(1, int(torneo.get("num_campi", 1)))
    orario_inizio = torneo.get("orario_inizio", "")
    data_torneo   = torneo.get("data", "")
    luogo         = torneo.get("luogo", "")
    formato_set   = torneo.get("formato_set", "")
    tipo          = torneo.get("modalita", torneo.get("tipo_tabellone", ""))
    tipo_gioco    = torneo.get("tipo_gioco", "")
    pmax          = torneo.get("punteggio_max", "")

    st.markdown("""
    <script>setTimeout(function(){ window.location.reload(); }, 30000);</script>
    <style>
    .rank-table{width:100%;border-collapse:collapse;font-size:.82rem}
    .rank-table th{background:#1a1a2a;color:#888;font-size:.62rem;letter-spacing:2px;
        text-transform:uppercase;padding:8px 10px;border-bottom:2px solid #2a2a3a}
    .rank-table td{padding:8px 10px;border-bottom:1px solid #1a1a2a;color:#ccc;vertical-align:middle}
    .rank-table tr:hover td{background:#16161f}
    .live-badge{animation:pulse 1.5s ease-in-out infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
    </style>
    """, unsafe_allow_html=True)

    meta_bits = "  ·  ".join(filter(None, [
        ("📅 " + data_torneo)   if data_torneo   else "",
        ("📍 " + luogo)         if luogo         else "",
        ("⏰ " + orario_inizio) if orario_inizio else "",
        (f"🏖️ {num_campi} campo{'i' if num_campi>1 else ''}") if num_campi else "",
        ("🏐 " + formato_set)   if formato_set   else "",
        ("👥 " + tipo_gioco)    if tipo_gioco    else "",
        ("📊 " + tipo)          if tipo          else "",
        (f"🎯 {pmax} pt")       if pmax          else "",
    ]))

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a0a0f,#1a0a0f);border:2px solid #e8002d;
         border-radius:16px;padding:22px 28px;margin-bottom:20px;text-align:center">
        <div class="live-badge" style="font-size:.62rem;letter-spacing:4px;color:#e8002d;
             text-transform:uppercase;font-weight:700;margin-bottom:8px">🔴 LIVE — Solo Visualizzazione</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:2.2rem;font-weight:900;
             color:#fff;text-transform:uppercase;letter-spacing:2px">{nome_torneo}</div>
        <div style="color:#666;font-size:.72rem;margin-top:10px;line-height:2">{meta_bits}</div>
    </div>""", unsafe_allow_html=True)

    if fase == "setup":
        st.markdown(_empty_box("⏳ Il torneo non è ancora iniziato. Questa pagina si aggiornerà automaticamente."))
        return
    if fase == "proclamazione":
        _render_podio_live(state)
        return

    tabs = st.tabs(["📋 Programma", "🏐 Gironi", "⚡ Playoff", "📊 Classifiche"])
    with tabs[0]: _render_programma(state)
    with tabs[1]: _render_gironi_live(state)
    with tabs[2]: _render_bracket_live(state)
    with tabs[3]: _render_classifiche_live(state)


def _render_programma(state):
    num_campi = max(1, int(state.get("torneo", {}).get("num_campi", 1)))
    tutte = []
    for g in state.get("gironi", []):
        for p in g.get("partite", []):
            if not p.get("is_bye"):
                tutte.append((g.get("nome","Girone"), p))
    for p in state.get("bracket",[]) + state.get("bracket_extra",[]):
        if not p.get("is_bye"):
            tutte.append((p.get("round","Playoff"), p))

    if not tutte:
        st.markdown(_empty_box("Nessuna partita schedulata.")); return

    in_prog  = [(l,p) for l,p in tutte if not p.get("confermata")]
    complete = [(l,p) for l,p in tutte if p.get("confermata")]

    if in_prog:
        st.markdown("### 🔴 Partite in Programma")
        for campo_n in range(1, num_campi+1):
            gruppo = sorted([(l,p) for l,p in in_prog if p.get("campo")==campo_n],
                            key=lambda x: x[1].get("orario_schedulato","99:99"))
            if not gruppo: continue
            st.markdown(f'<div style="display:inline-block;background:#1a1a0a;border:1px solid #ffd700;'
                        f'border-radius:6px;padding:4px 14px;font-size:.72rem;font-weight:800;'
                        f'color:#ffd700;letter-spacing:2px;text-transform:uppercase;margin:12px 0 6px">'
                        f'🏖️ CAMPO {campo_n}</div>', unsafe_allow_html=True)
            for l,p in gruppo:
                _card_match(state, p, l, "live")
        senza = [(l,p) for l,p in in_prog if not p.get("campo")]
        if senza:
            st.markdown("#### ⏳ Da programmare")
            for l,p in senza: _card_match(state, p, l, "pending")

    if complete:
        n = len(complete)
        st.markdown(f'<div style="margin-top:20px;padding-top:16px;border-top:1px solid #2a2a3a;'
                    f'color:#555;font-size:.65rem;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px">'
                    f'✅ Risultati ({n} {"partita completata" if n==1 else "partite completate"})</div>',
                    unsafe_allow_html=True)
        for l,p in complete[-6:]: _card_match(state, p, l, "done")
        if n > 6:
            st.markdown(f'<div style="color:#555;font-size:.72rem;text-align:center">… e altre {n-6} partite completate</div>',
                        unsafe_allow_html=True)


def _render_gironi_live(state):
    gironi = state.get("gironi", [])
    if not gironi:
        st.markdown(_empty_box("La fase a gironi non è ancora iniziata.")); return

    passano       = state["torneo"].get("squadre_per_girone_passano", 2)
    num_campi     = max(1, int(state["torneo"].get("num_campi",1)))
    girone_ded    = (len(gironi) == num_campi)

    for g_idx, girone in enumerate(gironi):
        campo_lbl = (f'<span style="color:#ffd700;font-size:.7rem;font-weight:700;background:#1a1a0a;'
                     f'border:1px solid #ffd700;border-radius:4px;padding:2px 8px;margin-left:10px">'
                     f'🏖️ Campo {g_idx+1}</span>') if girone_ded else ""
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:18px 0 8px">'
                    f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.3rem;'
                    f'font-weight:900;color:#fff;text-transform:uppercase">{girone["nome"]}</span>'
                    f'{campo_lbl}</div>', unsafe_allow_html=True)

        sq_ord = classifica_girone(state, girone)
        rows = ""
        for i, sq in enumerate(sq_ord):
            q = i < passano
            c = "#00c851" if q else "#ccc"
            op = "opacity:.3;" if sq.get("is_ghost") else ""
            sv, sp = sq.get("set_vinti",0), sq.get("set_persi",0)
            rows += (f'<tr style="{op}"><td style="font-weight:900;color:{c};text-align:center">{i+1}</td>'
                     f'<td style="font-weight:700;color:{c}">{"🟢 " if q else ""}{sq["nome"]}</td>'
                     f'<td style="font-weight:900;color:#ffd700;text-align:center">{sq["punti_classifica"]}</td>'
                     f'<td style="color:#00c851;text-align:center">{sq["vittorie"]}</td>'
                     f'<td style="color:#e8002d;text-align:center">{sq["sconfitte"]}</td>'
                     f'<td style="color:#888;text-align:center">{sv}/{sp}</td></tr>')

        st.markdown(f'<table class="rank-table"><tr>'
                    f'<th style="text-align:center;width:36px">#</th><th style="text-align:left">Squadra</th>'
                    f'<th style="text-align:center">Punti</th><th style="text-align:center">V</th>'
                    f'<th style="text-align:center">P</th><th style="text-align:center">Set V/P</th>'
                    f'</tr>{rows}</table>'
                    f'<div style="font-size:.65rem;color:#555;margin:6px 0 12px">🟢 Prime {passano} qualificate ai playoff</div>',
                    unsafe_allow_html=True)

        pgg = sorted([p for p in girone.get("partite",[]) if not p.get("is_bye")],
                     key=lambda p: (p.get("orario_schedulato","99:99"), p.get("campo",99)))
        for p in pgg:
            _card_match(state, p, girone["nome"], "done" if p.get("confermata") else "live")
        st.markdown('<hr style="border-color:#1a1a2a;margin:4px 0 12px">', unsafe_allow_html=True)


def _render_bracket_live(state):
    bracket_all = state.get("bracket",[]) + state.get("bracket_extra",[])
    if not bracket_all:
        st.markdown(_empty_box("La fase eliminatoria non è ancora iniziata.")); return

    ROUND_ORDER = ["⚡ Sessantaquattresimi di Finale","⚡ Trentaduesimi di Finale",
                   "⚡ Sedicesimi di Finale","🏅 Ottavi di Finale","🏅 Quarti di Finale",
                   "🥇 Semifinali","🥉 Finale 3°/4° Posto","🏆 FINALE 1°/2° Posto","⚡ Playoff"]
    rm, ro = {}, []
    for p in bracket_all:
        r = p.get("round","Playoff")
        if r not in rm: rm[r]=[]; ro.append(r)
        rm[r].append(p)

    shown = [r for r in ROUND_ORDER if r in rm]
    other = [r for r in ro if r not in ROUND_ORDER]

    for rname in shown + other:
        partite = [p for p in rm[rname] if not p.get("is_bye")]
        if not partite: continue
        comp = sum(1 for p in partite if p.get("confermata"))
        st.markdown(f'<div style="background:#0d0d18;border-left:3px solid #e8002d;border-radius:0 8px 8px 0;'
                    f'padding:10px 16px;margin:20px 0 10px">'
                    f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.15rem;'
                    f'font-weight:900;color:#fff;text-transform:uppercase">{rname}</span>'
                    f'<span style="color:#555;font-size:.7rem;margin-left:12px">{comp}/{len(partite)} completate</span></div>',
                    unsafe_allow_html=True)

        campi = sorted(set(p.get("campo",0) for p in partite))
        if any(campi):
            for cn in campi:
                grp = sorted([p for p in partite if p.get("campo")==cn],
                             key=lambda p: p.get("orario_schedulato","99:99"))
                if not grp: continue
                if cn:
                    st.markdown(f'<div style="font-size:.65rem;font-weight:800;color:#ffd700;'
                                f'letter-spacing:2px;text-transform:uppercase;margin:6px 0 4px">'
                                f'🏖️ Campo {cn}</div>', unsafe_allow_html=True)
                for p in grp:
                    _card_match(state, p, rname, "done" if p.get("confermata") else "live")
        else:
            for p in sorted(partite, key=lambda p: p.get("orario_schedulato","99:99")):
                _card_match(state, p, rname, "done" if p.get("confermata") else "live")


def _render_classifiche_live(state):
    squadre = [sq for sq in state.get("squadre",[]) if not sq.get("is_ghost")]
    if not squadre:
        st.markdown(_empty_box("Nessuna squadra registrata.")); return

    sord = sorted(squadre, key=lambda sq: (
        -sq.get("vittorie",0), -sq.get("punti_classifica",0),
        -(sq.get("set_vinti",0)-sq.get("set_persi",0)), -sq.get("punti_fatti",0)))
    medals = {1:("🥇","#ffd700"),2:("🥈","#c0c0c0"),3:("🥉","#cd7f32")}
    rows = ""
    for i, sq in enumerate(sord):
        pos=i+1; med,mc=medals.get(pos,(str(pos),"#ccc"))
        nomi=[a["nome"] for aid in sq.get("atleti",[]) if (a:=get_atleta_by_id(state,aid))]
        sv,sp=sq.get("set_vinti",0),sq.get("set_persi",0)
        pf,ps=sq.get("punti_fatti",0),sq.get("punti_subiti",0)
        rows+=(f'<tr><td style="font-weight:900;color:{mc};text-align:center;font-size:1rem">{med}</td>'
               f'<td style="font-weight:800;color:#fff">{sq["nome"]}</td>'
               f'<td style="color:#666;font-size:.72rem">{" / ".join(nomi)}</td>'
               f'<td style="color:#00c851;font-weight:700;text-align:center">{sq.get("vittorie",0)}</td>'
               f'<td style="color:#e8002d;text-align:center">{sq.get("sconfitte",0)}</td>'
               f'<td style="text-align:center">{sv}</td><td style="text-align:center">{sp}</td>'
               f'<td style="color:#888;font-size:.72rem;text-align:center">{pf}–{ps}</td>'
               f'<td style="font-weight:900;color:#ffd700;text-align:center">{sq.get("punti_classifica",0)}</td></tr>')

    st.markdown(f'<table class="rank-table"><tr>'
                f'<th style="text-align:center">#</th><th style="text-align:left">Squadra</th>'
                f'<th style="text-align:left">Atleti</th><th style="text-align:center">V</th>'
                f'<th style="text-align:center">P</th><th style="text-align:center">SV</th>'
                f'<th style="text-align:center">SP</th><th style="text-align:center">Punti</th>'
                f'<th style="text-align:center">Cls</th></tr>{rows}</table>'
                f'<div style="font-size:.62rem;color:#444;margin-top:8px;text-align:right">'
                f'Aggiornamento automatico ogni 30 secondi</div>',
                unsafe_allow_html=True)


def _render_podio_live(state):
    podio = state.get("podio",[])
    st.markdown('<div style="text-align:center;margin-bottom:20px">'
                '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:2.5rem;'
                'font-weight:900;color:#ffd700;text-transform:uppercase;letter-spacing:3px">'
                '🏆 Torneo Concluso!</div></div>', unsafe_allow_html=True)
    if not podio: return
    medals={1:("🥇","#ffd700"),2:("🥈","#c0c0c0"),3:("🥉","#cd7f32")}
    cols=st.columns(len(podio))
    for col,(pos,sq_id) in zip(cols,sorted(podio,key=lambda x:x[0])):
        sq=get_squadra_by_id(state,sq_id)
        if not sq: continue
        med,color=medals.get(pos,("","#fff"))
        nomi=[a["nome"] for aid in sq.get("atleti",[]) if (a:=get_atleta_by_id(state,aid))]
        with col:
            st.markdown(f'<div style="background:#13131a;border:2px solid {color};border-radius:14px;'
                        f'padding:24px 16px;text-align:center">'
                        f'<div style="font-size:3rem;margin-bottom:8px">{med}</div>'
                        f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.4rem;'
                        f'font-weight:900;color:{color};text-transform:uppercase">{sq["nome"]}</div>'
                        f'<div style="color:#666;font-size:.75rem;margin-top:6px">{" / ".join(nomi)}</div></div>',
                        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _render_classifiche_live(state)


def _card_match(state, p, label="", status="live"):
    sq1=get_squadra_by_id(state,p.get("sq1",""))
    sq2=get_squadra_by_id(state,p.get("sq2",""))
    if not sq1 or not sq2: return
    nome1,nome2=sq1.get("nome","?"),sq2.get("nome","?")
    set1,set2=p.get("set_sq1",0),p.get("set_sq2",0)
    campo,orario=p.get("campo"),p.get("orario_schedulato","")
    punteggi=p.get("punteggi",[])
    parziali="  |  ".join(f"{a}–{b}" for a,b in punteggi) if punteggi else ""

    if status=="done":
        border,bg="#1e3a1e","#0d1a0d"
        tag=f'<span style="color:#00c851;font-size:.65rem;font-weight:700">✅ COMPLETATA</span>'
        score=f'<span style="font-size:1.8rem;font-weight:900;color:#00c851">{set1}–{set2}</span>'
        d1op = "opacity:.45;" if p.get("vincitore") and p["vincitore"]!=p.get("sq1") else ""
        d2op = "opacity:.45;" if p.get("vincitore") and p["vincitore"]!=p.get("sq2") else ""
    elif status=="live":
        border,bg="#3a1a1a","#130d0d"
        tag=f'<span class="live-badge" style="color:#e8002d;font-size:.65rem;font-weight:700">🔴 IN PROGRAMMA</span>'
        score='<span style="font-size:1.4rem;color:#555;font-weight:700">VS</span>'
        d1op=d2op=""
    else:
        border,bg="#2a2a2a","#0d0d0d"
        tag='<span style="color:#555;font-size:.65rem">⏳ IN ATTESA</span>'
        score='<span style="font-size:1.4rem;color:#333;font-weight:700">—</span>'
        d1op=d2op=""

    cs=f"🏖️ Campo {campo}" if campo else ""
    os=f"⏰ {orario}" if orario else ""
    info="  ·  ".join(filter(None,[cs,os,label]))
    parz_html=f'<div style="font-size:.62rem;color:#555;margin-top:2px">{parziali}</div>' if parziali else ""

    st.markdown(f'<div style="background:{bg};border:1px solid {border};border-radius:10px;'
                f'padding:12px 16px;margin-bottom:7px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
                f'<span style="font-size:.62rem;color:#555">{info}</span>{tag}</div>'
                f'<div style="display:flex;align-items:center;justify-content:space-between;gap:8px">'
                f'<div style="font-weight:800;font-size:.92rem;color:#fff;flex:1;{d1op}">{nome1}</div>'
                f'<div style="text-align:center;min-width:64px">{score}{parz_html}</div>'
                f'<div style="font-weight:800;font-size:.92rem;color:#fff;flex:1;text-align:right;{d2op}">{nome2}</div>'
                f'</div></div>', unsafe_allow_html=True)


def _empty_box(msg):
    return (f'<div style="background:#0d0d0d;border:1px dashed #2a2a3a;border-radius:10px;'
            f'padding:32px;text-align:center;color:#555;font-size:.85rem">{msg}</div>')
