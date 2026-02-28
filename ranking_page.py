"""
ranking_page.py — Ranking globale + Card FC26 Ultra-Premium v5
Carte dinamiche con tier system: Bronzo → GOAT con animazioni CSS avanzate
"""
import streamlit as st
import pandas as pd
from data_manager import (
    get_atleta_by_id, get_squadra_by_id, save_state,
    calcola_overall_fifa, get_card_type, get_trofei_atleta, TROFEI_DEFINIZIONE
)


def calcola_punti_ranking(pos, n_squadre):
    pts_massimi = n_squadre * 10
    return max(10, pts_massimi - ((pos - 1) * 10))


def build_ranking_data(state):
    atleti_stats = []
    for a in state["atleti"]:
        s = a["stats"]
        # Nuovi atleti partono con overall 40 (bronzo_raro) anche senza tornei
        rank_pts = 0
        for entry in s["storico_posizioni"]:
            if len(entry) == 3:
                tn, pos, n_sq = entry
            else:
                tn, pos = entry
                n_sq = _get_n_squadre_torneo(state, tn)
            rank_pts += calcola_punti_ranking(pos, n_sq)
        quoziente_punti = round(s["punti_fatti"] / max(s["set_vinti"] + s["set_persi"], 1), 2)
        quoziente_set = round(s["set_vinti"] / max(s["set_persi"], 1), 2)
        win_rate = round(s["vittorie"] / max(s["tornei"], 1) * 100, 1) if s["tornei"] > 0 else 0
        def _pos(entry): return entry[1]
        medaglie_oro = sum(1 for e in s["storico_posizioni"] if _pos(e) == 1)
        medaglie_argento = sum(1 for e in s["storico_posizioni"] if _pos(e) == 2)
        medaglie_bronzo = sum(1 for e in s["storico_posizioni"] if _pos(e) == 3)
        overall = calcola_overall_fifa(a)
        card_type = get_card_type(overall, s["tornei"], s["vittorie"])
        atleti_stats.append({
            "atleta": a, "id": a["id"], "nome": a["nome"],
            "tornei": s["tornei"], "vittorie": s["vittorie"], "sconfitte": s["sconfitte"],
            "set_vinti": s["set_vinti"], "set_persi": s["set_persi"],
            "punti_fatti": s["punti_fatti"], "punti_subiti": s["punti_subiti"],
            "quoziente_punti": quoziente_punti, "quoziente_set": quoziente_set,
            "win_rate": win_rate, "rank_pts": rank_pts,
            "oro": medaglie_oro, "argento": medaglie_argento, "bronzo": medaglie_bronzo,
            "storico": s["storico_posizioni"],
            "overall": overall, "card_type": card_type,
        })
    atleti_stats.sort(key=lambda x: (-x["rank_pts"], -x["oro"], -x["argento"], -x["win_rate"]))
    return atleti_stats


def _get_n_squadre_torneo(state, torneo_nome):
    return max(len(state["squadre"]), 4)


def render_ranking_page(state):
    st.markdown("## 🏅 Ranking Globale")
    ranking = build_ranking_data(state)
    if not ranking:
        st.info("Aggiungi atleti per visualizzare i profili e il ranking.")
        return
    tabs = st.tabs(["🏆 Classifica", "🃏 Card Giocatori", "🏅 Trofei", "👤 Carriera", "📄 Esporta PDF"])
    with tabs[0]:
        _render_classifica_completa(state, ranking)
    with tabs[1]:
        _render_carte_fifa(state, ranking)
    with tabs[2]:
        _render_trofei_page(state, ranking)
    with tabs[3]:
        _render_schede_atleti(state, ranking)
    with tabs[4]:
        _render_export_ranking_pdf(state, ranking)


def build_ranking_data_all(state):
    return build_ranking_data(state)


# ─── FC26 CARD SYSTEM ─────────────────────────────────────────────────────────

CARD_ANIMATIONS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;800;900&display=swap');
.fc26-card,.fc26-card *{-webkit-box-sizing:border-box;box-sizing:border-box}
@-webkit-keyframes shine_swipe{0%{left:-120%}40%,100%{left:150%}}
@keyframes shine_swipe{0%{left:-120%}40%,100%{left:150%}}
@-webkit-keyframes pulse_glow{0%,100%{opacity:.4}50%{opacity:1}}
@keyframes pulse_glow{0%,100%{opacity:.4}50%{opacity:1}}
@-webkit-keyframes lightning{0%,90%,100%{opacity:0}92%,96%{opacity:1}94%,98%{opacity:.3}}
@keyframes lightning{0%,90%,100%{opacity:0}92%,96%{opacity:1}94%,98%{opacity:.3}}
@-webkit-keyframes lightning2{0%,85%,100%{opacity:0}87%,91%{opacity:.9}89%,93%{opacity:.2}}
@keyframes lightning2{0%,85%,100%{opacity:0}87%,91%{opacity:.9}89%,93%{opacity:.2}}
@-webkit-keyframes wing_float{0%,100%{-webkit-transform:translateY(0) rotate(-8deg) scaleX(-1);transform:translateY(0) rotate(-8deg) scaleX(-1)}50%{-webkit-transform:translateY(-6px) rotate(-12deg) scaleX(-1);transform:translateY(-6px) rotate(-12deg) scaleX(-1)}}
@keyframes wing_float{0%,100%{transform:translateY(0) rotate(-8deg) scaleX(-1)}50%{transform:translateY(-6px) rotate(-12deg) scaleX(-1)}}
@-webkit-keyframes wing_float_r{0%,100%{-webkit-transform:translateY(0) rotate(8deg);transform:translateY(0) rotate(8deg)}50%{-webkit-transform:translateY(-6px) rotate(12deg);transform:translateY(-6px) rotate(12deg)}}
@keyframes wing_float_r{0%,100%{transform:translateY(0) rotate(8deg)}50%{transform:translateY(-6px) rotate(12deg)}}
@-webkit-keyframes golden_ribbon{0%{-webkit-transform:translateX(-110%) rotate(-30deg);transform:translateX(-110%) rotate(-30deg)}100%{-webkit-transform:translateX(210%) rotate(-30deg);transform:translateX(210%) rotate(-30deg)}}
@keyframes golden_ribbon{0%{transform:translateX(-110%) rotate(-30deg)}100%{transform:translateX(210%) rotate(-30deg)}}
@-webkit-keyframes ovr_pulse{0%,100%{text-shadow:0 0 8px currentColor}50%{text-shadow:0 0 20px currentColor,0 0 40px currentColor}}
@keyframes ovr_pulse{0%,100%{text-shadow:0 0 8px currentColor}50%{text-shadow:0 0 20px currentColor,0 0 40px currentColor}}
@-webkit-keyframes cloud_drift{0%,100%{-webkit-transform:translateX(0);transform:translateX(0)}50%{-webkit-transform:translateX(6px);transform:translateX(6px)}}
@keyframes cloud_drift{0%,100%{transform:translateX(0)}50%{transform:translateX(6px)}}
@-webkit-keyframes lava_glow{0%,100%{-webkit-box-shadow:0 0 30px rgba(255,50,0,.6),0 0 60px rgba(200,0,0,.3);box-shadow:0 0 30px rgba(255,50,0,.6),0 0 60px rgba(200,0,0,.3)}50%{-webkit-box-shadow:0 0 50px rgba(255,100,0,.9),0 0 100px rgba(255,50,0,.5);box-shadow:0 0 50px rgba(255,100,0,.9),0 0 100px rgba(255,50,0,.5)}}
@keyframes lava_glow{0%,100%{box-shadow:0 0 30px rgba(255,50,0,.6),0 0 60px rgba(200,0,0,.3)}50%{box-shadow:0 0 50px rgba(255,100,0,.9),0 0 100px rgba(255,50,0,.5)}}
@-webkit-keyframes crumble_shake{0%,100%{-webkit-transform:rotate(0);transform:rotate(0)}25%{-webkit-transform:rotate(-1deg) translateX(-1px);transform:rotate(-1deg) translateX(-1px)}75%{-webkit-transform:rotate(1deg) translateX(1px);transform:rotate(1deg) translateX(1px)}}
@keyframes crumble_shake{0%,100%{transform:rotate(0)}25%{transform:rotate(-1deg) translateX(-1px)}75%{transform:rotate(1deg) translateX(1px)}}
</style>
"""


def get_card_style(overall):
    """Restituisce la configurazione visuale per il tier dato l'overall."""
    if overall >= 95:
        return "goat"
    elif overall >= 90:
        return "toty_evoluto"
    elif overall >= 85:
        return "toty"
    elif overall >= 80:
        return "leggenda"
    elif overall >= 75:
        return "if_card"
    elif overall >= 70:
        return "eroe"
    elif overall >= 65:
        return "oro_raro"
    elif overall >= 60:
        return "oro_comune"
    elif overall >= 55:
        return "argento_raro"
    elif overall >= 50:
        return "argento_comune"
    elif overall >= 45:
        return "bronzo_raro"
    else:
        return "bronzo_comune"


def _get_foto_html(atleta, height="110px"):
    """Genera HTML immagine o placeholder sagoma atletica SVG."""
    if atleta.get("foto_b64"):
        return f'<img src="data:image/png;base64,{atleta["foto_b64"]}" style="width:100%;height:{height};object-fit:cover;object-position:top center;display:block">'
    # Placeholder SVG sagoma atletica stilizzata
    return f'''<div style="width:100%;height:{height};background:rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center">
<svg width="60" height="80" viewBox="0 0 60 80" fill="none" xmlns="http://www.w3.org/2000/svg" opacity="0.5">
  <circle cx="30" cy="16" r="10" fill="rgba(255,255,255,0.6)"/>
  <path d="M14 36 Q30 28 46 36 L44 60 Q30 56 16 60 Z" fill="rgba(255,255,255,0.5)"/>
  <path d="M16 60 L12 78" stroke="rgba(255,255,255,0.5)" stroke-width="5" stroke-linecap="round"/>
  <path d="M44 60 L48 78" stroke="rgba(255,255,255,0.5)" stroke-width="5" stroke-linecap="round"/>
  <path d="M14 36 L4 58" stroke="rgba(255,255,255,0.5)" stroke-width="5" stroke-linecap="round"/>
  <path d="M46 36 L56 58" stroke="rgba(255,255,255,0.5)" stroke-width="5" stroke-linecap="round"/>
</svg>
</div>'''


def render_card_html(a, size="normal", clickable=True):
    """
    Genera HTML per una card giocatore stile FC26 Ultimate Team.
    Cambia automaticamente aspetto in base all'overall.
    """
    overall = a["overall"]
    tier = get_card_style(overall)
    s = a["atleta"]["stats"]

    card_w = "210px" if size == "normal" else "170px"
    foto_h = "110px" if size == "normal" else "88px"
    ovr_size = "3.8rem" if size == "normal" else "3rem"
    name_size = "1.05rem" if size == "normal" else "0.88rem"
    cursor = "cursor:pointer;" if clickable else ""
    cid = f"card_{a['id']}"

    foto_html = _get_foto_html(a["atleta"], foto_h)

    attrs_html = ""
    for attr, lbl in [("attacco","ATT"),("difesa","DIF"),("muro","MUR"),("ricezione","RIC"),("battuta","BAT"),("alzata","ALZ")]:
        val = s.get(attr, 40)
        attrs_html += f'<div style="display:flex;justify-content:space-between;padding:1.5px 8px;font-size:0.7rem;font-weight:800;letter-spacing:0.5px"><span style="opacity:0.75">{lbl}</span><span>{val}</span></div>'

    # ─── TIER DEFINITIONS ───────────────────────────────────────────────────

    if tier == "bronzo_comune":
        card_bg = "linear-gradient(165deg,#2a1500 0%,#5C3317 40%,#8B5E3C 65%,#4a2800 100%)"
        border_col = "#8B5A2B"; glow_col = "rgba(100,60,20,0.5)"
        text_col = "rgba(255,235,190,0.95)"; badge_bg = "rgba(0,0,0,0.4)"; badge_col = "#D4956A"
        label_txt = "BRONZO"; ovr_col = "#D4956A"
        overlay = ""
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "bronzo_raro":
        card_bg = "linear-gradient(165deg,#1a0800 0%,#7a3a10 25%,#CD7F32 50%,#FF8C00 68%,#8B4513 85%,#3d1500 100%)"
        border_col = "#FF8C00"; glow_col = "rgba(255,140,0,0.55)"
        text_col = "rgba(255,240,200,0.95)"; badge_bg = "rgba(255,120,0,0.2)"; badge_col = "#FF9D3A"
        label_txt = "BRONZO RARO"; ovr_col = "#FF9D3A"
        overlay = '<div style="position:absolute;top:0;left:-120%;width:60%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,160,60,0.25),transparent);border-radius:14px;-webkit-animation:shine_swipe 3.5s ease-in-out infinite;animation:shine_swipe 3.5s ease-in-out infinite;pointer-events:none"></div>'
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "argento_comune":
        card_bg = "linear-gradient(165deg,#1a1a1a 0%,#555 35%,#C0C0C0 60%,#888 80%,#2a2a2a 100%)"
        border_col = "#C0C0C0"; glow_col = "rgba(192,192,192,0.4)"
        text_col = "rgba(255,255,255,0.95)"; badge_bg = "rgba(200,200,200,0.15)"; badge_col = "#E8E8E8"
        label_txt = "ARGENTO"; ovr_col = "#E8E8E8"
        overlay = ""
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "argento_raro":
        card_bg = "linear-gradient(165deg,#0a1020 0%,#2a3a6a 30%,#6080D0 55%,#A0B8E8 70%,#3050A0 88%,#0a1020 100%)"
        border_col = "#7090D8"; glow_col = "rgba(100,140,220,0.6)"
        text_col = "rgba(220,235,255,0.97)"; badge_bg = "rgba(80,120,220,0.2)"; badge_col = "#A0C0F0"
        label_txt = "ARGENTO RARO"; ovr_col = "#A0C0F0"
        overlay = '<div style="position:absolute;top:0;left:-120%;width:60%;height:100%;background:linear-gradient(105deg,transparent,rgba(150,200,255,0.3),transparent);border-radius:14px;-webkit-animation:shine_swipe 2.8s ease-in-out infinite;animation:shine_swipe 2.8s ease-in-out infinite;pointer-events:none"></div>'
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "oro_comune":
        card_bg = "linear-gradient(165deg,#2a1a00 0%,#8B6914 28%,#FFD700 52%,#D4AF37 68%,#8B6914 85%,#2a1a00 100%)"
        border_col = "#FFD700"; glow_col = "rgba(255,215,0,0.55)"
        text_col = "rgba(20,10,0,0.95)"; badge_bg = "rgba(255,215,0,0.2)"; badge_col = "#8B6914"
        label_txt = "ORO"; ovr_col = "#8B6914"
        overlay = ""
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "oro_raro":
        card_bg = "linear-gradient(165deg,#1a0d00 0%,#6B4400 22%,#FFD700 44%,#FFA500 60%,#FF8C00 74%,#6B4400 88%,#1a0d00 100%)"
        border_col = "#FFA500"; glow_col = "rgba(255,165,0,0.75)"
        text_col = "rgba(15,8,0,0.95)"; badge_bg = "rgba(255,165,0,0.25)"; badge_col = "#8B5500"
        label_txt = "ORO RARO &#10024;"; ovr_col = "#8B5500"
        overlay = (
            '<div style="position:absolute;top:0;left:-120%;width:55%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,215,0,0.4),rgba(255,180,0,0.2),transparent);border-radius:14px;-webkit-animation:shine_swipe 2.2s ease-in-out infinite;animation:shine_swipe 2.2s ease-in-out infinite;pointer-events:none"></div>'
            '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#FFD700,#FFA500,#FFD700,transparent);border-radius:14px 14px 0 0;pointer-events:none"></div>'
        )
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "eroe":
        card_bg = "linear-gradient(165deg,#0d0018 0%,#3a0060 25%,#7800CC 48%,#AA00EE 65%,#5500AA 82%,#0d0018 100%)"
        border_col = "#CC00FF"; glow_col = "rgba(180,0,255,0.8)"
        text_col = "rgba(240,200,255,0.97)"; badge_bg = "rgba(180,0,255,0.2)"; badge_col = "#DD88FF"
        label_txt = "⚡ EROE"; ovr_col = "#DD88FF"
        overlay = (
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;border-radius:14px;overflow:hidden">'
            '<div style="position:absolute;top:0;left:-120%;width:55%;height:100%;background:linear-gradient(105deg,transparent,rgba(200,0,255,0.35),transparent);-webkit-animation:shine_swipe 2.5s ease-in-out infinite;animation:shine_swipe 2.5s ease-in-out infinite"></div>'
            '<div style="position:absolute;top:8px;left:50%;-webkit-transform:translateX(-50%);transform:translateX(-50%);color:rgba(220,100,255,0.6);font-size:0.5rem;letter-spacing:4px">&#9889; &#9889; &#9889; &#9889; &#9889;</div>'
            '</div>'
            '<div style="position:absolute;top:15%;left:-18px;font-size:2.2rem;color:#CC00FF;opacity:0.7;-webkit-animation:wing_float 3s ease-in-out infinite;animation:wing_float 3s ease-in-out infinite;pointer-events:none;-webkit-filter:drop-shadow(0 0 6px #CC00FF);filter:drop-shadow(0 0 6px #CC00FF)">&#9889;</div>'
            '<div style="position:absolute;top:15%;right:-18px;font-size:2.2rem;color:#CC00FF;opacity:0.7;-webkit-animation:wing_float_r 3s ease-in-out infinite 0.4s;animation:wing_float_r 3s ease-in-out infinite 0.4s;pointer-events:none;-webkit-filter:drop-shadow(0 0 6px #CC00FF);filter:drop-shadow(0 0 6px #CC00FF)">&#9889;</div>'
            '<div style="position:absolute;bottom:6px;left:0;right:0;height:40px;background:repeating-linear-gradient(45deg,transparent,transparent 6px,rgba(200,0,255,0.04) 6px,rgba(200,0,255,0.04) 12px);pointer-events:none;border-radius:0 0 14px 14px"></div>'
            '<div style="position:absolute;top:-6px;left:10%;right:10%;height:5px;overflow:hidden;border-radius:99px;pointer-events:none">'
            '<div style="width:40%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,215,0,0.9),transparent);-webkit-animation:golden_ribbon 2.5s linear infinite;animation:golden_ribbon 2.5s linear infinite"></div>'
            '</div>'
        )
        card_extra_style = ""
        card_shape = "border-radius:14px;"

    elif tier == "if_card":
        card_bg = "linear-gradient(165deg,#050505 0%,#1a1a1a 20%,#2a2a2a 40%,#FFD700 55%,#FFF8DC 68%,#C0C0C0 78%,#1a1a1a 92%,#050505 100%)"
        border_col = "#FFD700"; glow_col = "rgba(255,215,0,0.85)"
        text_col = "rgba(10,8,0,0.97)"; badge_bg = "rgba(255,215,0,0.25)"; badge_col = "#000000"
        label_txt = "⭐ IF"; ovr_col = "#1a0d00"
        overlay = (
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;border-radius:16px;overflow:hidden">'
            '<div style="position:absolute;top:0;left:-120%;width:50%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,255,255,0.45),rgba(255,215,0,0.3),transparent);-webkit-animation:shine_swipe 1.8s ease-in-out infinite;animation:shine_swipe 1.8s ease-in-out infinite"></div>'
            '</div>'
            '<div style="position:absolute;top:-14px;left:50%;-webkit-transform:translateX(-50%);transform:translateX(-50%);font-size:1.8rem;-webkit-filter:drop-shadow(0 0 8px gold);filter:drop-shadow(0 0 8px gold)">&#11088;</div>'
            '<div style="position:absolute;top:-4px;left:0;right:0;height:4px;background:linear-gradient(90deg,#FFD700,#FFF8DC,#FFD700);border-radius:16px 16px 0 0;pointer-events:none"></div>'
            '<div style="position:absolute;bottom:-4px;left:0;right:0;height:4px;background:linear-gradient(90deg,#FFD700,#FFF8DC,#FFD700);border-radius:0 0 16px 16px;pointer-events:none"></div>'
        )
        card_extra_style = f"box-shadow:0 0 0 3px #FFD700, 0 0 0 5px #8B6914, 0 0 40px {glow_col},0 0 80px rgba(255,215,0,0.3);"
        card_shape = "border-radius:16px;clip-path:polygon(0 0,100% 0,100% 88%,88% 100%,0 100%);"

    elif tier == "leggenda":
        card_bg = "linear-gradient(165deg,#f5f0e8 0%,#e8dfc8 20%,#fff8f0 45%,#f0e8d8 60%,#D4AF37 75%,#e8dfc8 90%,#f5f0e8 100%)"
        border_col = "#D4AF37"; glow_col = "rgba(212,175,55,0.8)"
        text_col = "rgba(10,5,0,0.97)"; badge_bg = "rgba(212,175,55,0.2)"; badge_col = "#6B4400"
        label_txt = "👑 LEGGENDA"; ovr_col = "#6B4400"
        overlay = (
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden;border-radius:16px">'
            '<div style="position:absolute;top:0;left:-120%;width:50%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,255,255,0.6),transparent);-webkit-animation:shine_swipe 2s ease-in-out infinite;animation:shine_swipe 2s ease-in-out infinite"></div>'
            '</div>'
            '<div style="position:absolute;top:18%;left:-32px;width:40px;height:80px;pointer-events:none;overflow:visible">'
            '<svg width="40" height="80" viewBox="0 0 40 80" style="-webkit-animation:wing_float 4s ease-in-out infinite;animation:wing_float 4s ease-in-out infinite;-webkit-filter:drop-shadow(0 0 6px rgba(255,255,255,0.8));filter:drop-shadow(0 0 6px rgba(255,255,255,0.8))">'
            '<path d="M40,10 Q0,20 2,40 Q0,60 40,70 Q20,55 22,40 Q20,25 40,10Z" fill="rgba(255,255,255,0.85)" stroke="#D4AF37" stroke-width="0.8"/>'
            '<path d="M40,10 Q15,30 18,40 Q15,52 40,70" fill="rgba(255,230,180,0.5)" stroke="rgba(212,175,55,0.4)" stroke-width="0.5"/>'
            '</svg></div>'
            '<div style="position:absolute;top:18%;right:-32px;width:40px;height:80px;pointer-events:none;overflow:visible">'
            '<svg width="40" height="80" viewBox="0 0 40 80" style="-webkit-animation:wing_float_r 4s ease-in-out infinite 0.3s;animation:wing_float_r 4s ease-in-out infinite 0.3s;-webkit-filter:drop-shadow(0 0 6px rgba(255,255,255,0.8));filter:drop-shadow(0 0 6px rgba(255,255,255,0.8))">'
            '<path d="M0,10 Q40,20 38,40 Q40,60 0,70 Q20,55 18,40 Q20,25 0,10Z" fill="rgba(255,255,255,0.85)" stroke="#D4AF37" stroke-width="0.8"/>'
            '<path d="M0,10 Q25,30 22,40 Q25,52 0,70" fill="rgba(255,230,180,0.5)" stroke="rgba(212,175,55,0.4)" stroke-width="0.5"/>'
            '</svg></div>'
            '<div style="position:absolute;top:30%;left:8px;width:4px;height:30px;background:linear-gradient(180deg,rgba(255,215,0,0.9),transparent);border-radius:2px;-webkit-animation:lightning 4s ease-in-out infinite;animation:lightning 4s ease-in-out infinite;pointer-events:none"></div>'
            '<div style="position:absolute;top:25%;right:8px;width:3px;height:25px;background:linear-gradient(180deg,rgba(255,215,0,0.8),transparent);border-radius:2px;-webkit-animation:lightning2 4s ease-in-out infinite 1.5s;animation:lightning2 4s ease-in-out infinite 1.5s;pointer-events:none"></div>'
            '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#D4AF37,#FFF8DC,#D4AF37,transparent);pointer-events:none"></div>'
        )
        card_extra_style = f"box-shadow:0 0 0 2px #D4AF37, 0 0 0 4px rgba(212,175,55,0.3), 0 0 40px {glow_col};"
        card_shape = "border-radius:16px;clip-path:polygon(4% 0,96% 0,100% 4%,100% 96%,96% 100%,4% 100%,0 96%,0 4%);"

    elif tier == "toty":
        card_bg = "linear-gradient(165deg,#000820 0%,#001055 22%,#002099 42%,#1040CC 56%,#2860FF 68%,#C0A820 80%,#FFD700 90%,#001055 100%)"
        border_col = "#FFD700"; glow_col = "rgba(255,215,0,0.9)"
        text_col = "rgba(220,240,255,0.98)"; badge_bg = "rgba(0,60,200,0.2)"; badge_col = "#FFD700"
        label_txt = "🏆 TOTY"; ovr_col = "#FFD700"
        overlay = (
            '<div style="position:absolute;top:12%;left:-40px;width:48px;height:90px;pointer-events:none">'
            '<svg width="48" height="90" viewBox="0 0 48 90" style="-webkit-animation:wing_float 3.5s ease-in-out infinite;animation:wing_float 3.5s ease-in-out infinite;-webkit-filter:drop-shadow(0 0 10px rgba(200,220,255,0.9));filter:drop-shadow(0 0 10px rgba(200,220,255,0.9))">'
            '<path d="M48,8 Q0,18 2,45 Q0,72 48,82 Q22,62 24,45 Q22,28 48,8Z" fill="rgba(200,220,255,0.8)" stroke="#C0D0FF" stroke-width="1"/>'
            '<path d="M48,8 Q14,30 16,45 Q14,60 48,82" fill="rgba(180,200,255,0.35)" stroke="rgba(180,200,255,0.5)" stroke-width="0.5"/>'
            '<path d="M38,15 Q10,32 12,45 Q10,58 38,75" fill="none" stroke="rgba(200,220,255,0.4)" stroke-width="0.5"/>'
            '</svg></div>'
            '<div style="position:absolute;top:12%;right:-40px;width:48px;height:90px;pointer-events:none">'
            '<svg width="48" height="90" viewBox="0 0 48 90" style="-webkit-animation:wing_float_r 3.5s ease-in-out infinite 0.4s;animation:wing_float_r 3.5s ease-in-out infinite 0.4s;-webkit-filter:drop-shadow(0 0 10px rgba(200,220,255,0.9));filter:drop-shadow(0 0 10px rgba(200,220,255,0.9))">'
            '<path d="M0,8 Q48,18 46,45 Q48,72 0,82 Q26,62 24,45 Q26,28 0,8Z" fill="rgba(200,220,255,0.8)" stroke="#C0D0FF" stroke-width="1"/>'
            '<path d="M0,8 Q34,30 32,45 Q34,60 0,82" fill="rgba(180,200,255,0.35)" stroke="rgba(180,200,255,0.5)" stroke-width="0.5"/>'
            '</svg></div>'
            '<div style="position:absolute;top:4px;left:5px;font-size:1rem;opacity:0.5;-webkit-animation:cloud_drift 4s ease-in-out infinite;animation:cloud_drift 4s ease-in-out infinite;pointer-events:none">&#x2601;&#xFE0F;</div>'
            '<div style="position:absolute;top:4px;right:5px;font-size:0.85rem;opacity:0.4;-webkit-animation:cloud_drift 4s ease-in-out infinite 1.5s;animation:cloud_drift 4s ease-in-out infinite 1.5s;pointer-events:none">&#x2601;&#xFE0F;</div>'
            '<div style="position:absolute;top:20%;left:5px;font-size:0.8rem;-webkit-animation:lightning 3.5s infinite;animation:lightning 3.5s infinite;pointer-events:none;color:#FFD700">&#9889;</div>'
            '<div style="position:absolute;top:35%;right:5px;font-size:0.7rem;-webkit-animation:lightning2 3.5s infinite 1.2s;animation:lightning2 3.5s infinite 1.2s;pointer-events:none;color:#A0C0FF">&#9889;</div>'
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden;border-radius:18px">'
            '<div style="position:absolute;top:0;left:-120%;width:50%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,215,0,0.2),rgba(200,220,255,0.15),transparent);-webkit-animation:shine_swipe 2s ease-in-out infinite;animation:shine_swipe 2s ease-in-out infinite"></div>'
            '</div>'
            '<div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,transparent,#FFD700,#A0C8FF,#FFD700,transparent);pointer-events:none"></div>'
            '<div style="position:absolute;bottom:0;left:0;right:0;height:4px;background:linear-gradient(90deg,transparent,#FFD700,#A0C8FF,#FFD700,transparent);pointer-events:none"></div>'
        )
        card_extra_style = f"box-shadow:0 0 0 2px #FFD700, 0 0 0 5px rgba(30,60,200,0.4), 0 0 50px {glow_col},0 0 100px rgba(0,80,255,0.25);"
        card_shape = "border-radius:18px;clip-path:polygon(6% 0,94% 0,100% 6%,100% 94%,94% 100%,6% 100%,0 94%,0 6%);"

    elif tier == "toty_evoluto":
        card_bg = "linear-gradient(165deg,#050010 0%,#180040 18%,#000080 35%,#1020A0 50%,#2040CC 62%,#A000CC 74%,#FFD700 85%,#180040 100%)"
        border_col = "#CC00FF"; glow_col = "rgba(200,0,255,0.9)"
        text_col = "rgba(240,220,255,0.98)"; badge_bg = "rgba(160,0,200,0.2)"; badge_col = "#FFD700"
        label_txt = "👑 TOTY+"; ovr_col = "#FFD700"
        overlay = (
            '<div style="position:absolute;top:10%;left:-44px;width:52px;height:95px;pointer-events:none">'
            '<svg width="52" height="95" viewBox="0 0 52 95" style="-webkit-animation:wing_float 3s ease-in-out infinite;animation:wing_float 3s ease-in-out infinite;-webkit-filter:drop-shadow(0 0 12px rgba(255,215,0,0.9)) sepia(0.4) hue-rotate(10deg);filter:drop-shadow(0 0 12px rgba(255,215,0,0.9)) sepia(0.4) hue-rotate(10deg)">'
            '<path d="M52,8 Q0,20 2,47 Q0,74 52,86 Q24,66 26,47 Q24,28 52,8Z" fill="rgba(255,215,0,0.75)" stroke="#FFD700" stroke-width="1.2"/>'
            '<path d="M52,8 Q14,32 16,47 Q14,62 52,86" fill="rgba(255,180,0,0.3)" stroke="rgba(255,215,0,0.6)" stroke-width="0.6"/>'
            '</svg></div>'
            '<div style="position:absolute;top:10%;right:-44px;width:52px;height:95px;pointer-events:none">'
            '<svg width="52" height="95" viewBox="0 0 52 95" style="-webkit-animation:wing_float_r 3s ease-in-out infinite 0.5s;animation:wing_float_r 3s ease-in-out infinite 0.5s;-webkit-filter:drop-shadow(0 0 12px rgba(255,215,0,0.9)) sepia(0.4) hue-rotate(10deg);filter:drop-shadow(0 0 12px rgba(255,215,0,0.9)) sepia(0.4) hue-rotate(10deg)">'
            '<path d="M0,8 Q52,20 50,47 Q52,74 0,86 Q28,66 26,47 Q28,28 0,8Z" fill="rgba(255,215,0,0.75)" stroke="#FFD700" stroke-width="1.2"/>'
            '</svg></div>'
            '<div style="position:absolute;bottom:-5px;left:-8px;font-size:1.8rem;opacity:0.4;pointer-events:none;-webkit-filter:sepia(1) hue-rotate(-10deg);filter:sepia(1) hue-rotate(-10deg)">&#127963;</div>'
            '<div style="position:absolute;bottom:-5px;right:-8px;font-size:1.8rem;opacity:0.4;pointer-events:none;-webkit-transform:scaleX(-1);transform:scaleX(-1);-webkit-filter:sepia(1) hue-rotate(-10deg);filter:sepia(1) hue-rotate(-10deg)">&#127963;</div>'
            '<div style="position:absolute;top:5px;left:8px;font-size:0.9rem;opacity:0.45;-webkit-animation:cloud_drift 5s ease-in-out infinite;animation:cloud_drift 5s ease-in-out infinite;pointer-events:none">&#x26C8;&#xFE0F;</div>'
            '<div style="position:absolute;top:5px;right:8px;font-size:0.85rem;opacity:0.35;-webkit-animation:cloud_drift 5s ease-in-out infinite 2s;animation:cloud_drift 5s ease-in-out infinite 2s;pointer-events:none">&#x26C8;&#xFE0F;</div>'
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden">'
            '<div style="position:absolute;top:0;left:-120%;width:50%;height:100%;background:linear-gradient(105deg,transparent,rgba(200,0,255,0.2),rgba(255,215,0,0.15),transparent);-webkit-animation:shine_swipe 1.8s ease-in-out infinite;animation:shine_swipe 1.8s ease-in-out infinite"></div>'
            '</div>'
            '<div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,transparent,#CC00FF,#FFD700,#CC00FF,transparent);pointer-events:none"></div>'
        )
        card_extra_style = f"box-shadow:0 0 0 2px #CC00FF,0 0 0 4px #FFD700,0 0 60px {glow_col},0 0 100px rgba(255,215,0,0.3);"
        card_shape = "border-radius:18px;clip-path:polygon(6% 0,94% 0,100% 6%,100% 94%,94% 100%,6% 100%,0 94%,0 6%);"

    else:  # goat — sfondo infernale, ali nere infuocate, forma rocciosa/grotta lava
        card_bg = "linear-gradient(165deg,#000000 0%,#1a0000 15%,#3d0000 30%,#7a0000 45%,#CC2200 58%,#FF4400 68%,#7a0000 78%,#1a0000 90%,#000000 100%)"
        border_col = "#FF2200"; glow_col = "rgba(255,40,0,0.9)"
        text_col = "rgba(255,220,200,0.98)"; badge_bg = "rgba(255,40,0,0.2)"; badge_col = "#FF6644"
        label_txt = "🔥 GOAT"; ovr_col = "#FF6644"
        overlay = (
            '<div style="position:absolute;top:4px;left:5px;font-size:0.9rem;opacity:0.6;-webkit-animation:cloud_drift 3s ease-in-out infinite;animation:cloud_drift 3s ease-in-out infinite;pointer-events:none;-webkit-filter:brightness(0.4) contrast(2);filter:brightness(0.4) contrast(2)">&#x26C8;&#xFE0F;</div>'
            '<div style="position:absolute;top:3px;right:5px;font-size:0.8rem;opacity:0.5;-webkit-animation:cloud_drift 3.5s ease-in-out infinite 1s;animation:cloud_drift 3.5s ease-in-out infinite 1s;pointer-events:none;-webkit-filter:brightness(0.3) contrast(2);filter:brightness(0.3) contrast(2)">&#x26C8;&#xFE0F;</div>'
            '<div style="position:absolute;top:22%;left:4px;font-size:0.8rem;-webkit-animation:lightning 2.5s infinite;animation:lightning 2.5s infinite;pointer-events:none;color:#FF4400;-webkit-filter:drop-shadow(0 0 4px #FF4400);filter:drop-shadow(0 0 4px #FF4400)">&#9889;</div>'
            '<div style="position:absolute;top:38%;right:4px;font-size:0.7rem;-webkit-animation:lightning2 2.5s infinite 0.8s;animation:lightning2 2.5s infinite 0.8s;pointer-events:none;color:#FF2200;-webkit-filter:drop-shadow(0 0 4px #FF2200);filter:drop-shadow(0 0 4px #FF2200)">&#9889;</div>'
            '<div style="position:absolute;top:16%;left:-36px;width:44px;height:85px;pointer-events:none">'
            '<svg width="44" height="85" viewBox="0 0 44 85" style="-webkit-animation:wing_float 2.8s ease-in-out infinite;animation:wing_float 2.8s ease-in-out infinite;-webkit-filter:drop-shadow(0 0 10px rgba(255,50,0,0.9));filter:drop-shadow(0 0 10px rgba(255,50,0,0.9))">'
            '<path d="M44,6 Q0,16 2,42 Q0,68 44,78 Q20,58 22,42 Q20,26 44,6Z" fill="rgba(30,0,0,0.95)" stroke="#FF2200" stroke-width="1.2"/>'
            '<path d="M44,6 Q12,28 14,42 Q12,56 44,78" fill="rgba(255,60,0,0.15)" stroke="rgba(255,80,0,0.5)" stroke-width="0.6"/>'
            '</svg></div>'
            '<div style="position:absolute;top:16%;right:-36px;width:44px;height:85px;pointer-events:none">'
            '<svg width="44" height="85" viewBox="0 0 44 85" style="-webkit-animation:wing_float_r 2.8s ease-in-out infinite 0.3s;animation:wing_float_r 2.8s ease-in-out infinite 0.3s;-webkit-filter:drop-shadow(0 0 10px rgba(255,50,0,0.9));filter:drop-shadow(0 0 10px rgba(255,50,0,0.9))">'
            '<path d="M0,6 Q44,16 42,42 Q44,68 0,78 Q24,58 22,42 Q24,26 0,6Z" fill="rgba(30,0,0,0.95)" stroke="#FF2200" stroke-width="1.2"/>'
            '</svg></div>'
            '<div style="position:absolute;top:-2px;right:-2px;width:45px;height:45px;pointer-events:none;overflow:visible">'
            '<svg width="45" height="45" viewBox="0 0 45 45">'
            '<path d="M45,0 L45,45 L20,40 L15,30 L22,20 L12,15 L18,5 L30,8 L35,0 Z" fill="#000000" opacity="0.92"/>'
            '<path d="M45,0 L35,0 L30,8 L18,5 L12,15 L22,20 L15,30 L20,40 L45,45" fill="none" stroke="#FF2200" stroke-width="0.8" opacity="0.6"/>'
            '</svg></div>'
            '<div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden;border-radius:14px">'
            '<div style="position:absolute;top:0;left:-120%;width:50%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,60,0,0.2),transparent);-webkit-animation:shine_swipe 2.2s ease-in-out infinite;animation:shine_swipe 2.2s ease-in-out infinite"></div>'
            '</div>'
        )
        card_extra_style = f"animation:lava_glow 2s ease-in-out infinite;border-radius:14px;"
        # Forma rocciosa grotta lava
        card_shape = "border-radius:14px 4px 14px 14px;clip-path:polygon(0 0,78% 0,82% 2%,86% 0,100% 0,100% 100%,0 100%);"

    # ─── ASSEMBLE CARD ───────────────────────────────────────────────────────

    hover_glow = glow_col.replace("rgba(", "").replace(")", "").split(",")
    hover_shadow = f"0 16px 50px {glow_col}, 0 6px 20px rgba(0,0,0,0.9)"

    return f"""
<div id="{cid}" class="fc26-card" style="position:relative;background:{card_bg};border:2px solid {border_col};
    {card_shape}
    width:{card_w};padding:0 0 12px 0;text-align:center;color:{text_col};
    box-shadow:0 6px 30px {glow_col},0 2px 8px rgba(0,0,0,0.7);{card_extra_style}
    -webkit-transition:transform 0.25s ease,box-shadow 0.25s ease;transition:transform 0.25s ease,box-shadow 0.25s ease;{cursor}overflow:visible;
    font-family:'Barlow Condensed',sans-serif"
    onmouseover="this.style.transform='scale(1.05) translateY(-6px)';this.style.boxShadow='{hover_shadow}'"
    onmouseout="this.style.transform='scale(1) translateY(0)';this.style.boxShadow='0 6px 30px {glow_col},0 2px 8px rgba(0,0,0,0.7)'">
  {overlay}
  <div style="position:relative;overflow:hidden;border-radius:12px 12px 0 0">
    {foto_html}
    <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(180deg,transparent 50%,rgba(0,0,0,0.55));pointer-events:none"></div>
    <div style="position:absolute;top:6px;left:7px;text-align:center;line-height:1">
      <div style="font-size:{ovr_size};font-weight:900;color:{ovr_col};
          font-family:'Barlow Condensed',sans-serif;
          text-shadow:0 0 10px {ovr_col},0 2px 8px rgba(0,0,0,0.9);
          -webkit-animation:ovr_pulse 2s ease-in-out infinite;animation:ovr_pulse 2s ease-in-out infinite;line-height:1">{overall}</div>
      <div style="font-size:0.45rem;letter-spacing:2.5px;font-weight:800;opacity:0.85;text-shadow:none">OVR</div>
    </div>
    <div style="position:absolute;top:6px;right:6px;background:{badge_bg};
        -webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);border-radius:5px;padding:3px 6px">
      <div style="font-size:0.38rem;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;opacity:0.95">{label_txt}</div>
    </div>
  </div>
  <div style="font-size:{name_size};font-weight:900;text-transform:uppercase;letter-spacing:1.8px;
      padding:7px 6px 5px;border-bottom:1px solid rgba(255,255,255,0.12);
      text-shadow:0 1px 4px rgba(0,0,0,0.6)">{a['nome']}</div>
  <div style="background:rgba(0,0,0,0.22);padding:5px 0;margin-top:2px;-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)">{attrs_html}</div>
  <div style="font-size:0.52rem;opacity:0.8;padding:5px 6px 0;display:-webkit-flex;display:flex;-webkit-justify-content:space-around;justify-content:space-around;letter-spacing:0.5px">
    <span title="Ori">&#127945;{a['oro']}</span>
    <span title="Tornei">&#127918;{a['tornei']}</span>
    <span title="Win Rate">{a['win_rate']}%WR</span>
  </div>
</div>
"""


# ─── RENDER FUNZIONI ─────────────────────────────────────────────────────────

def _render_carte_fifa(state, ranking):
    st.markdown("### 🃏 Card Giocatori FC26")
    st.markdown(CARD_ANIMATIONS, unsafe_allow_html=True)

    # Leggenda tier
    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;padding:10px;
        background:var(--bg-card2);border-radius:8px;border:1px solid var(--border)">
      <span style="font-size:0.6rem;color:var(--text-secondary);letter-spacing:2px;text-transform:uppercase;align-self:center">TIER:</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#3d1500;border-radius:4px;color:#D4956A">Bronzo 40-54</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#2a2a2a;border-radius:4px;color:#E8E8E8">Argento 55-64</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#3d2e00;border-radius:4px;color:#FFD700">Oro 65-74</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#2a0050;border-radius:4px;color:#DD88FF">Eroe 70-74</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#050505;border-radius:4px;color:#FFD700">IF 75-79</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#f5f0e8;border-radius:4px;color:#6B4400">Leggenda 80-84</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#000820;border-radius:4px;color:#FFD700">TOTY 85-89</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#050010;border-radius:4px;color:#CC00FF">TOTY+ 90-94</span>
      <span style="font-size:0.62rem;padding:2px 7px;background:#1a0000;border-radius:4px;color:#FF6644">🔥 GOAT 95+</span>
    </div>
    """, unsafe_allow_html=True)

    # Griglia carte — 4 per riga con wrapper HTML
    cards_per_row = 4
    for i in range(0, len(ranking), cards_per_row):
        chunk = ranking[i:i+cards_per_row]
        cols = st.columns(len(chunk))
        for col, a_data in zip(cols, chunk):
            with col:
                card_html = render_card_html(a_data, size="normal", clickable=True)
                st.markdown(card_html, unsafe_allow_html=True)
                # Bottone sotto la carta
                if st.button(f"👤 {a_data['nome'].split()[0]}", key=f"card_btn_{a_data['id']}", use_container_width=True):
                    st.session_state.profilo_atleta_id = a_data["id"]
                    st.session_state.current_page = "profili"
                    st.rerun()


def _render_classifica_completa(state, ranking):
    n_sq = len(state["squadre"])
    st.markdown(f"""
    <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:var(--radius,12px);
        padding:12px 20px;margin-bottom:20px;font-size:0.8rem;color:var(--text-secondary)">
        💡 <strong>Formula punti:</strong> {n_sq} squadre × 10 =
        <strong style="color:var(--accent-gold)">{n_sq*10} pt per il 1°</strong>
        · Ogni posizione successiva: -10 pt
    </div>
    """, unsafe_allow_html=True)

    if len(ranking) >= 3:
        st.markdown(CARD_ANIMATIONS, unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        podio_cols = [(col2, ranking[0], "🥇", "#ffd700", "1°"),
                      (col1, ranking[1], "🥈", "#c0c0c0", "2°"),
                      (col3, ranking[2], "🥉", "#cd7f32", "3°")]
        for col, atleta, medal, color, pos in podio_cols:
            with col:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:2px solid {color};
                    border-radius:var(--radius,12px);padding:20px;text-align:center;
                    margin-top:{'0' if pos=='1°' else '20px'}">
                    <div style="font-size:2.5rem">{medal}</div>
                    <div style="font-family:var(--font-display,'Barlow Condensed'),sans-serif;font-size:1.3rem;font-weight:800;color:{color}">{atleta['nome']}</div>
                    <div style="color:var(--text-secondary);font-size:0.85rem;margin:4px 0">{atleta['rank_pts']} pt</div>
                    <div style="font-size:0.75rem;color:{color}">🥇{atleta['oro']} 🥈{atleta['argento']} 🥉{atleta['bronzo']}</div>
                    <div style="background:rgba(255,215,0,0.15);border-radius:8px;padding:4px 10px;margin-top:8px;display:inline-block">
                        <span style="font-weight:800;color:var(--accent-gold,#ffd700);font-size:0.9rem">OVR {atleta['overall']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    html = """
    <table class="rank-table">
    <tr>
        <th>#</th><th style="text-align:left">ATLETA</th>
        <th>OVR</th><th>PTS RANK</th><th>T</th><th>V</th><th>P</th>
        <th>SV</th><th>SP</th><th>WIN%</th>
    </tr>"""
    pos_cls = {1: "gold", 2: "silver", 3: "bronze"}
    for i, a in enumerate(ranking):
        pos = i + 1
        cls = pos_cls.get(pos, "")
        ct_label = a["card_type"].replace("_", " ").upper()
        html += f"""
        <tr>
            <td><span class="rank-pos {cls}">{pos}</span></td>
            <td style="text-align:left">
                <span style="font-weight:700">{a['nome']}</span>
                <span style="font-size:0.65rem;color:var(--text-secondary);margin-left:6px">{ct_label}</span>
            </td>
            <td style="font-weight:800;color:var(--accent-gold)">{a['overall']}</td>
            <td style="font-weight:700;color:var(--accent-gold)">{a['rank_pts']}</td>
            <td>{a['tornei']}</td>
            <td style="color:var(--green)">{a['vittorie']}</td>
            <td style="color:var(--accent-red)">{a['sconfitte']}</td>
            <td>{a['set_vinti']}</td><td>{a['set_persi']}</td>
            <td>{a['win_rate']}%</td>
        </tr>"""
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


def _render_trofei_page(state, ranking):
    st.markdown("### 🏅 Trofei Giocatori")
    if not ranking:
        st.info("Aggiungi atleti per visualizzare i trofei.")
        return
    tutti_atleti = {a["nome"]: a["atleta"] for a in ranking}
    sel = st.selectbox("Seleziona giocatore", list(tutti_atleti.keys()), key="trofei_sel")
    atleta = tutti_atleti[sel]
    trofei = get_trofei_atleta(atleta)
    sbloccati = sum(1 for _, unlocked in trofei if unlocked)
    st.markdown(f"""
    <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:var(--radius,12px);
        padding:14px 20px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center">
        <div>
            <div style="font-family:var(--font-display,'Barlow Condensed'),sans-serif;font-size:1.5rem;font-weight:800">{atleta['nome']}</div>
            <div style="color:var(--text-secondary);font-size:0.8rem">{sbloccati}/{len(trofei)} trofei sbloccati</div>
        </div>
        <div style="text-align:center">
            <div style="font-size:2rem;font-weight:900;color:var(--accent-gold)">{sbloccati}</div>
            <div style="font-size:0.7rem;color:var(--text-secondary);letter-spacing:2px">TROFEI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    perc = int(sbloccati / len(trofei) * 100)
    st.markdown(f"""
    <div style="background:var(--border,#2a2a3a);border-radius:10px;height:8px;margin-bottom:20px;overflow:hidden">
        <div style="background:linear-gradient(90deg,var(--accent1,#e8002d),var(--accent-gold,#ffd700));height:100%;width:{perc}%;border-radius:10px;transition:width 0.5s"></div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (trofeo, sbloccato) in enumerate(trofei):
        with cols[i % 4]:
            tc = {"comune":"#cd7f32","non comune":"#c0c0c0","raro":"#ffd700","epico":"#e040fb","leggendario":"#00f5ff"}.get(trofeo["rarità"],"#888")
            locked_filter = "" if sbloccato else "filter:grayscale(100%) opacity(0.4);"
            st.markdown(f"""
            <div title="{trofeo['descrizione']}" style="background:{trofeo['sfondo'] if sbloccato else 'var(--bg-card2)'};
                border:2px solid {tc if sbloccato else 'var(--border)'};
                border-radius:12px;padding:16px;text-align:center;margin-bottom:8px;
                {locked_filter}{'box-shadow:0 0 20px ' + tc + '40;' if sbloccato else ''}
                transition:all 0.3s;cursor:help">
                <div style="font-size:2.5rem;margin-bottom:6px">{trofeo['icona']}</div>
                <div style="font-weight:800;font-size:0.85rem;color:{'rgba(0,0,0,0.9)' if sbloccato else 'var(--text-primary)'};
                    text-transform:uppercase;letter-spacing:1px">{trofeo['nome']}</div>
                <div style="font-size:0.65rem;margin-top:4px;color:{'rgba(0,0,0,0.7)' if sbloccato else 'var(--text-secondary)'}">
                    {trofeo['descrizione']}</div>
                <div style="margin-top:8px;font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                    color:{'rgba(0,0,0,0.6)' if sbloccato else tc}">{trofeo['rarità'].upper()}</div>
                {'<div style="margin-top:6px;font-size:0.8rem;font-weight:700;color:rgba(0,0,0,0.8)">✓ SBLOCCATO</div>' if sbloccato else '<div style="margin-top:6px;font-size:0.7rem;color:var(--text-secondary)">🔒 Bloccato</div>'}
            </div>
            """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🏆 Bacheca Globale Trofei")
    _render_global_trophy_board(state, ranking)


def _render_global_trophy_board(state, ranking):
    if not ranking: return
    html = '<table class="rank-table"><tr><th style="text-align:left">GIOCATORE</th>'
    for t in TROFEI_DEFINIZIONE:
        html += f'<th title="{t["descrizione"]}">{t["icona"]}</th>'
    html += '</tr>'
    for a_data in ranking:
        atleta = a_data["atleta"]
        trofei = get_trofei_atleta(atleta)
        html += f'<tr><td style="text-align:left;font-weight:700">{atleta["nome"]}</td>'
        for trofeo, sbloccato in trofei:
            if sbloccato:
                html += f'<td title="{trofeo["nome"]}">✅</td>'
            else:
                html += '<td style="opacity:0.2">🔒</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)


def _render_schede_atleti(state, ranking, atleta_id_preselect=None):
    if not ranking: return
    nomi = [a["nome"] for a in ranking]
    default_idx = 0
    if atleta_id_preselect:
        for i, a in enumerate(ranking):
            if a["id"] == atleta_id_preselect:
                default_idx = i; break
    elif st.session_state.get("profilo_atleta_id"):
        for i, a in enumerate(ranking):
            if a["id"] == st.session_state.profilo_atleta_id:
                default_idx = i; break

    sel = st.selectbox("🔍 Seleziona Atleta", nomi, index=default_idx, key="rank_career_sel")
    a = next((x for x in ranking if x["nome"] == sel), None)
    if not a: return

    with st.expander("✏️ Modifica Profilo Atleta", expanded=False):
        _render_modifica_profilo(state, a["atleta"])

    col_card, col_stats = st.columns([1, 2])
    with col_card:
        st.markdown(CARD_ANIMATIONS, unsafe_allow_html=True)
        st.markdown(render_card_html(a, size="normal", clickable=False), unsafe_allow_html=True)
    with col_stats:
        s = a["atleta"]["stats"]
        st.markdown(f"""
        <div class="career-card">
            <div class="career-name">👤 {a['nome']}</div>
            <div style="color:var(--accent-gold,#ffd700);font-size:0.85rem;margin-top:4px">
                🏅 {a['rank_pts']} punti ranking · OVR {a['overall']} · {a['card_type'].replace('_',' ').upper()}
            </div>
            <div class="stat-grid">
                <div class="stat-box"><div class="stat-value" style="color:var(--accent-gold)">{a['rank_pts']}</div><div class="stat-label">Rank Pts</div></div>
                <div class="stat-box"><div class="stat-value">{a['tornei']}</div><div class="stat-label">Tornei</div></div>
                <div class="stat-box"><div class="stat-value" style="color:var(--green)">{a['vittorie']}</div><div class="stat-label">Vittorie</div></div>
                <div class="stat-box"><div class="stat-value">{a['win_rate']}%</div><div class="stat-label">Win Rate</div></div>
                <div class="stat-box"><div class="stat-value">{a['set_vinti']}</div><div class="stat-label">Set Vinti</div></div>
                <div class="stat-box"><div class="stat-value">{a['set_persi']}</div><div class="stat-label">Set Persi</div></div>
                <div class="stat-box"><div class="stat-value">{a['quoziente_set']}</div><div class="stat-label">Q.Set</div></div>
                <div class="stat-box"><div class="stat-value">{a['quoziente_punti']}</div><div class="stat-label">Q.Punti</div></div>
                <div class="stat-box"><div class="stat-value">{a['punti_fatti']}</div><div class="stat-label">Pt Fatti</div></div>
                <div class="stat-box"><div class="stat-value">{a['oro']}</div><div class="stat-label">🥇 Ori</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 🎮 Attributi")
    col_attrs = st.columns(6)
    attrs = ["attacco","difesa","muro","ricezione","battuta","alzata"]
    icons = ["⚡","🛡️","🧱","🤲","🏐","🎯"]
    for col, attr, icon in zip(col_attrs, attrs, icons):
        with col:
            val = s.get(attr, 40)
            color = "#00c851" if val >= 75 else "#ffd700" if val >= 60 else "#a0a0b0"
            st.markdown(f"""
            <div style="background:var(--bg-card2);border-radius:8px;padding:10px;text-align:center">
                <div style="font-size:1.1rem">{icon}</div>
                <div style="font-size:1.6rem;font-weight:900;color:{color}">{val}</div>
                <div style="font-size:0.6rem;color:var(--text-secondary);letter-spacing:1px;text-transform:uppercase">{attr}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 🏆 Trofei")
    trofei = get_trofei_atleta(a["atleta"])
    sbloccati_count = sum(1 for _, u in trofei if u)
    st.caption(f"{sbloccati_count}/{len(trofei)} sbloccati")
    tcols = st.columns(6)
    for i, (trofeo, sbloccato) in enumerate(trofei):
        with tcols[i % 6]:
            tc = {"comune":"#cd7f32","non comune":"#c0c0c0","raro":"#ffd700","epico":"#e040fb","leggendario":"#00f5ff"}.get(trofeo["rarità"],"#888")
            locked_filter = "" if sbloccato else "filter:grayscale(100%) opacity(0.35);"
            st.markdown(f"""
            <div title="{trofeo['descrizione']} ({'SBLOCCATO' if sbloccato else 'Bloccato'})"
                style="background:{trofeo['sfondo'] if sbloccato else 'var(--bg-card2)'};
                border:1px solid {tc if sbloccato else 'var(--border)'};
                border-radius:8px;padding:8px;text-align:center;margin-bottom:6px;
                {locked_filter}cursor:help">
                <div style="font-size:1.5rem">{trofeo['icona']}</div>
                <div style="font-size:0.55rem;font-weight:700;margin-top:2px;color:{'rgba(0,0,0,0.85)' if sbloccato else 'var(--text-primary)'}">{trofeo['nome']}</div>
                <div style="font-size:0.45rem;margin-top:1px;color:{'rgba(0,0,0,0.6)' if sbloccato else tc};letter-spacing:1px">{trofeo['rarità'].upper()}</div>
            </div>
            """, unsafe_allow_html=True)

    if a["storico"]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📈 Andamento Posizioni")
            df_pos = pd.DataFrame({
                "Torneo": [e[0] for e in a["storico"]],
                "Posizione": [e[1] for e in a["storico"]]
            }).set_index("Torneo")
            max_pos = df_pos["Posizione"].max()
            df_pos["Inv"] = max_pos + 1 - df_pos["Posizione"]
            st.line_chart(df_pos["Inv"], height=200, color="#e8002d")
            st.caption("↑ = Migliore posizione")
        with col2:
            st.markdown("#### 📊 Punti per Torneo")
            storico_pts = []
            for entry in a["storico"]:
                t_nome, pos = entry[0], entry[1]
                n_sq_e = entry[2] if len(entry) == 3 else (len(state["squadre"]) or 8)
                storico_pts.append({"Torneo": t_nome, "Punti": calcola_punti_ranking(pos, n_sq_e)})
            df_pts = pd.DataFrame(storico_pts).set_index("Torneo")
            st.bar_chart(df_pts, height=200, color="#ffd700")
        st.markdown("#### 📋 Storico Tornei")
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for entry in a["storico"]:
            t_nome, pos = entry[0], entry[1]
            n_sq_entry = entry[2] if len(entry) == 3 else (len(state["squadre"]) or 8)
            icon = medals.get(pos, f"#{pos}")
            pts = calcola_punti_ranking(pos, n_sq_entry)
            st.markdown(f"• {icon} **{t_nome}** — {pos}° posto → +{pts} pt ranking")


def _render_modifica_profilo(state, atleta):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        nuovo_nome = st.text_input("Nome", value=atleta.get("nome_proprio", atleta["nome"].split()[0] if atleta["nome"] else ""), key=f"edit_nome_{atleta['id']}")
    with col2:
        nuovo_cognome = st.text_input("Cognome", value=atleta.get("cognome", atleta["nome"].split()[-1] if len(atleta["nome"].split()) > 1 else ""), key=f"edit_cognome_{atleta['id']}")
    with col3:
        foto_up = st.file_uploader("📷 Foto", type=["png","jpg","jpeg"], key=f"edit_foto_{atleta['id']}")
    if st.button("💾 Salva Modifiche Profilo", key=f"save_profile_{atleta['id']}"):
        full_name = f"{nuovo_nome} {nuovo_cognome}".strip()
        if full_name:
            atleta["nome"] = full_name
            atleta["nome_proprio"] = nuovo_nome
            atleta["cognome"] = nuovo_cognome
        if foto_up:
            import base64
            atleta["foto_b64"] = base64.b64encode(foto_up.read()).decode()
        save_state(state)
        st.success("✅ Profilo aggiornato!")
        st.rerun()


def _render_export_ranking_pdf(state, ranking):
    st.markdown("### 📄 Esporta Ranking in PDF")
    if st.button("🖨️ GENERA PDF RANKING", use_container_width=True):
        try:
            pdf_path = _genera_pdf_ranking(state, ranking)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ SCARICA PDF RANKING", f, file_name="ranking_beach_volley.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Errore: {e}")
            import traceback; st.code(traceback.format_exc())


def _genera_pdf_ranking(state, ranking):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    pdf_path = "/tmp/ranking_beach_volley.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=20*mm, bottomMargin=20*mm)
    DARK=colors.HexColor("#0a0a0f"); RED=colors.HexColor("#e8002d"); GOLD=colors.HexColor("#ffd700")
    LIGHT=colors.HexColor("#f0f0f0"); WHITE=colors.white
    styles=getSampleStyleSheet()
    title_s=ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=24,textColor=RED,spaceAfter=4,alignment=1)
    sub_s=ParagraphStyle("sub",fontName="Helvetica",fontSize=11,textColor=colors.grey,spaceAfter=12,alignment=1)
    h2_s=ParagraphStyle("h2",fontName="Helvetica-Bold",fontSize=14,textColor=DARK,spaceBefore=14,spaceAfter=8)
    story=[]
    story.append(Paragraph("BEACH VOLLEY RANKING GLOBALE", title_s))
    story.append(Paragraph(f"{state['torneo']['nome'] or 'Stagione'} · {len(ranking)} atleti classificati", sub_s))
    story.append(HRFlowable(width="100%",thickness=3,color=RED))
    story.append(Spacer(1,10))
    full_data=[["#","ATLETA","OVR","TIER","PTS","T","V","P","SV","SP","WIN%"]]
    for i,a in enumerate(ranking):
        full_data.append([str(i+1),a["nome"],str(a["overall"]),a["card_type"].replace("_"," ").upper(),
                          str(a["rank_pts"]),str(a["tornei"]),str(a["vittorie"]),str(a["sconfitte"]),
                          str(a["set_vinti"]),str(a["set_persi"]),f"{a['win_rate']}%"])
    ft=Table(full_data,colWidths=[8*mm,42*mm,12*mm,24*mm,14*mm,8*mm,8*mm,8*mm,10*mm,10*mm,14*mm])
    ft.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT,WHITE]),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(1,0),(1,-1),"LEFT"),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#dddddd")),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#fff8dc")),
        ("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),
    ]))
    story.append(ft)
    story.append(Spacer(1,10))
    story.append(Paragraph("Documento generato da Beach Volley Tournament Manager Pro",
                            ParagraphStyle("footer",fontName="Helvetica",fontSize=7,textColor=colors.grey,alignment=1)))
    doc.build(story)
    return pdf_path
