"""
mbt_rivals.py — MBT RIVALS v4.0
OTTIMIZZAZIONI v4.0:
- Lazy loading carte: paginazione per evitare render di 700+ carte in una volta
- Cache immagini base64 con @st.cache_data per non rileggere foto ad ogni rerun
- Animazioni card semplificate in CSS (niente random Python su ogni render)
- Tutte e 6 le statistiche visibili su due righe da 3 in fondo alla carta
- Campo da gioco beach volley nella schermata battaglia
- Slot carta Trainer fuori dal campo, schieramento da Collezione
- Carte TRAINER con grafica dedicata (verde/rosso/viola) e effetto polvere luccicante
- Animazioni arena preview e pulsanti battaglia
- Sezione Admin: pulsante "Aggiungi Carta" diretto senza compilare tutto
- Edit inline statistiche nel Card Manager
"""
import streamlit as st
import json
import random
import time
import base64
import os
import hashlib
from pathlib import Path
from datetime import datetime
from functools import lru_cache

# ─── FILE PERSISTENZA ────────────────────────────────────────────────────────
RIVALS_FILE       = "mbt_rivals_data.json"
CARDS_DB_FILE     = "mbt_cards_db.json"
ASSETS_ICONS_DIR  = "assets/icons"
ASSETS_CARDS_DIR  = "assets/card_templates"

# ─── OVR CALC ────────────────────────────────────────────────────────────────

def calcola_ovr_da_stats(atk=40, dif=40, ric=40, bat=40, mur=40, alz=40):
    pesi = {"atk":1.4,"dif":1.2,"bat":1.1,"ric":1.0,"mur":0.9,"alz":0.8}
    tot  = sum(pesi.values())
    raw  = (atk*pesi["atk"]+dif*pesi["dif"]+bat*pesi["bat"]+
            ric*pesi["ric"]+mur*pesi["mur"]+alz*pesi["alz"])/tot
    return int(max(40,min(125,raw)))

# ─── CSS ─────────────────────────────────────────────────────────────────────

RIVALS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Orbitron:wght@400;700;900&family=Exo+2:ital,wght@0,300;0,700;0,900;1,700&display=swap');
:root{
  --rivals-bg:#080810;--rivals-card:#10101e;--rivals-border:#1e1e3a;
  --rivals-gold:#ffd700;--rivals-purple:#9b59b6;--rivals-blue:#1e3a8a;
  --rivals-red:#dc2626;--rivals-green:#16a34a;--rivals-cyan:#00f5ff;
  --font-rivals:'Orbitron','Rajdhani',sans-serif;--font-body:'Exo 2',sans-serif;
}
/* ─── Keyframes ─── */
@keyframes goldShine{0%{background-position:200% center}100%{background-position:-200% center}}
@keyframes pulseGlow{0%,100%{box-shadow:0 0 10px currentColor}50%{box-shadow:0 0 35px currentColor,0 0 70px currentColor}}
@keyframes shimmer{0%{left:-100%}100%{left:200%}}
@keyframes holographic{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes nebulaSwirl{0%{transform:rotate(0deg) scale(1)}50%{transform:rotate(180deg) scale(1.1)}100%{transform:rotate(360deg) scale(1)}}
@keyframes nebulaFloat{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(6px,-8px) scale(1.05)}66%{transform:translate(-4px,5px) scale(0.97)}}
@keyframes beamRotate{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
@keyframes fireFlicker{0%,100%{transform:scaleY(1) translateX(0);opacity:.85}25%{transform:scaleY(1.12) translateX(-2px)}75%{transform:scaleY(.93) translateX(2px)}}
@keyframes lightningFlash{0%,88%,100%{opacity:0}90%,96%{opacity:1}93%,99%{opacity:.25}}
@keyframes driftParticle{0%{transform:translate(0,0) scale(1);opacity:.9}100%{transform:translate(var(--dx,15px),var(--dy,-40px)) scale(0);opacity:0}}
@keyframes holoSheen{0%{background-position:0% 50%;opacity:.5}50%{background-position:100% 50%;opacity:1}100%{background-position:0% 50%;opacity:.5}}
@keyframes iconGodPulse{0%,100%{box-shadow:0 0 22px #ff2200,0 0 55px #880000,inset 0 0 22px rgba(255,0,0,.3)}50%{box-shadow:0 0 45px #ff4400,0 0 90px #ff0000,inset 0 0 45px rgba(255,80,0,.6)}}
@keyframes rainbowBorder{0%{border-color:#f00}16%{border-color:#f80}33%{border-color:#ff0}50%{border-color:#0f0}66%{border-color:#08f}83%{border-color:#80f}100%{border-color:#f00}}
@keyframes screenShake{0%,100%{transform:translate(0,0)}10%{transform:translate(-8px,4px)}20%{transform:translate(8px,-4px)}30%{transform:translate(-6px,6px)}40%{transform:translate(6px,-2px)}50%{transform:translate(-4px,4px)}}
@keyframes cardFlipIn{0%{transform:rotateY(90deg) scale(.75);opacity:0;filter:brightness(4)}55%{transform:rotateY(-8deg) scale(1.06)}100%{transform:rotateY(0deg) scale(1);opacity:1;filter:brightness(1)}}
@keyframes godReveal{0%{transform:scale(.4) rotate(-12deg);opacity:0;filter:brightness(6) saturate(3)}55%{transform:scale(1.25) rotate(3deg);opacity:1;filter:brightness(2)}100%{transform:scale(1) rotate(0);opacity:1;filter:brightness(1)}}
@keyframes glassShimmer{0%{transform:translateX(-100%) skewX(-15deg)}100%{transform:translateX(300%) skewX(-15deg)}}
@keyframes orbPulse{0%,100%{transform:scale(1);opacity:.4}50%{transform:scale(1.3);opacity:.8}}
@keyframes trainerSparkle{0%{transform:translate(0,0) scale(1) rotate(0deg);opacity:1}100%{transform:translate(var(--dx),var(--dy)) scale(0) rotate(720deg);opacity:0}}
@keyframes trainerGlow{0%,100%{box-shadow:0 0 8px var(--trainer-color,#fff),0 0 20px var(--trainer-color,#fff)}50%{box-shadow:0 0 20px var(--trainer-color,#fff),0 0 50px var(--trainer-color,#fff),inset 0 0 15px rgba(255,255,255,.1)}}
@keyframes arenaPulse{0%,100%{opacity:.6;transform:scale(1)}50%{opacity:1;transform:scale(1.02)}}
@keyframes netWave{0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.04)}}
@keyframes ballBounce{0%,100%{transform:translateY(0) scale(1)}40%{transform:translateY(-12px) scale(.92,1.08)}60%{transform:translateY(-6px)}}
@keyframes floatCard{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes statBarFill{0%{width:0}100%{width:var(--bar-w)}}

/* ─── Card wrapper ─── */
.mbt-card-wrap{position:relative;display:inline-block;cursor:pointer;transition:transform .38s cubic-bezier(.34,1.56,.64,1),filter .38s ease;perspective:800px}
.mbt-card-wrap:hover{transform:translateY(-12px) scale(1.07) rotateX(4deg) rotateY(-2deg);z-index:10;filter:drop-shadow(0 24px 48px rgba(0,0,0,.85))}
.mbt-card{width:140px;min-height:210px;border-radius:14px;position:relative;overflow:hidden;font-family:var(--font-rivals);user-select:none;transform-style:preserve-3d}
.mbt-card::after{content:'';position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,255,255,.18),transparent);transform:skewX(-15deg);z-index:25;pointer-events:none;border-radius:14px;opacity:0}
.mbt-card-wrap:hover .mbt-card::after{animation:glassShimmer .7s ease .05s forwards;opacity:1}

/* Card bg/overlay */
.mbt-card-bg-image{position:absolute;inset:0;background-size:cover;background-position:center top;border-radius:14px;z-index:0}
.mbt-card-overlay{position:absolute;inset:0;border-radius:14px;z-index:1;pointer-events:none}
.mbt-card-hover-overlay{position:absolute;inset:0;border-radius:14px;z-index:22;pointer-events:none;opacity:0;background:radial-gradient(ellipse at 50% 30%,rgba(255,255,255,.12) 0%,transparent 70%);transition:opacity .35s}
.mbt-card-wrap:hover .mbt-card-hover-overlay{opacity:1}

/* Photo */
.mbt-card-photo{position:absolute!important;top:12%!important;left:0!important;width:100%!important;height:46%!important;object-fit:cover!important;object-position:center top;border-radius:0!important;z-index:3}
.mbt-card-photo-placeholder{position:absolute;top:18%;left:50%;transform:translateX(-50%);font-size:2rem;z-index:3;text-align:center;filter:drop-shadow(0 2px 8px rgba(0,0,0,.7))}
/* Trainer photo — occupa tutta la carta tranne stats */
.mbt-card-photo-trainer{position:absolute!important;top:0!important;left:0!important;width:100%!important;height:68%!important;object-fit:cover!important;object-position:center top;border-radius:14px 14px 0 0!important;z-index:3}

/* OVR */
.mbt-card-ovr{position:absolute;top:6px;left:8px;font-family:var(--font-rivals);font-weight:900;z-index:10;text-shadow:0 0 12px currentColor,0 2px 4px rgba(0,0,0,.9);line-height:1}

/* Tier label */
.mbt-card-tier-label{position:absolute;top:6px;right:7px;font-size:.38rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;z-index:10;text-shadow:0 0 8px currentColor;opacity:.9}

/* Name block */
.mbt-card-name-block{position:absolute;bottom:56px;left:0;right:0;text-align:center;z-index:10;padding:0 4px;line-height:1.1}
.mbt-card-firstname{display:block;font-size:.38rem;font-weight:400;letter-spacing:2px;text-transform:uppercase;opacity:.8;text-shadow:0 0 8px currentColor}
.mbt-card-lastname{display:block;font-weight:900;letter-spacing:1px;text-transform:uppercase;text-shadow:0 0 14px currentColor}

/* Role */
.mbt-card-role{position:absolute;bottom:40px;left:0;right:0;text-align:center;font-size:.38rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;z-index:10;opacity:.75}

/* Stats — 6 attributi su 2 righe */
.mbt-card-stats-6{position:absolute;bottom:3px;left:3px;right:3px;z-index:10}
.mbt-stats-row{display:flex;justify-content:space-around;margin-bottom:1px}
.mbt-stat{text-align:center;flex:1}
.mbt-stat-val{font-size:.58rem;font-weight:900;line-height:1;text-shadow:0 0 8px currentColor}
.mbt-stat-lbl{font-size:.28rem;color:#aaa;letter-spacing:.5px;text-transform:uppercase;line-height:1}

/* Trainer special power badge */
.trainer-power-badge{position:absolute;bottom:28px;left:4px;right:4px;text-align:center;z-index:12;font-size:.32rem;letter-spacing:.5px;text-transform:uppercase;padding:2px 4px;border-radius:4px;border:1px solid currentColor}

/* HP bars */
.hp-bar-container{height:10px;background:#1a1a2a;border-radius:5px;overflow:hidden;border:1px solid #2a2a3a}
.hp-bar-fill{height:100%;background:linear-gradient(90deg,#16a34a,#4ade80);border-radius:5px;transition:width .5s ease}
.hp-bar-fill.danger{background:linear-gradient(90deg,#dc2626,#ef4444);animation:pulseGlow 1s infinite}

/* Battle arena field */
.battle-field-outer{background:linear-gradient(180deg,#03070a 0%,#061520 100%);border:2px solid #0a2040;border-radius:16px;padding:10px;position:relative;overflow:hidden}
.beach-court{background:linear-gradient(180deg,#c8973a 0%,#d4a445 100%);border-radius:10px;position:relative;overflow:hidden}
.court-line{background:rgba(255,255,255,.55);position:absolute;border-radius:1px}
.court-net{background:rgba(255,255,255,.9);position:absolute;left:0;right:0;z-index:5}
.court-net-posts{background:#ccc;position:absolute;z-index:6;border-radius:2px}
.fighter-slot{border:1px dashed rgba(255,255,255,.25);border-radius:8px;display:flex;align-items:center;justify-content:center;min-height:90px;transition:border-color .2s,background .2s;position:relative}
.fighter-slot.active{border-color:#ffd700!important;background:rgba(255,215,0,.07)}
.trainer-slot{border:2px dashed rgba(100,255,100,.35);border-radius:8px;display:flex;align-items:center;justify-content:center;min-height:80px;background:rgba(0,30,0,.25)}
.trainer-slot.equipped{border-color:rgba(100,255,100,.7);background:rgba(0,50,0,.3)}

/* Scoreboard */
.scoreboard{background:linear-gradient(180deg,#050510,#0a0a20);border:1px solid #1e1e3a;border-radius:10px;padding:10px;text-align:center}

/* Battle log */
.battle-log{background:#05050f;border:1px solid #1e1e3a;border-radius:8px;padding:10px;max-height:160px;overflow-y:auto;font-family:var(--font-body);font-size:.72rem}

/* Arena badge */
.arena-badge{border-radius:10px;padding:16px;text-align:center;cursor:pointer;transition:transform .2s,box-shadow .2s;position:relative;overflow:hidden}
.arena-badge:hover{transform:translateY(-4px)}
.arena-badge-anim{animation:arenaPulse 3s ease-in-out infinite}
.arena-base{background:linear-gradient(135deg,#2a1f0f,#5a3a0f);border:2px solid #cd7f32}
.arena-epica{background:linear-gradient(135deg,#1a003a,#4a0080);border:2px solid #9b59b6}
.arena-leggendaria{background:linear-gradient(135deg,#0a0a0a,#2a2a2a);border:2px solid #fff}
.arena-toty{background:linear-gradient(135deg,#000820,#001855);border:2px solid #4169e1}
.arena-icona{background:linear-gradient(135deg,#1a0f00,#3d2800);border:3px solid #ffd700}
.arena-icona-epica{background:linear-gradient(135deg,#1a0030,#4a0090);border:3px solid #cc44ff}
.arena-icona-leggendaria{background:linear-gradient(135deg,#111,#2a2a2a);border:3px solid #fff;box-shadow:0 0 30px rgba(255,255,255,.3)}
.arena-toty-plus{background:linear-gradient(135deg,#000820,#001060);border:4px solid #4169e1;box-shadow:0 0 30px rgba(65,105,225,.5)}
.arena-god{background:linear-gradient(135deg,#0a0000,#2a0000);border:4px solid #ff2200;box-shadow:0 0 40px rgba(255,34,0,.6)}
.arena-omega{background:#000;border:4px solid transparent;box-shadow:0 0 60px rgba(255,0,200,.8),0 0 120px rgba(0,100,255,.6)}

/* Pack cards */
.pack-card{transition:transform .3s,box-shadow .3s}
.pack-card:hover{transform:scale(1.04) translateY(-4px)}
.pack-base{background:linear-gradient(160deg,#2a1f0f,#5a3a0f,#2a1f0f);border:2px solid #cd7f32;box-shadow:0 0 20px rgba(205,127,50,.3)}
.pack-epico{background:linear-gradient(160deg,#1a0033,#4a0080,#1a0033);border:2px solid #9b59b6;box-shadow:0 0 25px rgba(155,89,182,.4)}
.pack-leggenda{background:linear-gradient(160deg,#1a0a00,#3a1a00,#1a0a00);border:2px solid #ff6600;box-shadow:0 0 30px rgba(255,100,0,.5)}

/* Collection / buttons */
.collection-filter-btn{border:1px solid;border-radius:20px;padding:4px 12px;cursor:pointer;font-size:.7rem;font-family:var(--font-rivals);transition:all .2s;background:transparent}
.collection-filter-btn.active{background:var(--rivals-gold);border-color:var(--rivals-gold);color:#000}
.collection-filter-btn:not(.active){color:var(--rivals-gold);border-color:#555}
.creator-preview-wrap{display:flex;justify-content:center;padding:20px;background:radial-gradient(ellipse at center,rgba(255,215,0,.06) 0%,transparent 70%);border-radius:12px;border:1px dashed #333}
.pack-revealed-card{animation:cardFlipIn .75s cubic-bezier(.34,1.56,.64,1) both}
.pack-revealed-card-god{animation:godReveal 1.1s cubic-bezier(.34,1.56,.64,1) both}

/* Battle action buttons animated */
.battle-btn-atk{background:linear-gradient(135deg,#4a0010,#8b0000)!important;border:1px solid #dc2626!important;transition:all .2s!important}
.battle-btn-atk:hover{box-shadow:0 0 18px #dc2626,0 0 40px rgba(220,38,38,.4)!important;transform:scale(1.04)!important}
.battle-btn-sp{background:linear-gradient(135deg,#2a1a00,#7a4e00)!important;border:1px solid #ffd700!important;transition:all .2s!important}
.battle-btn-sp:hover{box-shadow:0 0 18px #ffd700,0 0 40px rgba(255,215,0,.4)!important;transform:scale(1.04)!important}
.battle-btn-def{background:linear-gradient(135deg,#001040,#1e3a8a)!important;border:1px solid #4169e1!important;transition:all .2s!important}
.battle-btn-def:hover{box-shadow:0 0 18px #4169e1,0 0 40px rgba(65,105,225,.4)!important;transform:scale(1.04)!important}
.battle-btn-fin{background:linear-gradient(135deg,#200040,#6a0080)!important;border:1px solid #cc44ff!important;transition:all .2s!important}
.battle-btn-fin:hover{box-shadow:0 0 18px #cc44ff,0 0 40px rgba(204,68,255,.4)!important;transform:scale(1.04)!important}
</style>
"""


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

ROLES = [
    "SPIKER","IRONBLOCKER","DIFENSORE","ACER","SPECIALISTA",
    "TRAINER - Fisioterapista","TRAINER - Mental Coach","TRAINER - Scoutman"
]

ROLE_ICONS = {
    "SPIKER":"⚡","IRONBLOCKER":"🛡️","DIFENSORE":"🤿","ACER":"🎯","SPECIALISTA":"🔮",
    "TRAINER - Fisioterapista":"💊","TRAINER - Mental Coach":"🧠","TRAINER - Scoutman":"🔭"
}

ROLE_DESCRIPTIONS = {
    "SPIKER":"Super Attacco: Nocchino di Ghiaccio – attacco che non fallisce mai",
    "IRONBLOCKER":"Fortezza di Titanio (Annulla danni) o Muro Corna (danno+difesa)",
    "DIFENSORE":"Dig Classico / Sky Dive / Sabbia Mobile (recupera HP)",
    "ACER":"Jump Float Infuocato – danni critici doppi se vince il turno battuta",
    "SPECIALISTA":"Seconda Intenzione – attacca nel turno difesa",
    "TRAINER - Fisioterapista":"Riduce consumo Stamina del 20%",
    "TRAINER - Mental Coach":"Aumenta danni Super quando HP < 30%",
    "TRAINER - Scoutman":"Vedi in anticipo la prima carta CPU",
}

# Poteri Trainer che si applicano in battaglia
TRAINER_POWERS = {
    "TRAINER - Fisioterapista": {
        "id":"fisio","label":"STAMINA -20%","desc":"Riduce consumo Stamina del 20%",
        "color":"#16a34a","border_color":"#22c55e","bg":"rgba(0,40,0,.6)"
    },
    "TRAINER - Mental Coach": {
        "id":"mental","label":"SUP +30% HP crit","desc":"Danni Super +30% quando HP < 30%",
        "color":"#dc2626","border_color":"#ef4444","bg":"rgba(40,0,0,.6)"
    },
    "TRAINER - Scoutman": {
        "id":"scout","label":"SCOUT ATTIVO","desc":"Rivela prossima mossa CPU",
        "color":"#9b59b6","border_color":"#a855f7","bg":"rgba(20,0,40,.6)"
    },
}

CARD_TIERS = {
    "Bronzo Comune":    {"ovr_range":(40,44),"color":"#cd7f32","rarity":0},
    "Bronzo Raro":      {"ovr_range":(45,49),"color":"#e8902a","rarity":1},
    "Argento Comune":   {"ovr_range":(50,54),"color":"#c0c0c0","rarity":2},
    "Argento Raro":     {"ovr_range":(55,59),"color":"#d8d8d8","rarity":3},
    "Oro Comune":       {"ovr_range":(60,64),"color":"#ffd700","rarity":4},
    "Oro Raro":         {"ovr_range":(65,69),"color":"#ffec4a","rarity":5},
    "Eroe":             {"ovr_range":(70,74),"color":"#9b59b6","rarity":6},
    "IF (In Form)":     {"ovr_range":(75,79),"color":"#b07dd0","rarity":7},
    "Leggenda":         {"ovr_range":(80,84),"color":"#ffffff","rarity":8},
    "TOTY":             {"ovr_range":(85,89),"color":"#4169e1","rarity":9},
    "TOTY Evoluto":     {"ovr_range":(90,94),"color":"#6a8fff","rarity":10},
    "GOAT":             {"ovr_range":(95,99),"color":"#ff4400","rarity":11},
    "ICON BASE":        {"ovr_range":(100,104),"color":"#ffd700","rarity":12},
    "ICON EPICA":       {"ovr_range":(105,109),"color":"#cc44ff","rarity":13},
    "ICON LEGGENDARIA": {"ovr_range":(110,114),"color":"#ffffff","rarity":14},
    "ICON TOTY":        {"ovr_range":(115,119),"color":"#4169e1","rarity":15},
    "ICON GOD":         {"ovr_range":(120,125),"color":"#ff2200","rarity":16},
}

TIER_CARD_IMAGES = {
    "Bronzo Comune":"BRONZO_png.webp","Bronzo Raro":"BRONZO_RARO_png.webp",
    "Argento Comune":"ARGENTO.png","Argento Raro":"argento_raro_png.webp",
    "Oro Comune":"ORO.png","Oro Raro":"ORO_RARO_png.webp",
    "Eroe":"EROE.png","IF (In Form)":"EROE.png","Leggenda":"LEGGENDA.png",
    "TOTY":"TOTY.webp","TOTY Evoluto":"TOTY_EVOLUTO.png","GOAT":"GOAT_png.webp",
    "ICON BASE":"ICON_BASE.png","ICON EPICA":"ICON_BASE.png",
    "ICON LEGGENDARIA":"ICON_LEGGENDARIA.png","ICON TOTY":"ICON_TOTY_png.webp",
    "ICON GOD":"ICONA_GOD.png",
}

def get_tier_by_ovr(ovr):
    ovr = int(ovr)
    for tn,td in CARD_TIERS.items():
        lo,hi = td["ovr_range"]
        if lo<=ovr<=hi: return tn
    if ovr>=120: return "ICON GOD"
    if ovr>=115: return "ICON TOTY"
    if ovr>=110: return "ICON LEGGENDARIA"
    if ovr>=105: return "ICON EPICA"
    if ovr>=100: return "ICON BASE"
    if ovr>=95:  return "GOAT"
    return "TOTY Evoluto"

PACKS = {
    "Base":{"price":200,"css_class":"pack-base","label_color":"#cd7f32",
        "description":"6 carte | Comuni e Rare",
        "weights":{"Bronzo Comune":.30,"Bronzo Raro":.25,"Argento Comune":.20,
                   "Argento Raro":.12,"Oro Comune":.07,"Oro Raro":.04,"Eroe":.015,"IF (In Form)":.005}},
    "Epico":{"price":500,"css_class":"pack-epico","label_color":"#9b59b6",
        "description":"6 carte | Da Oro a Leggenda",
        "weights":{"Oro Comune":.25,"Oro Raro":.22,"Eroe":.18,"IF (In Form)":.15,
                   "Leggenda":.08,"TOTY":.04,"TOTY Evoluto":.02,"GOAT":.01,
                   "ICON BASE":.008,"ICON EPICA":.002}},
    "Leggenda":{"price":1200,"css_class":"pack-leggenda","label_color":"#ff6600",
        "description":"6 carte | Alta probabilità di Speciali",
        "weights":{"Leggenda":.25,"TOTY":.20,"TOTY Evoluto":.18,"GOAT":.12,
                   "ICON BASE":.10,"ICON EPICA":.07,"ICON LEGGENDARIA":.04,
                   "ICON TOTY":.02,"ICON GOD":.01,"IF (In Form)":.01}},
}

ARENE = [
    {"min_level":1, "max_level":2, "name":"Arena Base",           "css":"arena-base",             "color":"#cd7f32","icon":"🏟️"},
    {"min_level":3, "max_level":4, "name":"Arena Epica",          "css":"arena-epica",            "color":"#9b59b6","icon":"⚡"},
    {"min_level":5, "max_level":6, "name":"Arena Leggendaria",    "css":"arena-leggendaria",      "color":"#ffffff","icon":"👑"},
    {"min_level":7, "max_level":8, "name":"Arena TOTY",           "css":"arena-toty",             "color":"#4169e1","icon":"🌟"},
    {"min_level":9, "max_level":10,"name":"Arena ICONA",          "css":"arena-icona",            "color":"#ffd700","icon":"🏆"},
    {"min_level":11,"max_level":12,"name":"Arena ICONA EPICA",    "css":"arena-icona-epica",      "color":"#cc44ff","icon":"💫"},
    {"min_level":13,"max_level":14,"name":"Arena ICONA LEGGEND.", "css":"arena-icona-leggendaria","color":"#ffffff","icon":"✨"},
    {"min_level":15,"max_level":16,"name":"Arena TOTY SUPREMA",   "css":"arena-toty-plus",        "color":"#4169e1","icon":"🔮"},
    {"min_level":17,"max_level":18,"name":"Arena GOD MODE",       "css":"arena-god",              "color":"#ff2200","icon":"🔥"},
    {"min_level":19,"max_level":20,"name":"Arena OMEGA",          "css":"arena-omega",            "color":"#ff00cc","icon":"⚜️"},
]

XP_PER_LEVEL = [0,100,250,450,700,1000,1350,1750,2200,2700,
                3250,3850,4500,5200,5950,6750,7600,8500,9450,10450]

SPECIAL_MOVES = [
    {"id":"nocchino_ghiaccio","name":"Nocchino di Ghiaccio","role":"SPIKER","cost_coins":300,"dmg":35,"desc":"Attacco che non fallisce mai"},
    {"id":"fortezza_titanio","name":"Fortezza di Titanio","role":"IRONBLOCKER","cost_coins":280,"dmg":0,"desc":"Annulla il prossimo attacco"},
    {"id":"muro_corna","name":"Muro Corna","role":"IRONBLOCKER","cost_coins":320,"dmg":20,"desc":"Danno e difesa simultanei"},
    {"id":"sky_dive","name":"Sky Dive","role":"DIFENSORE","cost_coins":250,"dmg":0,"desc":"Recupera 20 HP"},
    {"id":"sabbia_mobile","name":"Sabbia Mobile","role":"DIFENSORE","cost_coins":270,"dmg":0,"desc":"Recupera 30 HP"},
    {"id":"jump_float","name":"Jump Float Infuocato","role":"ACER","cost_coins":350,"dmg":40,"desc":"Danni critici doppi se primo turno"},
    {"id":"skyball","name":"SKYBALL","role":"ACER","cost_coins":400,"dmg":45,"desc":"Danno critico al morale avversario"},
    {"id":"seconda_intenzione","name":"Seconda Intenzione","role":"SPECIALISTA","cost_coins":380,"dmg":30,"desc":"Attacca nel turno difesa"},
    {"id":"clutch_rise","name":"Clutch Rise","role":None,"cost_coins":500,"dmg":50,"desc":"Danno x2 quando HP < 30%"},
    {"id":"final_spike","name":"FINAL SPIKE","role":None,"cost_coins":800,"dmg":80,"desc":"MOSSA FINALE — danno devastante"},
]

SUPERPOWERS = [
    {"id":"iron_will","name":"Iron Will","desc":"Riduce danni subiti del 10% per livello","max_level":5,"cost_per_level":200},
    {"id":"kill_shot","name":"Kill Shot","desc":"Aumenta ATK del 8% per livello","max_level":5,"cost_per_level":200},
    {"id":"stamina_boost","name":"Stamina Boost","desc":"Stamina si ricarica 15% più veloce per livello","max_level":5,"cost_per_level":150},
    {"id":"clutch_god","name":"Clutch God","desc":"HP critico (<30%): danno +20% per livello","max_level":3,"cost_per_level":350},
    {"id":"vision","name":"Vision","desc":"Vedi sempre la prossima mossa CPU per livello 3+","max_level":3,"cost_per_level":300},
]

# ─── CARDS PER PAGE ──────────────────────────────────────────────────────────
CARDS_PER_PAGE = 20   # Lazy loading: massimo carte renderizzate per volta


# ─── CACHE IMAGE LOADING ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_image_b64_cached(path: str) -> tuple:
    """Carica un'immagine da disco e la codifica in base64 — risultato cachato."""
    if not path or not os.path.exists(path):
        return None, None
    ext  = path.rsplit(".",1)[-1].lower()
    mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg",
            "webp":"image/webp","gif":"image/gif"}.get(ext,"image/png")
    try:
        with open(path,"rb") as f:
            return base64.b64encode(f.read()).decode(), mime
    except Exception:
        return None, None


@st.cache_data(show_spinner=False)
def _get_card_bg_b64(tier_name: str) -> tuple:
    """Carica il background PNG della carta per tier — cachato in sessione."""
    img_filename = TIER_CARD_IMAGES.get(tier_name,"")
    if not img_filename:
        return None, None
    for search_dir in [ASSETS_CARDS_DIR, "assets", "/mnt/user-data/uploads"]:
        p = os.path.join(search_dir, img_filename)
        if os.path.exists(p):
            return _load_image_b64_cached(p)
    return None, None


# ─── ANIMATION OVERLAYS (deterministici, no random per evitare re-render) ────

# Seed deterministico basato su card id per evitare che ogni rerun rimescoli le particelle
def _det_particles(card_id: str, n: int, color: str, min_sz: int = 2, max_sz: int = 4) -> str:
    """Genera particelle con posizioni deterministiche basate su card_id."""
    h = int(hashlib.md5(card_id.encode()).hexdigest()[:8], 16)
    out = ""
    for i in range(n):
        seed_i = (h >> i) & 0xFFFF
        dx  = (seed_i % 61) - 30
        dy  = -((seed_i >> 6) % 46) - 8
        dl  = ((seed_i >> 3) % 25) / 10.0
        dur = 1.5 + ((seed_i >> 1) % 15) / 10.0
        top = 20 + (seed_i >> 4) % 55
        lft = 10 + (seed_i >> 2) % 80
        sz  = min_sz + (seed_i % (max_sz - min_sz + 1))
        out += (
            '<div style="position:absolute;width:{sz}px;height:{sz}px;background:{c};border-radius:50%;'
            'top:{t}%;left:{l}%;animation:driftParticle {dur:.1f}s {dl:.1f}s infinite;'
            '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 5px {c}"></div>'
        ).format(sz=sz,c=color,t=top,l=lft,dur=dur,dl=dl,dx=dx,dy=dy)
    return out


def _det_trainer_sparkles(card_id: str, color: str, n: int = 10) -> str:
    """Genera scintille luccicanti per le carte Trainer."""
    h = int(hashlib.md5(("trainer"+card_id).encode()).hexdigest()[:8], 16)
    out = ""
    shapes = ["✦","✧","★","⬡","◆","·"]
    for i in range(n):
        seed_i = (h * (i+7)) & 0xFFFF
        dx  = (seed_i % 71) - 35
        dy  = -((seed_i >> 5) % 56) - 5
        dl  = ((seed_i >> 2) % 30) / 10.0
        dur = 1.2 + ((seed_i >> 1) % 18) / 10.0
        top = 5 + (seed_i >> 4) % 85
        lft = 5 + (seed_i >> 3) % 85
        sz  = 0.4 + (seed_i % 6) / 10.0
        shp = shapes[seed_i % len(shapes)]
        out += (
            '<div style="position:absolute;font-size:{sz}rem;color:{c};'
            'top:{t}%;left:{l}%;animation:trainerSparkle {dur:.1f}s {dl:.1f}s infinite;'
            '--dx:{dx}px;--dy:{dy}px;z-index:8;text-shadow:0 0 4px {c};">{shp}</div>'
        ).format(sz=sz,c=color,t=top,l=lft,dur=dur,dl=dl,dx=dx,dy=dy,shp=shp)
    return out


def _get_card_animation_overlay(tier_name: str, color: str, rarity: int, card_id: str = "x") -> str:
    if tier_name == "ICON GOD":
        fire = (
            '<div style="position:absolute;bottom:0;left:0;right:0;height:40%;'
            'background:linear-gradient(0deg,rgba(255,40,0,.55),rgba(255,100,0,.22),transparent);'
            'animation:fireFlicker .4s infinite alternate;pointer-events:none"></div>'
            '<div style="position:absolute;top:12%;left:47%;width:3px;height:72%;'
            'background:linear-gradient(180deg,rgba(255,255,0,.95),transparent);'
            'transform:rotate(8deg);animation:lightningFlash 1.2s infinite;'
            'box-shadow:0 0 8px #ff0;pointer-events:none"></div>'
        )
        particles = _det_particles(card_id, 8, "#ff6600")
        border_anim = '<div style="position:absolute;inset:-2px;border-radius:16px;border:2px solid #ff2200;animation:iconGodPulse 1.5s infinite;pointer-events:none;z-index:30"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>{}'.format(fire,particles,border_anim)
    elif tier_name == "ICON TOTY":
        beam = '<div style="position:absolute;inset:-40px;background:conic-gradient(from 0deg,transparent 0deg,rgba(65,105,225,.35) 30deg,transparent 60deg,rgba(100,180,255,.25) 120deg,transparent 150deg);animation:beamRotate 3s linear infinite;border-radius:50%;pointer-events:none"></div>'
        particles = _det_particles(card_id, 10, color)
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(beam,particles)
    elif tier_name == "ICON LEGGENDARIA":
        particles = _det_particles(card_id, 7, "#ffffff")
        sheen = '<div style="position:absolute;inset:0;background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,.14) 50%,transparent 70%);background-size:200% 200%;animation:holographic 2.2s infinite;pointer-events:none"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(sheen,particles)
    elif tier_name == "ICON EPICA":
        nebula = '<div style="position:absolute;inset:-30px;background:conic-gradient(from 0deg,transparent,rgba(180,0,255,.2),transparent,rgba(100,0,200,.15),transparent);animation:nebulaSwirl 5s linear infinite;pointer-events:none"></div>'
        particles = _det_particles(card_id, 6, color)
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(nebula,particles)
    elif tier_name == "ICON BASE":
        nebula = '<div style="position:absolute;width:80px;height:80px;top:-10px;left:-10px;background:radial-gradient(ellipse at center,rgba(255,215,0,.25) 0%,transparent 70%);animation:nebulaFloat 6s ease-in-out infinite;pointer-events:none"></div>'
        particles = _det_particles(card_id, 5, color, 2, 3)
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(nebula,particles)
    elif tier_name == "GOAT":
        fire = '<div style="position:absolute;bottom:0;left:0;right:0;height:28%;background:linear-gradient(0deg,rgba(255,68,0,.45),transparent);animation:fireFlicker .6s infinite alternate;pointer-events:none"></div>'
        particles = _det_particles(card_id, 6, color)
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(fire,particles)
    elif tier_name in ("TOTY","TOTY Evoluto"):
        beam = '<div style="position:absolute;inset:-30px;background:conic-gradient(from 0deg,transparent 0deg,rgba(65,105,225,.22) 30deg,transparent 60deg);animation:beamRotate 4s linear infinite;border-radius:50%;pointer-events:none"></div>'
        particles = _det_particles(card_id, 4, color, 2, 2)
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>'.format(beam,particles)
    elif tier_name == "Leggenda":
        sheen = '<div style="position:absolute;inset:0;background:linear-gradient(135deg,transparent 30%,rgba(255,255,255,.11) 50%,transparent 70%);background-size:200% 200%;animation:holographic 2.8s infinite;pointer-events:none"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}</div>'.format(sheen)
    elif tier_name in ("Eroe","IF (In Form)"):
        nebula = '<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(155,89,182,.28) 0%,transparent 70%);animation:holoSheen 3.5s infinite;pointer-events:none"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}</div>'.format(nebula)
    elif rarity >= 5:
        shimmer = '<div style="position:absolute;top:0;left:-80%;width:40%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,215,0,.22),transparent);animation:shimmer 2.2s infinite;transform:skewX(-15deg);pointer-events:none"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}</div>'.format(shimmer)
    elif rarity >= 2:
        sheen = '<div style="position:absolute;inset:0;background:linear-gradient(135deg,transparent 40%,rgba(255,255,255,.07) 50%,transparent 60%);background-size:200% 200%;animation:holoSheen 4.5s infinite;pointer-events:none"></div>'
        return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}</div>'.format(sheen)
    return ""


def _get_trainer_animation_overlay(card_id: str, trainer_color: str) -> str:
    """Overlay animato speciale per carte Trainer: polvere luccicante."""
    sparkles = _det_trainer_sparkles(card_id, trainer_color, 12)
    border_anim = (
        '<div style="position:absolute;inset:0;border-radius:14px;pointer-events:none;z-index:20;'
        'box-shadow:inset 0 0 15px {c}55;animation:trainerGlow 2s ease-in-out infinite;'
        '--trainer-color:{c}"></div>'
    ).format(c=trainer_color)
    shimmer = (
        '<div style="position:absolute;top:0;left:-80%;width:40%;height:100%;'
        'background:linear-gradient(105deg,transparent,{c}44,transparent);'
        'animation:shimmer 2.5s infinite;transform:skewX(-15deg);pointer-events:none"></div>'
    ).format(c=trainer_color)
    return '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">{}{}</div>{}'.format(shimmer, sparkles, border_anim)


def _get_card_border_style(tier_name, color, rarity):
    if tier_name=="ICON GOD":
        return "border:3px solid #ff2200;box-shadow:0 0 22px #ff2200,0 0 50px #880000,0 0 90px #440000;border-radius:14px;"
    elif tier_name=="ICON TOTY":
        return "border:3px solid {c};box-shadow:0 0 25px {c},0 0 60px {c}55,0 0 100px {c}33;border-radius:14px;".format(c=color)
    elif tier_name in ("ICON LEGGENDARIA","ICON EPICA","ICON BASE"):
        return "border:2px solid {c};box-shadow:0 0 20px {c}88,0 0 40px {c}44;border-radius:14px;".format(c=color)
    elif tier_name=="GOAT":
        return "border:2px solid {c};box-shadow:0 0 18px {c}99,0 0 35px {c}44;border-radius:14px;".format(c=color)
    elif tier_name in ("TOTY","TOTY Evoluto"):
        return "border:2px solid {c};box-shadow:0 0 16px {c}99,0 0 32px {c}44;border-radius:14px;".format(c=color)
    elif tier_name=="Leggenda":
        return "border:2px solid #ffffff;box-shadow:0 0 16px rgba(255,255,255,.5),0 0 32px rgba(255,255,255,.2);border-radius:14px;"
    elif rarity>=6:
        return "border:2px solid {c};box-shadow:0 0 14px {c}88;border-radius:14px;".format(c=color)
    elif rarity>=4:
        return "border:1px solid {c};box-shadow:0 0 10px {c}66;border-radius:14px;".format(c=color)
    else:
        return "border:1px solid {c}55;border-radius:14px;".format(c=color)


# ─── IS TRAINER ──────────────────────────────────────────────────────────────

def _is_trainer(card) -> bool:
    return "TRAINER" in card.get("ruolo","")


# ─── CARD RENDERER ───────────────────────────────────────────────────────────

def render_card_html(card_data, size="normal", show_special_effects=True):
    """Genera HTML completo per una carta MBT — v4.0 con 6 stat + Trainer support."""
    ovr       = int(card_data.get("overall",40))
    tier_name = get_tier_by_ovr(ovr)
    ti        = CARD_TIERS.get(tier_name, CARD_TIERS["Bronzo Comune"])
    color     = ti["color"]
    rarity    = ti.get("rarity",0)
    nome      = card_data.get("nome","?")
    cognome   = card_data.get("cognome","")
    role      = card_data.get("ruolo","SPIKER")
    role_icon = ROLE_ICONS.get(role,"⚡")
    photo_path= card_data.get("foto_path","")
    card_id   = card_data.get("id","x") or card_data.get("instance_id","x") or "x"
    is_trainer= _is_trainer(card_data)

    atk = int(card_data.get("attacco",40))
    dif = int(card_data.get("difesa", 40))
    bat = int(card_data.get("battuta",40))
    mur = int(card_data.get("muro",   40))
    ric = int(card_data.get("ricezione",40))
    alz = int(card_data.get("alzata", 40))

    widths = {"small":"105px","normal":"140px","large":"185px"}
    fovrs  = {"small":"1.05rem","normal":"1.4rem","large":"1.9rem"}
    fnames = {"small":"0.55rem","normal":"0.72rem","large":"0.95rem"}
    ffirsts= {"small":"0.32rem","normal":"0.42rem","large":"0.52rem"}
    width  = widths.get(size,"140px")
    font_ovr  = fovrs.get(size,"1.4rem")
    font_name = fnames.get(size,"0.72rem")
    font_first= ffirsts.get(size,"0.42rem")

    # Determina se Trainer e colori speciali
    trainer_color = ""
    trainer_power_html = ""
    if is_trainer:
        tp = TRAINER_POWERS.get(role,{})
        trainer_color = tp.get("border_color","#ffffff")
        lbl = tp.get("label","TRAINER")
        trainer_power_html = (
            '<div class="trainer-power-badge" style="color:{c};border-color:{c};'
            'background:{bg};font-size:{fs}rem">{lbl}</div>'
        ).format(c=trainer_color, bg=tp.get("bg","rgba(0,0,0,.5)"),
                 fs="0.28" if size=="small" else "0.32", lbl=lbl)
        # Per Trainer il bordo è il colore speciale
        _border_color = trainer_color
    else:
        _border_color = color

    # Background immagine
    bg_b64, bg_mime = _get_card_bg_b64(tier_name)
    if bg_b64:
        bg_style = "background-image:url('data:{m};base64,{b}');background-size:cover;background-position:center top;".format(m=bg_mime,b=bg_b64)
    else:
        fallbacks = {
            "Bronzo Comune":"linear-gradient(160deg,#3d2b1f,#6b4226,#3d2b1f)",
            "Bronzo Raro":"linear-gradient(160deg,#4a2e10,#7a5030,#4a2e10)",
            "Argento Comune":"linear-gradient(160deg,#2a2a2a,#555,#2a2a2a)",
            "Argento Raro":"linear-gradient(160deg,#333,#666,#333)",
            "Oro Comune":"linear-gradient(160deg,#2a1f00,#5a4200,#2a1f00)",
            "Oro Raro":"linear-gradient(160deg,#3a2800,#6a5200,#3a2800)",
        }
        fb = fallbacks.get(tier_name,"linear-gradient(160deg,#111,#222,#111)")
        if is_trainer:
            # Background bianco per Trainer
            fb = "linear-gradient(160deg,#e8e8f0,#ffffff,#e8e8f0)"
        bg_style = "background:{};".format(fb)

    bg_div = '<div class="mbt-card-bg-image" style="{}"></div>'.format(bg_style)

    # Overlay gradient
    if is_trainer:
        overlay_grad = "linear-gradient(180deg,rgba(255,255,255,.0) 0%,rgba(255,255,255,.0) 50%,rgba(0,0,0,.75) 100%)"
    else:
        overlay_grad = "linear-gradient(180deg,rgba(0,0,0,.18) 0%,rgba(0,0,0,.05) 35%,rgba(0,0,0,.6) 72%,rgba(0,0,0,.88) 100%)"
    overlay_div = '<div class="mbt-card-overlay" style="background:{};"></div>'.format(overlay_grad)

    # Foto atleta
    if photo_path and os.path.exists(str(photo_path)):
        b64_img, mime_img = _load_image_b64_cached(str(photo_path))
        if b64_img:
            photo_cls = "mbt-card-photo-trainer" if is_trainer else "mbt-card-photo"
            foto_html = '<img class="{}" src="data:{};base64,{}" alt="" style="opacity:.92">'.format(photo_cls, mime_img, b64_img)
        else:
            foto_html = '<div class="mbt-card-photo-placeholder">{}</div>'.format(role_icon)
    else:
        foto_html = '<div class="mbt-card-photo-placeholder">{}</div>'.format(role_icon)

    # Animazioni overlay
    anim_overlay = ""
    if show_special_effects:
        if is_trainer:
            anim_overlay = _get_trainer_animation_overlay(card_id, trainer_color or "#ffffff")
        else:
            anim_overlay = _get_card_animation_overlay(tier_name, color, rarity, card_id)

    # Bordo/glow
    if is_trainer:
        tc = trainer_color or "#ffffff"
        border_style = "border:2px solid {c};box-shadow:0 0 16px {c}88,0 0 35px {c}44;border-radius:14px;".format(c=tc)
    else:
        border_style = _get_card_border_style(tier_name, color, rarity)

    # Hover glow
    hover_overlay = '<div class="mbt-card-hover-overlay" style="background:radial-gradient(ellipse at 50% 25%,{c}33 0%,transparent 65%);"></div>'.format(c=_border_color)

    # Firma su hover per carte rare
    hover_sign = ""
    if rarity >= 8 and not is_trainer:
        hover_sign = (
            '<div class="card-signature" style="position:absolute;bottom:72px;width:100%;'
            'text-align:center;font-family:cursive;font-size:.7rem;color:{c};opacity:0;'
            'transition:opacity .35s;z-index:15;text-shadow:0 0 10px {c}">✦ {n} ✦</div>'
            '<style>.mbt-card-wrap:hover .card-signature{{opacity:1!important;}}</style>'
        ).format(c=color,n=(cognome or nome).upper())

    tier_short = tier_name.split()[0] if len(tier_name.split())>1 else tier_name
    display_first = nome.upper()
    display_last  = (cognome or nome).upper()

    # Nome colore: per Trainer usiamo il colore del tier trainer
    name_color = trainer_color if is_trainer else color
    # Testo scuro per Trainer se sfondo bianco
    if is_trainer:
        name_color_dark = trainer_color  # manteniamo colore border per OVR

    # ── Stats block: 2 righe da 3 attributi ──
    stats_row1 = (
        '<div class="mbt-stats-row">'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{atk}</div><div class="mbt-stat-lbl">ATK</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{dif}</div><div class="mbt-stat-lbl">DIF</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{bat}</div><div class="mbt-stat-lbl">BAT</div></div>'
        '</div>'
    ).format(c=_border_color,atk=atk,dif=dif,bat=bat)
    stats_row2 = (
        '<div class="mbt-stats-row">'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{mur}</div><div class="mbt-stat-lbl">MUR</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{ric}</div><div class="mbt-stat-lbl">RIC</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{c}">{alz}</div><div class="mbt-stat-lbl">ALZ</div></div>'
        '</div>'
    ).format(c=_border_color,mur=mur,ric=ric,alz=alz)
    stats_block = '<div class="mbt-card-stats-6">{}{}</div>'.format(stats_row1,stats_row2)

    html = (
        '<div class="mbt-card-wrap" style="width:{width}">'
        '<div class="mbt-card" style="width:{width};{border}">'
        '{bg}{overlay}'
        '<div class="mbt-card-ovr" style="color:{nc};font-size:{fovr}">{ovr}</div>'
        '<div class="mbt-card-tier-label" style="color:{nc}">{tier_short}</div>'
        '{foto}'
        '<div class="mbt-card-name-block">'
        '<span class="mbt-card-firstname" style="color:{nc};font-size:{ffirst}">{first}</span>'
        '<span class="mbt-card-lastname" style="color:{nc};font-size:{fname}">{last}</span>'
        '</div>'
        '<div class="mbt-card-role" style="color:{nc}">{role_icon} {role}</div>'
        '{trainer_power}'
        '{stats}'
        '{anim}{hover}{sign}'
        '</div>'
        '</div>'
    ).format(
        width=width, border=border_style, bg=bg_div, overlay=overlay_div,
        nc=_border_color, fovr=font_ovr, ovr=ovr, tier_short=tier_short,
        foto=foto_html, ffirst=font_first, fname=font_name,
        first=display_first, last=display_last,
        role_icon=role_icon, role=role,
        trainer_power=trainer_power_html,
        stats=stats_block,
        anim=anim_overlay, hover=hover_overlay, sign=hover_sign,
    )
    return html


# ─── DATA HELPERS ─────────────────────────────────────────────────────────────

def load_rivals_data():
    if Path(RIVALS_FILE).exists():
        with open(RIVALS_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return empty_rivals_state()

def save_rivals_data(data):
    with open(RIVALS_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)

def load_cards_db():
    if Path(CARDS_DB_FILE).exists():
        with open(CARDS_DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"cards":[],"next_id":1}

def save_cards_db(db):
    with open(CARDS_DB_FILE,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,indent=2)

def empty_rivals_state():
    return {
        "player_level":1,"player_xp":0,"mbt_coins":500,"trofei_rivals":0,
        "collection":[],"active_team":[],"arena_unlocked":1,
        "battle_wins":0,"battle_losses":0,
        "special_moves_learned":[],"superpowers":{},"achievements":[],
        "equipped_trainer":None,  # instance_id della carta trainer schierata
    }



# ─── PACK OPENING ─────────────────────────────────────────────────────────────

def draw_cards_from_pack(pack_name, cards_db):
    pack_info = PACKS[pack_name]
    weights   = pack_info["weights"]
    tiers     = list(weights.keys())
    probs     = list(weights.values())
    total     = sum(probs)
    probs     = [p/total for p in probs]
    drawn     = []
    all_cards = cards_db.get("cards",[])
    for _ in range(6):
        chosen_tier = random.choices(tiers,weights=probs,k=1)[0]
        matching    = [c for c in all_cards if get_tier_by_ovr(c.get("overall",40))==chosen_tier and not _is_trainer(c)]
        if matching:
            card = random.choice(matching).copy()
        else:
            tier_info = CARD_TIERS.get(chosen_tier,CARD_TIERS["Bronzo Comune"])
            lo,hi = tier_info["ovr_range"]
            ovr = random.randint(lo,hi)
            card = {
                "id":"gen_{}".format(random.randint(100000,999999)),
                "nome":random.choice(["Marco","Luca","Andrea","Fabio","Simone","Giulio","Matteo","Riccardo"]),
                "cognome":random.choice(["Rossi","Bianchi","Ferrari","Conti","Esposito","Costa","Ricci","Serra"]),
                "overall":ovr,"ruolo":random.choice(list(ROLE_ICONS.keys())[:5]),
                "attacco":max(40,ovr-random.randint(0,15)),"difesa":max(40,ovr-random.randint(0,15)),
                "muro":max(40,ovr-random.randint(0,20)),"ricezione":max(40,ovr-random.randint(0,20)),
                "battuta":max(40,ovr-random.randint(0,18)),"alzata":max(40,ovr-random.randint(0,20)),
                "foto_path":"","tier":chosen_tier,"generated":True,
            }
        card["instance_id"] = "inst_{}".format(random.randint(1000000,9999999))
        drawn.append(card)
    return drawn


def render_pack_opening_animation(drawn_cards, pack_name):
    st.markdown("### 🎁 Apertura **{}** — Carte trovate:".format(pack_name))
    drawn_sorted = sorted(drawn_cards,key=lambda c: CARD_TIERS.get(get_tier_by_ovr(c.get("overall",40)),{}).get("rarity",0),reverse=True)
    cols = st.columns(6)
    for i,card in enumerate(drawn_sorted):
        tier       = get_tier_by_ovr(card.get("overall",40))
        rarity     = CARD_TIERS.get(tier,{}).get("rarity",0)
        tier_color = CARD_TIERS.get(tier,{}).get("color","#fff")
        with cols[i]:
            delay     = i*0.18
            anim_cls  = "pack-revealed-card-god" if rarity>=16 else "pack-revealed-card"
            if rarity>=12:
                lbl = '<div style="text-align:center;font-size:.58rem;color:{tc};margin-top:4px;font-weight:700;letter-spacing:2px;text-shadow:0 0 8px {tc}">⚡ {t} ⚡</div>'.format(tc=tier_color,t=tier)
            elif rarity>=8:
                lbl = '<div style="text-align:center;font-size:.55rem;color:{tc};margin-top:4px">✦ {t} ✦</div>'.format(tc=tier_color,t=tier)
            else:
                lbl = '<div style="text-align:center;font-size:.5rem;color:#888;margin-top:4px">{}</div>'.format(tier)
            st.markdown('<div class="{}" style="animation-delay:{}s">{}</div>{}'.format(
                anim_cls,delay,render_card_html(card,size="small"),lbl),unsafe_allow_html=True)


# ─── BATTLE ENGINE ────────────────────────────────────────────────────────────

def init_battle_state(player_cards, cpu_level=1, trainer_card=None):
    def make_fighter(card, is_cpu=False):
        ovr     = card.get("overall",40)
        base_hp = 80 + ovr*2
        if is_cpu: base_hp = int(base_hp*(0.9+cpu_level*0.1))
        return {"card":card,"hp":base_hp,"max_hp":base_hp,"stamina":100,"shield":0}

    player_fighters = [make_fighter(c) for c in player_cards[:3]]
    cpu_ovr_base    = 40 + cpu_level*4
    cpu_cards = []
    for _ in range(3):
        ovr = min(125,cpu_ovr_base+random.randint(-5,10))
        cpu_cards.append({
            "nome":random.choice(["Robot","CPU","AI","BOT"]),
            "overall":ovr,"ruolo":random.choice(list(ROLE_ICONS.keys())[:5]),
            "attacco":max(40,ovr-random.randint(0,10)),"difesa":max(40,ovr-random.randint(0,10)),
            "battuta":max(40,ovr-random.randint(0,10)),"muro":max(40,ovr-random.randint(0,10)),
            "ricezione":max(40,ovr-random.randint(0,10)),"alzata":max(40,ovr-random.randint(0,10)),
            "foto_path":"",
        })
    cpu_fighters = [make_fighter(c,is_cpu=True) for c in cpu_cards]

    # Trainer CPU casuale
    trainer_roles = ["TRAINER - Fisioterapista","TRAINER - Mental Coach","TRAINER - Scoutman"]
    cpu_trainer   = {
        "nome":"CPU","cognome":"Coach","overall":40+cpu_level*4,
        "ruolo":random.choice(trainer_roles),"attacco":40,"difesa":40,
        "battuta":40,"muro":40,"ricezione":40,"alzata":40,"foto_path":"",
        "id":"cpu_trainer",
    }

    return {
        "player_fighters":player_fighters,"cpu_fighters":cpu_fighters,
        "player_active_idx":0,"cpu_active_idx":0,
        "turn":0,"phase":"battle","log":[],
        "stamina_charges":0,"start_time":time.time(),"time_limit":300,
        "trainer_card":trainer_card,"cpu_trainer":cpu_trainer,
        "cpu_next_move":None,   # Scouting: rivelato se Vision/Scoutman
    }


def calculate_damage(attacker_card, defender_card, move_type="attack", superpowers=None, trainer_card=None):
    atk  = attacker_card.get("attacco",40)
    def_ = defender_card.get("difesa", 40)
    base = max(5,(atk-def_*0.6)*0.4+random.randint(3,12))
    if move_type=="special":
        base *= 1.8
        # Mental Coach: +30% danni super se HP critico
        if trainer_card and "Mental Coach" in trainer_card.get("ruolo",""):
            hp_ratio = attacker_card.get("_hp_ratio",1.0)
            if hp_ratio < 0.3:
                base *= 1.3
    elif move_type=="super":
        base *= 2.5
    if superpowers:
        ksl = superpowers.get("kill_shot",0)
        base *= (1+ksl*0.08)
    return max(5,int(base))


def cpu_choose_action(cpu_fighter, player_fighter, turn):
    hp_ratio = cpu_fighter["hp"]/max(1,cpu_fighter["max_hp"])
    if cpu_fighter["stamina"]>=50 and random.random()<0.3: return "special"
    if hp_ratio<0.3: return random.choice(["attack","attack","special","defend"])
    return random.choice(["attack","attack","attack","defend"])


def process_battle_action(battle_state, action, rivals_data):
    p_idx      = battle_state["player_active_idx"]
    c_idx      = battle_state["cpu_active_idx"]
    p_fighter  = battle_state["player_fighters"][p_idx]
    c_fighter  = battle_state["cpu_fighters"][c_idx]
    log        = battle_state["log"]
    superpowers= rivals_data.get("superpowers",{})
    trainer    = battle_state.get("trainer_card")
    player_name= p_fighter["card"].get("nome","Player")
    cpu_name   = c_fighter["card"].get("nome","CPU")

    # Calcola HP ratio per Mental Coach
    p_fighter["card"]["_hp_ratio"] = p_fighter["hp"]/max(1,p_fighter["max_hp"])

    # Stamina regen modificata da Fisioterapista
    stamina_use_mult = 1.0
    if trainer and "Fisioterapista" in trainer.get("ruolo",""):
        stamina_use_mult = 0.8

    if action=="attack":
        dmg = calculate_damage(p_fighter["card"],c_fighter["card"],"attack",superpowers,trainer)
        c_fighter["hp"] = max(0,c_fighter["hp"]-dmg)
        p_fighter["stamina"] = min(100,p_fighter["stamina"]+10)
        log.append("⚡ {} attacca → {} danni! (HP CPU: {})".format(player_name,dmg,c_fighter["hp"]))
        battle_state["stamina_charges"] += 1
    elif action=="special":
        cost = int(40*stamina_use_mult)
        if p_fighter["stamina"]>=cost:
            dmg = calculate_damage(p_fighter["card"],c_fighter["card"],"special",superpowers,trainer)
            c_fighter["hp"] = max(0,c_fighter["hp"]-dmg)
            p_fighter["stamina"] -= cost
            log.append("🔥 {} SUPER ATTACCO → {} danni!".format(player_name,dmg))
        else:
            log.append("⚠️ Stamina insufficiente (serve {})!".format(int(40*stamina_use_mult)))
    elif action=="defend":
        p_fighter["shield"] = 30
        p_fighter["stamina"] = min(100,p_fighter["stamina"]+int(20*stamina_use_mult))
        log.append("🛡️ {} si difende! Scudo attivato.".format(player_name))
    elif action=="final":
        if battle_state["stamina_charges"]>=10:
            dmg = calculate_damage(p_fighter["card"],c_fighter["card"],"super",superpowers,trainer)
            c_fighter["hp"] = max(0,c_fighter["hp"]-dmg)
            battle_state["stamina_charges"] = 0
            log.append("💥 MOSSA FINALE! {} → {} danni DEVASTANTI!".format(player_name,dmg))
        else:
            log.append("⚠️ Carica la Stamina per la Mossa Finale ({}/10)!".format(battle_state["stamina_charges"]))

    if c_fighter["hp"]<=0:
        next_cpu = c_idx+1
        if next_cpu<len(battle_state["cpu_fighters"]):
            battle_state["cpu_active_idx"] = next_cpu
            log.append("💀 {} eliminato! Prossimo avversario!".format(cpu_name))
        else:
            battle_state["phase"] = "win"
            log.append("🏆 HAI VINTO!")
            return

    if battle_state["phase"]=="battle":
        cpu_action = cpu_choose_action(c_fighter,p_fighter,battle_state["turn"])
        battle_state["cpu_next_move"] = cpu_action  # per Scoutman
        if cpu_action=="attack":
            cpu_dmg = calculate_damage(c_fighter["card"],p_fighter["card"],"attack")
            if p_fighter["shield"]>0:
                cpu_dmg = max(0,cpu_dmg-p_fighter["shield"])
                p_fighter["shield"] = 0
                log.append("🛡️ Scudo! {} attacca → {} danni dopo difesa".format(cpu_name,cpu_dmg))
            else:
                log.append("🤖 {} attacca → {} danni!".format(cpu_name,cpu_dmg))
            p_fighter["hp"] = max(0,p_fighter["hp"]-cpu_dmg)
        elif cpu_action=="special":
            cpu_dmg = calculate_damage(c_fighter["card"],p_fighter["card"],"special")
            log.append("💫 {} SUPER MOSSA → {} danni!".format(cpu_name,cpu_dmg))
            p_fighter["hp"] = max(0,p_fighter["hp"]-cpu_dmg)
        elif cpu_action=="defend":
            c_fighter["shield"] = 25
            log.append("🤖 {} si difende!".format(cpu_name))

    if p_fighter["hp"]<=0:
        next_p = p_idx+1
        if next_p<len(battle_state["player_fighters"]):
            battle_state["player_active_idx"] = next_p
            log.append("💔 {} KO! Prossima carta!".format(player_name))
        else:
            battle_state["phase"] = "lose"
            log.append("💀 HAI PERSO!")

    battle_state["turn"] += 1
    if len(log)>20: battle_state["log"] = log[-20:]


# ─── LEVEL UP / SYNC ──────────────────────────────────────────────────────────

def _check_level_up(rivals_data):
    level = rivals_data["player_level"]
    if level>=20: return
    xp        = rivals_data["player_xp"]
    xp_needed = XP_PER_LEVEL[level]
    if xp>=xp_needed:
        rivals_data["player_level"] += 1
        rivals_data["trofei_rivals"] += 10
        new_arena = next((a for a in ARENE if a["min_level"]<=rivals_data["player_level"]<=a["max_level"]),None)
        if new_arena:
            rivals_data["arena_unlocked"] = rivals_data["player_level"]


def _sync_ovr_from_tournament(state, cards_db):
    try:
        from data_manager import calcola_overall_fifa
        for atleta in state.get("atleti",[]):
            ovr = calcola_overall_fifa(atleta)
            for card in cards_db.get("cards",[]):
                if card.get("atleta_id")==atleta["id"]:
                    card["overall"] = ovr
                    s = atleta.get("stats",{})
                    card["attacco"]   = s.get("attacco",40)
                    card["difesa"]    = s.get("difesa",40)
                    card["muro"]      = s.get("muro",40)
                    card["ricezione"] = s.get("ricezione",40)
                    card["battuta"]   = s.get("battuta",40)
                    card["alzata"]    = s.get("alzata",40)
    except Exception:
        pass



# ─── MAIN RENDER ──────────────────────────────────────────────────────────────

def render_mbt_rivals(state):
    st.markdown(RIVALS_CSS, unsafe_allow_html=True)

    rivals_data = st.session_state.get("rivals_data")
    if rivals_data is None:
        rivals_data = load_rivals_data()
        st.session_state.rivals_data = rivals_data

    cards_db = st.session_state.get("cards_db")
    if cards_db is None:
        cards_db = load_cards_db()
        st.session_state.cards_db = cards_db

    # Assicura campo equipped_trainer
    rivals_data.setdefault("equipped_trainer",None)

    _sync_ovr_from_tournament(state, cards_db)

    level   = rivals_data["player_level"]
    xp      = rivals_data["player_xp"]
    coins   = rivals_data["mbt_coins"]
    xp_needed = XP_PER_LEVEL[min(level,len(XP_PER_LEVEL)-1)] if level<20 else 99999
    xp_pct    = min(100,int(xp/max(xp_needed,1)*100))
    current_arena = next((a for a in ARENE if a["min_level"]<=level<=a["max_level"]),ARENE[0])

    st.markdown("""
    <div style="background:linear-gradient(135deg,#080810,#10101e,#080810);
        border:2px solid #1e1e3a;border-radius:16px;padding:16px 24px;margin-bottom:20px;
        display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
            <div style="font-family:'Orbitron',sans-serif;font-size:1.6rem;font-weight:900;
                background:linear-gradient(90deg,#ffd700,#ffec4a,#ffd700);
                background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
                animation:goldShine 3s linear infinite">⚡ MBT RIVALS</div>
            <div style="font-size:.75rem;color:#666;letter-spacing:3px;margin-top:2px">CARD BATTLE SYSTEM v4.0</div>
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#ffd700">LV.{level}</div>
                <div style="font-size:.6rem;color:#888;letter-spacing:2px">LIVELLO</div>
                <div style="width:80px;height:6px;background:#1a1a2a;border-radius:3px;margin-top:4px;overflow:hidden">
                    <div style="width:{xp_pct}%;height:100%;background:linear-gradient(90deg,#ffd700,#ffec4a);border-radius:3px;transition:width .5s"></div>
                </div>
                <div style="font-size:.5rem;color:#666;margin-top:2px">{xp}/{xp_needed} XP</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#ffd700">🪙 {coins}</div>
                <div style="font-size:.6rem;color:#888;letter-spacing:2px">MBT COINS</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:{acol}">{aicon}</div>
                <div style="font-size:.6rem;color:{acol};letter-spacing:1px">{aname}</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#4ade80">{wins}W</div>
                <div style="font-size:.6rem;color:#888;letter-spacing:2px">VITTORIE</div>
            </div>
        </div>
    </div>
    """.format(
        level=level,xp_pct=xp_pct,xp=xp,xp_needed=xp_needed,coins=coins,
        acol=current_arena["color"],aicon=current_arena["icon"],aname=current_arena["name"],
        wins=rivals_data["battle_wins"]
    ), unsafe_allow_html=True)

    tabs = st.tabs(["⚔️ Battaglia","🃏 Collezione","🛒 Negozio","🏟️ Arene","💪 Poteri","⚙️ Admin"])
    with tabs[0]: _render_battle_tab(rivals_data, cards_db, state)
    with tabs[1]: _render_collection_tab(rivals_data, cards_db)
    with tabs[2]: _render_shop_tab(rivals_data, cards_db)
    with tabs[3]: _render_arenas_tab(rivals_data)
    with tabs[4]: _render_powers_tab(rivals_data)
    with tabs[5]: _render_admin_tab(state, cards_db, rivals_data)

    save_rivals_data(rivals_data)
    save_cards_db(cards_db)



# ─── BATTLE TAB ───────────────────────────────────────────────────────────────

def _get_trainer_card_for_battle(rivals_data, cards_db):
    """Restituisce la carta Trainer schierata (se presente e valida)."""
    tid = rivals_data.get("equipped_trainer")
    if not tid: return None
    all_cards = cards_db.get("cards",[])
    # cerca per id o instance_id
    for c in all_cards:
        if c.get("id")==tid or c.get("instance_id")==tid:
            if _is_trainer(c): return c
    return None


def _render_battle_tab(rivals_data, cards_db, state):
    st.markdown("## ⚔️ MBT RIVALS — Battaglia vs CPU")
    battle_state = st.session_state.get("battle_state")

    if battle_state is None:
        active_team_ids = rivals_data.get("active_team",[])
        all_cards       = cards_db.get("cards",[])
        # Risolve sia id che instance_id
        team_cards = [c for c in all_cards if c.get("id") in active_team_ids or c.get("instance_id") in active_team_ids]
        trainer_card = _get_trainer_card_for_battle(rivals_data, cards_db)

        # ── Squadra attiva ──
        st.markdown("### 🏆 La Tua Squadra Attiva")
        if not team_cards:
            st.warning("⚠️ Nessuna carta nella squadra attiva! Vai in **Collezione** per selezionare fino a 5 carte.")
            return

        cols = st.columns(min(5,len(team_cards)))
        for i,card in enumerate(team_cards[:5]):
            with cols[i]:
                st.markdown(render_card_html(card,size="small"),unsafe_allow_html=True)

        # ── Trainer schierata ──
        col_tr, col_arena_info = st.columns([1,2])
        with col_tr:
            if trainer_card:
                tp = TRAINER_POWERS.get(trainer_card.get("ruolo",""),{})
                st.markdown("**🧑‍🏫 Trainer schierato:**")
                st.markdown(render_card_html(trainer_card,size="small"),unsafe_allow_html=True)
                st.caption("✅ Potere attivo: **{}**".format(tp.get("label","")))
            else:
                st.markdown("""
                <div class="trainer-slot" style="text-align:center;padding:20px;border-radius:8px">
                    <div style="font-size:1.5rem">🧑‍🏫</div>
                    <div style="font-size:.65rem;color:#888;margin-top:4px">Nessun Trainer schierato</div>
                    <div style="font-size:.55rem;color:#555;margin-top:2px">Schiera un Trainer in Collezione</div>
                </div>
                """,unsafe_allow_html=True)

        with col_arena_info:
            level         = rivals_data["player_level"]
            current_arena = next((a for a in ARENE if a["min_level"]<=level<=a["max_level"]),ARENE[0])
            st.markdown("""
            <div class="arena-badge {css} arena-badge-anim" style="margin-bottom:12px">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-family:'Orbitron',sans-serif;font-weight:700;color:{color};font-size:.9rem">{name}</div>
                <div style="font-size:.65rem;color:#888;margin-top:4px">LV.{level} Arena</div>
            </div>
            <div style="background:#10101e;border:1px solid #1e1e3a;border-radius:10px;padding:16px;text-align:center;margin-top:8px">
                <div style="font-size:1.5rem">🤖</div>
                <div style="font-family:'Orbitron',sans-serif;color:#dc2626;font-weight:700">CPU LV.{level}</div>
                <div style="font-size:.65rem;color:#888">Difficoltà proporzionale al tuo livello</div>
            </div>
            """.format(css=current_arena["css"],icon=current_arena["icon"],
                       color=current_arena["color"],name=current_arena["name"],level=level),
                unsafe_allow_html=True)

        level = rivals_data["player_level"]
        st.markdown("**Ricompense vittoria:** 🪙 +{} Coins | ⭐ +{} XP | 🏆 +{} Trofei".format(
            50+level*10,30+level*5,2+level))

        st.markdown('<div class="battle-btn-atk" style="border-radius:8px;padding:2px">',unsafe_allow_html=True)
        if st.button("⚔️ INIZIA BATTAGLIA!",use_container_width=True,type="primary"):
            tc = _get_trainer_card_for_battle(rivals_data,cards_db)
            st.session_state.battle_state = init_battle_state(team_cards[:3],cpu_level=level,trainer_card=tc)
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    else:
        _render_active_battle(battle_state,rivals_data,cards_db)


def _render_active_battle(battle_state, rivals_data, cards_db):
    phase = battle_state["phase"]

    if phase=="win":
        level      = rivals_data["player_level"]
        xp_gain    = 30+level*5
        coins_gain = 50+level*10
        trofei_gain= 2+level
        rivals_data["player_xp"]      += xp_gain
        rivals_data["mbt_coins"]      += coins_gain
        rivals_data["trofei_rivals"]  += trofei_gain
        rivals_data["battle_wins"]    += 1
        _check_level_up(rivals_data)
        st.markdown("""
        <div style="text-align:center;padding:30px;background:linear-gradient(135deg,#001a00,#003300);
            border:3px solid #16a34a;border-radius:16px;animation:pulseGlow 1s infinite;color:#16a34a">
            <div style="font-size:3rem">🏆</div>
            <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:#4ade80">VITTORIA!</div>
            <div style="margin-top:10px;font-size:.8rem;color:#888">+{xp} XP | +{coins} Coins | +{trofei} Trofei</div>
        </div>
        """.format(xp=xp_gain,coins=coins_gain,trofei=trofei_gain),unsafe_allow_html=True)
        if st.button("🔄 Nuova Partita",use_container_width=True):
            st.session_state.battle_state = None
            st.rerun()
        return

    if phase=="lose":
        rivals_data["battle_losses"] += 1
        rivals_data["player_xp"]    += 10
        rivals_data["mbt_coins"]    += 20
        _check_level_up(rivals_data)
        st.markdown("""
        <div style="text-align:center;padding:30px;background:linear-gradient(135deg,#1a0000,#330000);
            border:3px solid #dc2626;border-radius:16px">
            <div style="font-size:3rem">💀</div>
            <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:#ef4444">SCONFITTA</div>
            <div style="margin-top:10px;font-size:.8rem;color:#888">+10 XP | +20 Coins per aver combattuto</div>
        </div>
        """,unsafe_allow_html=True)
        if st.button("🔄 Riprova",use_container_width=True):
            st.session_state.battle_state = None
            st.rerun()
        return

    elapsed   = time.time()-battle_state["start_time"]
    remaining = max(0,battle_state["time_limit"]-elapsed)
    if remaining<=0:
        battle_state["phase"] = "lose"
        st.rerun()

    p_idx     = battle_state["player_active_idx"]
    c_idx     = battle_state["cpu_active_idx"]
    p_fighter = battle_state["player_fighters"][p_idx]
    c_fighter = battle_state["cpu_fighters"][c_idx]
    trainer   = battle_state.get("trainer_card")
    cpu_train = battle_state.get("cpu_trainer")
    min_r     = int(remaining//60)
    sec_r     = int(remaining%60)

    # ── Scoutman vision ──
    scout_active = trainer and "Scoutman" in trainer.get("ruolo","")
    superpowers  = rivals_data.get("superpowers",{})
    vision_active= superpowers.get("vision",0)>=3

    # ── Campo da gioco Beach Volley ──────────────────────────────────────────
    st.markdown("### 🏐 Campo da Gioco")

    st.markdown("""
    <div class="battle-field-outer">
      <!-- Sfondo cielo/luci -->
      <div style="background:linear-gradient(180deg,#03070a 0%,#061520 100%);border-radius:12px;padding:10px;position:relative">

        <!-- Luci ambiente -->
        <div style="position:absolute;top:0;left:10%;width:80%;height:3px;
          background:linear-gradient(90deg,transparent,rgba(255,200,50,.35),transparent);border-radius:0 0 50% 50%;"></div>

        <!-- CAMPO SABBIA BEACH VOLLEY -->
        <div class="beach-court" style="min-height:300px;padding:8px;position:relative;border-radius:10px">

          <!-- Linee campo -->
          <div class="court-line" style="top:0;left:0;right:0;height:3px;background:rgba(255,255,255,.5)"></div>
          <div class="court-line" style="bottom:0;left:0;right:0;height:3px;background:rgba(255,255,255,.5)"></div>
          <div class="court-line" style="top:0;bottom:0;left:0;width:3px;background:rgba(255,255,255,.5)"></div>
          <div class="court-line" style="top:0;bottom:0;right:0;width:3px;background:rgba(255,255,255,.5)"></div>
          <div class="court-line" style="top:0;bottom:0;left:49.5%;width:1px;background:rgba(255,255,255,.3)"></div>

          <!-- RETE -->
          <div style="position:absolute;top:0;bottom:0;left:48.5%;width:3%;z-index:5;display:flex;flex-direction:column;align-items:center;justify-content:stretch">
            <div style="width:4px;height:100%;background:linear-gradient(180deg,#999,#666 40%,#999);border-radius:2px;animation:netWave 3s ease-in-out infinite;position:relative">
              <!-- Maglie rete -->
              <div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 8px,rgba(255,255,255,.3) 8px,rgba(255,255,255,.3) 9px),repeating-linear-gradient(90deg,transparent,transparent 3px,rgba(255,255,255,.2) 3px,rgba(255,255,255,.2) 4px)"></div>
            </div>
          </div>
          <!-- Pallina decorativa sulla rete -->
          <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);z-index:10;font-size:1.1rem;animation:ballBounce 2s ease-in-out infinite">🏐</div>

        </div><!-- /beach-court -->
      </div><!-- /sfondo -->
    </div><!-- /outer -->
    """,unsafe_allow_html=True)

    # ── Layout due colonne: CPU | Player ──
    col_cpu, col_net_sep, col_player = st.columns([5,1,5])

    # ===== METÀ CPU =====
    with col_cpu:
        st.markdown("""
        <div style="text-align:center;font-family:'Orbitron',sans-serif;font-size:.7rem;
          color:#dc2626;letter-spacing:2px;margin-bottom:6px;font-weight:700">🤖 CPU</div>
        """,unsafe_allow_html=True)

        # Carte CPU in campo
        cpu_cols = st.columns(3)
        for i,cf in enumerate(battle_state["cpu_fighters"]):
            with cpu_cols[i]:
                is_active = (i==c_idx)
                is_dead   = cf["hp"]<=0
                border    = "2px solid #dc2626" if is_active else "1px dashed #333"
                opacity   = "0.3" if is_dead else ("1.0" if is_active else "0.65")
                st.markdown('<div style="opacity:{};border:{};border-radius:8px;padding:2px;background:{};transition:all .3s">'.format(
                    opacity,border,"rgba(220,38,38,.05)" if is_active else "transparent"),unsafe_allow_html=True)
                st.markdown(render_card_html(cf["card"],size="small",show_special_effects=False),unsafe_allow_html=True)
                # Mini HP bar CPU
                hp_pct = int(cf["hp"]/max(1,cf["max_hp"])*100)
                clr = "#dc2626" if hp_pct<30 else "#16a34a"
                st.markdown('<div style="height:4px;background:#1a1a2a;border-radius:2px;overflow:hidden;margin-top:2px"><div style="width:{}%;height:100%;background:{};border-radius:2px;transition:width .5s"></div></div>'.format(hp_pct,clr),unsafe_allow_html=True)
                st.markdown('</div>',unsafe_allow_html=True)

        # Slot Trainer CPU
        st.markdown("""
        <div style="margin-top:8px;text-align:center">
            <div style="font-size:.55rem;color:#555;letter-spacing:1px;margin-bottom:4px">TRAINER CPU</div>
        </div>
        """,unsafe_allow_html=True)
        if cpu_train:
            st.markdown(render_card_html(cpu_train,size="small",show_special_effects=False),unsafe_allow_html=True)

    # ===== SEPARATORE rete verticale =====
    with col_net_sep:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;min-height:200px">
            <div style="width:4px;min-height:200px;background:linear-gradient(180deg,#555,#999 50%,#555);border-radius:2px;position:relative">
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:1.2rem">🏐</div>
            </div>
        </div>
        """,unsafe_allow_html=True)

    # ===== METÀ PLAYER =====
    with col_player:
        st.markdown("""
        <div style="text-align:center;font-family:'Orbitron',sans-serif;font-size:.7rem;
          color:#4ade80;letter-spacing:2px;margin-bottom:6px;font-weight:700">⚡ PLAYER</div>
        """,unsafe_allow_html=True)

        player_cols = st.columns(3)
        for i,pf in enumerate(battle_state["player_fighters"]):
            with player_cols[i]:
                is_active = (i==p_idx)
                is_dead   = pf["hp"]<=0
                border    = "2px solid #4ade80" if is_active else "1px dashed #333"
                opacity   = "0.3" if is_dead else "1.0"
                st.markdown('<div style="opacity:{};border:{};border-radius:8px;padding:2px;background:{};transition:all .3s;animation:{}">'.format(
                    opacity,border,"rgba(74,222,128,.05)" if is_active else "transparent",
                    "floatCard 2.5s ease-in-out infinite" if is_active else "none"),unsafe_allow_html=True)
                st.markdown(render_card_html(pf["card"],size="small",show_special_effects=is_active),unsafe_allow_html=True)
                hp_pct = int(pf["hp"]/max(1,pf["max_hp"])*100)
                clr = "#dc2626" if hp_pct<30 else "#4ade80"
                st.markdown('<div style="height:4px;background:#1a1a2a;border-radius:2px;overflow:hidden;margin-top:2px"><div style="width:{}%;height:100%;background:{};border-radius:2px;transition:width .5s"></div></div>'.format(hp_pct,clr),unsafe_allow_html=True)
                st.markdown('</div>',unsafe_allow_html=True)

        # Slot Trainer Player (fuori dal campo, sotto)
        st.markdown("""
        <div style="margin-top:8px;text-align:center">
            <div style="font-size:.55rem;color:#888;letter-spacing:1px;margin-bottom:4px">TRAINER SCHIERATO</div>
        </div>
        """,unsafe_allow_html=True)
        if trainer:
            st.markdown(render_card_html(trainer,size="small",show_special_effects=True),unsafe_allow_html=True)
            tp = TRAINER_POWERS.get(trainer.get("ruolo",""),{})
            st.markdown('<div style="font-size:.55rem;color:{c};text-align:center;margin-top:2px">✅ {lbl}</div>'.format(
                c=tp.get("color","#888"),lbl=tp.get("label","")),unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="trainer-slot" style="padding:10px;text-align:center">
                <div style="font-size:1.2rem">🧑‍🏫</div>
                <div style="font-size:.5rem;color:#555">Nessun Trainer</div>
            </div>
            """,unsafe_allow_html=True)

    # ── TABELLONE DIVISO ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Tabellone di Gioco")
    tb_col_p, tb_col_mid, tb_col_c = st.columns([5,2,5])

    with tb_col_p:
        hp_pct  = int(p_fighter["hp"]/max(1,p_fighter["max_hp"])*100)
        hp_cls  = "danger" if hp_pct<30 else ""
        sta_pct = int(p_fighter["stamina"])
        p_name  = p_fighter["card"].get("nome","Player")+" "+p_fighter["card"].get("cognome","")
        st.markdown("""
        <div class="scoreboard">
            <div style="font-family:'Orbitron',sans-serif;font-size:.75rem;color:#4ade80;font-weight:700">{name}</div>
            <div style="font-size:.55rem;color:#888;margin-bottom:6px">OVR {ovr}</div>
            <div style="font-size:.6rem;color:#888;margin-bottom:2px;text-align:left">❤️ VITA</div>
            <div class="hp-bar-container">
                <div class="hp-bar-fill {hcls}" style="width:{hp}%"></div>
            </div>
            <div style="font-size:.6rem;color:#888;margin-top:3px;text-align:right">{hp_val}/{hp_max}</div>
            <div style="font-size:.6rem;color:#888;margin-top:6px;margin-bottom:2px;text-align:left">⚡ STAMINA</div>
            <div style="height:8px;background:#1a1a2a;border-radius:4px;overflow:hidden">
                <div style="width:{sta}%;height:100%;background:linear-gradient(90deg,#ffd700,#ffec4a);border-radius:4px;transition:width .3s"></div>
            </div>
            <div style="font-size:.6rem;color:#888;margin-top:3px;text-align:right">{sta}%</div>
            <div style="font-size:.6rem;color:#888;margin-top:6px;text-align:left">🛡️ SCUDO: {shield} | ⚡ CARICA: {charges}/10</div>
        </div>
        """.format(
            name=p_name.strip(), ovr=p_fighter["card"].get("overall",40),
            hcls=hp_cls, hp=hp_pct, hp_val=p_fighter["hp"], hp_max=p_fighter["max_hp"],
            sta=sta_pct, shield=p_fighter.get("shield",0), charges=battle_state["stamina_charges"]
        ),unsafe_allow_html=True)

    with tb_col_mid:
        st.markdown("""
        <div class="scoreboard" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:140px">
            <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;font-weight:900;color:#dc2626">VS</div>
            <div style="font-size:.65rem;color:#888;margin-top:8px">⏱️ {:02d}:{:02d}</div>
            <div style="font-size:.65rem;color:#ffd700;margin-top:4px">Turno {}</div>
        </div>
        """.format(min_r,sec_r,battle_state["turn"]),unsafe_allow_html=True)

    with tb_col_c:
        chp_pct = int(c_fighter["hp"]/max(1,c_fighter["max_hp"])*100)
        c_name  = c_fighter["card"].get("nome","CPU")
        st.markdown("""
        <div class="scoreboard">
            <div style="font-family:'Orbitron',sans-serif;font-size:.75rem;color:#ef4444;font-weight:700">🤖 {name}</div>
            <div style="font-size:.55rem;color:#888;margin-bottom:6px">OVR {ovr}</div>
            <div style="font-size:.6rem;color:#888;margin-bottom:2px;text-align:left">❤️ VITA</div>
            <div class="hp-bar-container">
                <div style="width:{hp}%;height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:5px;transition:width .5s"></div>
            </div>
            <div style="font-size:.6rem;color:#888;margin-top:3px;text-align:right">{hp_val}/{hp_max}</div>
            <div style="font-size:.6rem;color:#888;margin-top:6px;text-align:left">⚡ STAMINA</div>
            <div style="height:8px;background:#1a1a2a;border-radius:4px;overflow:hidden;margin-top:2px">
                <div style="width:{csta}%;height:100%;background:linear-gradient(90deg,#dc2626,#ff6666);border-radius:4px"></div>
            </div>
            {next_move_html}
        </div>
        """.format(
            name=c_name, ovr=c_fighter["card"].get("overall",40),
            hp=chp_pct, hp_val=c_fighter["hp"], hp_max=c_fighter["max_hp"],
            csta=int(c_fighter["stamina"]),
            next_move_html='<div style="font-size:.6rem;color:#a855f7;margin-top:6px">🔭 PROSSIMA MOSSA: <b>{}</b></div>'.format(
                battle_state.get("cpu_next_move","?").upper()) if (scout_active or vision_active) and battle_state.get("cpu_next_move") else ""
        ),unsafe_allow_html=True)

    # ── Azioni ──
    st.markdown("#### 🎮 Scegli la tua mossa:")
    st.markdown('<div style="display:flex;gap:8px;flex-wrap:wrap">',unsafe_allow_html=True)
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        st.markdown('<div class="battle-btn-atk" style="border-radius:8px">',unsafe_allow_html=True)
        if st.button("⚡ ATTACCO",key="ba_atk",use_container_width=True):
            process_battle_action(battle_state,"attack",rivals_data); st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    with col2:
        can_sp = p_fighter["stamina"]>=int(40*(0.8 if trainer and "Fisioterapista" in trainer.get("ruolo","") else 1.0))
        st.markdown('<div class="battle-btn-sp" style="border-radius:8px">',unsafe_allow_html=True)
        if st.button("🔥 SUPER {}".format("✓" if can_sp else "✗"),key="ba_sp",use_container_width=True,disabled=not can_sp):
            process_battle_action(battle_state,"special",rivals_data); st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="battle-btn-def" style="border-radius:8px">',unsafe_allow_html=True)
        if st.button("🛡️ DIFENDI",key="ba_def",use_container_width=True):
            process_battle_action(battle_state,"defend",rivals_data); st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    with col4:
        can_fin = battle_state["stamina_charges"]>=10
        st.markdown('<div class="battle-btn-fin" style="border-radius:8px">',unsafe_allow_html=True)
        if st.button("💥 FINALE {}/10".format(battle_state["stamina_charges"]),key="ba_fin",use_container_width=True,disabled=not can_fin):
            process_battle_action(battle_state,"final",rivals_data); st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    # ── Log ──
    if battle_state["log"]:
        with st.expander("📋 Log Battaglia",expanded=True):
            log_html = '<div class="battle-log">'
            for entry in reversed(battle_state["log"][-8:]):
                log_html += '<div style="padding:2px 0;border-bottom:1px solid #1a1a2a;color:#ccc">{}</div>'.format(entry)
            log_html += "</div>"
            st.markdown(log_html,unsafe_allow_html=True)

    if st.button("🏳️ Abbandona Partita",key="ba_quit"):
        rivals_data["battle_losses"] += 1
        st.session_state.battle_state = None
        st.rerun()



# ─── COLLECTION TAB ───────────────────────────────────────────────────────────

def _render_collection_tab(rivals_data, cards_db):
    st.markdown("## 🃏 La Mia Collezione")
    all_cards   = cards_db.get("cards",[])
    owned_ids   = rivals_data.get("collection",[])
    active_team = rivals_data.get("active_team",[])
    equipped_trainer_id = rivals_data.get("equipped_trainer")

    if not owned_ids and all_cards:
        st.info("💡 La tua collezione cresce acquistando pacchetti! Anteprima di tutte le carte disponibili.")
        owned_cards = all_cards
    else:
        owned_cards = [c for c in all_cards if c.get("id") in owned_ids or c.get("instance_id") in owned_ids]

    if not owned_cards:
        st.warning("📦 Nessuna carta! Vai nel **Negozio** per acquistare pacchetti.")
        return

    # ── Tab interni ──────────────────────────────────────────────────────────
    sub_tabs = st.tabs(["⚽ Squadra Attiva","🃏 Le Mie Carte","🧑‍🏫 Trainer"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: SQUADRA ATTIVA
    # ══════════════════════════════════════════════════════════════════════════
    with sub_tabs[0]:
        st.markdown("### 👥 Squadra Attiva (max 5 carte)")
        st.caption("Seleziona le carte combattenti da usare in battaglia")

        non_trainer_cards = [c for c in owned_cards if not _is_trainer(c)]

        if not active_team:
            st.info("Nessuna carta in squadra. Seleziona le carte qui sotto.")
        else:
            team_cards = [c for c in all_cards if c.get("id") in active_team or c.get("instance_id") in active_team]
            slot_cols  = st.columns(5)
            for si in range(5):
                with slot_cols[si]:
                    if si < len(team_cards):
                        c     = team_cards[si]
                        cid   = c.get("id","") or c.get("instance_id","")
                        st.markdown(render_card_html(c,size="small"),unsafe_allow_html=True)
                        if st.button("❌",key="rm_team_s_{}_{}".format(si,cid[:6]),help="Rimuovi",use_container_width=True):
                            if cid in active_team: active_team.remove(cid)
                            rivals_data["active_team"] = active_team
                            st.rerun()
                    else:
                        st.markdown("""
                        <div style="width:105px;height:160px;border:2px dashed #333;border-radius:8px;
                          display:flex;align-items:center;justify-content:center;color:#444;font-size:.65rem">
                          SLOT VUOTO
                        </div>
                        """,unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Seleziona carte da aggiungere:**")

        # Paginazione lazy loading
        pg_key   = "coll_active_pg"
        pg       = st.session_state.get(pg_key,0)
        per_page = CARDS_PER_PAGE
        start    = pg*per_page
        end      = start+per_page
        page_cards = non_trainer_cards[start:end]
        total_pages = max(1,(len(non_trainer_cards)+per_page-1)//per_page)

        if total_pages>1:
            pcol1,pcol2,pcol3 = st.columns([1,3,1])
            with pcol1:
                if pg>0 and st.button("◀ Prec",key="coll_act_prev"):
                    st.session_state[pg_key] = pg-1; st.rerun()
            with pcol2:
                st.caption("Pagina {}/{} ({} carte totali)".format(pg+1,total_pages,len(non_trainer_cards)))
            with pcol3:
                if pg<total_pages-1 and st.button("Succ ▶",key="coll_act_next"):
                    st.session_state[pg_key] = pg+1; st.rerun()

        cols_per_row = 5
        for i in range(0,len(page_cards),cols_per_row):
            chunk = page_cards[i:i+cols_per_row]
            rcols = st.columns(cols_per_row)
            for j,card in enumerate(chunk):
                with rcols[j]:
                    cid      = card.get("id","") or card.get("instance_id","")
                    is_active= cid in active_team
                    st.markdown(render_card_html(card,size="small"),unsafe_allow_html=True)
                    if is_active:
                        if st.button("✅ IN SQUADRA",key="rm_act_{}_{}".format(i+j,cid[:6]),use_container_width=True):
                            if cid in active_team: active_team.remove(cid)
                            rivals_data["active_team"] = active_team; st.rerun()
                    else:
                        if st.button("➕ Aggiungi",key="add_act_{}_{}".format(i+j,cid[:6]),
                                     disabled=len(active_team)>=5,use_container_width=True):
                            active_team.append(cid)
                            rivals_data["active_team"] = active_team; st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: TUTTE LE CARTE (lazy loading + paginazione)
    # ══════════════════════════════════════════════════════════════════════════
    with sub_tabs[1]:
        st.markdown("### 🗂️ Tutte le Carte")

        col_filter, col_sort = st.columns(2)
        with col_filter:
            tier_filter = st.selectbox("🔍 Filtra Rarità",["Tutte"]+list(CARD_TIERS.keys()),key="coll2_tf")
        with col_sort:
            sort_opt = st.selectbox("↕️ Ordina per",["OVR ↓","OVR ↑","Nome A-Z"],key="coll2_sort")

        filtered = [c for c in owned_cards if not _is_trainer(c)]
        if tier_filter!="Tutte":
            filtered = [c for c in filtered if get_tier_by_ovr(c.get("overall",40))==tier_filter]

        if sort_opt=="OVR ↓": filtered.sort(key=lambda c:c.get("overall",40),reverse=True)
        elif sort_opt=="OVR ↑": filtered.sort(key=lambda c:c.get("overall",40))
        else: filtered.sort(key=lambda c:(c.get("cognome","") or c.get("nome","")))

        st.caption("📊 Totale collezione: {} carte | Mostrate: {}".format(len(owned_cards),len(filtered)))

        # Paginazione
        pg2_key  = "coll2_pg"
        pg2      = st.session_state.get(pg2_key,0)
        per_page = CARDS_PER_PAGE
        start2   = pg2*per_page
        end2     = start2+per_page
        page2_cards  = filtered[start2:end2]
        total_pages2 = max(1,(len(filtered)+per_page-1)//per_page)

        if total_pages2>1:
            pc1,pc2,pc3 = st.columns([1,3,1])
            with pc1:
                if pg2>0 and st.button("◀",key="c2_prev"): st.session_state[pg2_key]=pg2-1; st.rerun()
            with pc2:
                st.caption("Pagina {}/{} — carte {}-{} di {}".format(
                    pg2+1,total_pages2,start2+1,min(end2,len(filtered)),len(filtered)))
            with pc3:
                if pg2<total_pages2-1 and st.button("▶",key="c2_next"): st.session_state[pg2_key]=pg2+1; st.rerun()

        # Raggruppa per tier solo le carte della pagina corrente
        rarity_groups = {}
        for card in page2_cards:
            tier = get_tier_by_ovr(card.get("overall",40))
            rarity_groups.setdefault(tier,[]).append(card)

        for tier_name in reversed(list(CARD_TIERS.keys())):
            if tier_name not in rarity_groups: continue
            tier_cards = rarity_groups[tier_name]
            tier_info  = CARD_TIERS[tier_name]
            with st.expander("{} ({} carte)".format(tier_name,len(tier_cards)),
                             expanded=tier_info["rarity"]>=12):
                for i in range(0,len(tier_cards),5):
                    chunk = tier_cards[i:i+5]
                    rcols = st.columns(5)
                    for j,card in enumerate(chunk):
                        with rcols[j]:
                            st.markdown(render_card_html(card,size="small"),unsafe_allow_html=True)
                            st.caption("OVR {} | {}".format(card.get("overall",40),card.get("ruolo","")[:10]))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: TRAINER — Schieramento
    # ══════════════════════════════════════════════════════════════════════════
    with sub_tabs[2]:
        st.markdown("### 🧑‍🏫 Carta Trainer")
        st.caption("Schiera una carta Trainer per attivare il suo potere speciale durante la battaglia. Solo una alla volta.")

        trainer_cards = [c for c in owned_cards if _is_trainer(c)]

        if not trainer_cards:
            st.warning("Nessuna carta Trainer in collezione! Creane una nella sezione **Admin → Crea Carta** selezionando un ruolo TRAINER.")
            st.info("**Come funzionano i Trainer:**\n"
                    "- 💊 **Fisioterapista** — Riduce consumo Stamina del 20%\n"
                    "- 🧠 **Mental Coach** — Super attacchi +30% danno quando HP < 30%\n"
                    "- 🔭 **Scoutman** — Rivela la prossima mossa CPU")
        else:
            # Card Trainer schierata attualmente
            if equipped_trainer_id:
                eq_card = next((c for c in trainer_cards if c.get("id")==equipped_trainer_id or c.get("instance_id")==equipped_trainer_id),None)
                if eq_card:
                    tp = TRAINER_POWERS.get(eq_card.get("ruolo",""),{})
                    st.success("✅ Trainer attivo: **{}** — {}".format(eq_card.get("cognome",eq_card.get("nome","")), tp.get("desc","")))
                    col_eq, col_remove = st.columns([2,1])
                    with col_eq:
                        st.markdown(render_card_html(eq_card,size="normal"),unsafe_allow_html=True)
                    with col_remove:
                        if st.button("🚫 Rimuovi Trainer",use_container_width=True):
                            rivals_data["equipped_trainer"] = None; st.rerun()
                else:
                    rivals_data["equipped_trainer"] = None
            else:
                st.info("Nessun Trainer schierato.")

            st.markdown("---")
            st.markdown("**Le tue carte Trainer:**")
            for i,card in enumerate(trainer_cards):
                cid = card.get("id","") or card.get("instance_id","")
                is_equipped = (cid==equipped_trainer_id)
                tp = TRAINER_POWERS.get(card.get("ruolo",""),{})
                col_c,col_i = st.columns([1,3])
                with col_c:
                    st.markdown(render_card_html(card,size="small"),unsafe_allow_html=True)
                with col_i:
                    st.markdown("""
                    <div style="padding:8px 0">
                        <div style="font-family:Orbitron,sans-serif;font-weight:700;color:{tc};font-size:.8rem">{nome} {cognome}</div>
                        <div style="font-size:.65rem;color:#888">OVR {ovr} · {role}</div>
                        <div style="font-size:.6rem;color:{tc};margin-top:4px;background:{bg};padding:4px 8px;border-radius:4px;border:1px solid {tc};display:inline-block">
                            {lbl}: {desc}
                        </div>
                    </div>
                    """.format(
                        tc=tp.get("color","#fff"),
                        nome=card.get("nome",""),cognome=card.get("cognome",""),
                        ovr=card.get("overall",40),role=card.get("ruolo",""),
                        bg=tp.get("bg","rgba(0,0,0,.5)"),
                        lbl=tp.get("label",""),desc=tp.get("desc","")
                    ),unsafe_allow_html=True)
                    if is_equipped:
                        st.success("✅ Attualmente schierato")
                    else:
                        if st.button("🧑‍🏫 Schiera questo Trainer",key="equip_trainer_{}_{}".format(i,cid[:6]),use_container_width=True):
                            rivals_data["equipped_trainer"] = cid; st.rerun()
                st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>",unsafe_allow_html=True)



# ─── SHOP TAB ─────────────────────────────────────────────────────────────────

def _render_shop_tab(rivals_data, cards_db):
    st.markdown("## 🛒 Negozio Pacchetti")
    coins = rivals_data.get("mbt_coins",0)
    st.markdown('<div style="text-align:right;margin-bottom:20px"><span style="font-family:\'Orbitron\',sans-serif;font-size:1.2rem;color:#ffd700;font-weight:700">🪙 {} MBT Coins</span></div>'.format(coins),unsafe_allow_html=True)

    pack_cols  = st.columns(3)
    pack_names = ["Base","Epico","Leggenda"]
    pack_emojis= {"Base":"🟫","Epico":"💜","Leggenda":"🔥"}
    pack_descs = {
        "Base":"Perfetto per iniziare. Carte Bronzo, Argento e raramente Oro.",
        "Epico":"Alta probabilità di Oro ed Eroi. Chance di Leggenda e TOTY!",
        "Leggenda":"Solo carte di alto livello. Garantisce almeno una Leggenda!",
    }
    for i,pack_name in enumerate(pack_names):
        pack_info = PACKS[pack_name]
        with pack_cols[i]:
            color      = pack_info["label_color"]
            can_afford = coins>=pack_info["price"]
            st.markdown("""
            <div class="pack-card {css}" style="width:100%;height:220px;border-radius:16px;
                position:relative;overflow:hidden;display:flex;flex-direction:column;
                align-items:center;justify-content:center;margin-bottom:8px">
                <div style="font-size:3rem;z-index:2">{emoji}</div>
                <div style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;
                    color:{color};z-index:2;letter-spacing:3px;text-transform:uppercase">{name}</div>
                <div style="font-size:.65rem;color:#888;z-index:2;text-align:center;padding:0 10px;margin-top:4px">{desc}</div>
                <div style="font-family:'Orbitron',sans-serif;font-size:1rem;font-weight:700;color:#ffd700;z-index:2;margin-top:8px">🪙 {price}</div>
            </div>
            """.format(css=pack_info["css_class"],emoji=pack_emojis[pack_name],
                       color=color,name=pack_name,desc=pack_descs[pack_name],price=pack_info["price"]),
                unsafe_allow_html=True)
            if st.button("🛒 Acquista {}".format(pack_name) if can_afford else "🔒 Coins insufficienti",
                         key="buy_pack_{}".format(pack_name),use_container_width=True,disabled=not can_afford):
                st.session_state["opening_pack"] = pack_name
                rivals_data["mbt_coins"] -= pack_info["price"]
                drawn = draw_cards_from_pack(pack_name,cards_db)
                st.session_state["drawn_cards"] = drawn
                for card in drawn:
                    cid = card.get("id",card.get("instance_id",""))
                    if cid: rivals_data["collection"].append(cid)
                st.rerun()

    if st.session_state.get("drawn_cards"):
        pack_name_opened = st.session_state.get("opening_pack","Base")
        drawn = st.session_state["drawn_cards"]
        st.markdown("---")
        max_rarity = max(CARD_TIERS.get(get_tier_by_ovr(c.get("overall",40)),{}).get("rarity",0) for c in drawn)
        if max_rarity>=12:
            st.markdown("""<div style="text-align:center;animation:screenShake .5s infinite;background:rgba(255,215,0,.1);border:2px solid #ffd700;border-radius:10px;padding:10px;margin-bottom:10px"><span style="font-family:'Orbitron',sans-serif;font-size:1rem;color:#ffd700;animation:goldShine 1s infinite">⚡💥 CARTA ICONA! 💥⚡</span></div>""",unsafe_allow_html=True)
        elif max_rarity>=8:
            st.markdown("""<div style="text-align:center;background:rgba(255,255,255,.05);border:2px solid #fff;border-radius:10px;padding:8px;margin-bottom:10px"><span style="font-family:'Orbitron',sans-serif;font-size:.9rem;color:#fff">✨ CARTA LEGGENDARIA O SUPERIORE! ✨</span></div>""",unsafe_allow_html=True)
        render_pack_opening_animation(drawn,pack_name_opened)
        cb1,cb2 = st.columns(2)
        with cb1:
            if st.button("✅ Tieni tutte e Continua",use_container_width=True,type="primary"):
                st.session_state["drawn_cards"] = None; st.session_state["opening_pack"] = None; st.rerun()
        with cb2:
            if st.button("🔄 Apri un altro pacchetto",use_container_width=True):
                st.session_state["drawn_cards"] = None; st.session_state["opening_pack"] = None; st.rerun()

    # ── Mosse Speciali ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Mosse Speciali")
    st.caption("Insegna mosse speciali alle tue carte spendendo MBT Coins")
    learned = rivals_data.get("special_moves_learned",[])
    move_cols = st.columns(3)
    for i,move in enumerate(SPECIAL_MOVES[:9]):
        with move_cols[i%3]:
            already = move["id"] in learned
            rt = "[{}]".format(move["role"]) if move.get("role") else "[Universale]"
            can_afford_move = coins>=move["cost_coins"]
            bc  = "#ffd700" if already else "#1e1e3a"
            nc  = "#ffd700" if already else "#ccc"
            plbl= "✅ Appresa" if already else "🪙 {} Coins".format(move["cost_coins"])
            st.markdown("""
            <div style="background:#10101e;border:1px solid {bc};border-radius:8px;padding:10px;margin-bottom:8px;min-height:100px">
                <div style="font-family:'Orbitron',sans-serif;font-size:.7rem;font-weight:700;color:{nc}">{name}</div>
                <div style="font-size:.55rem;color:#666;margin:4px 0">{rt}</div>
                <div style="font-size:.6rem;color:#888">{desc}</div>
                <div style="font-size:.6rem;color:#ffd700;margin-top:4px">{pl}</div>
            </div>
            """.format(bc=bc,nc=nc,name=move["name"],rt=rt,desc=move["desc"],pl=plbl),unsafe_allow_html=True)
            if not already:
                if st.button("Apprendi",key="learn_{}".format(move["id"]),disabled=not can_afford_move,use_container_width=True):
                    rivals_data["special_moves_learned"].append(move["id"])
                    rivals_data["mbt_coins"] -= move["cost_coins"]; st.rerun()


# ─── ARENAS TAB ───────────────────────────────────────────────────────────────

def _render_arenas_tab(rivals_data):
    st.markdown("## 🏟️ Sistema Arene")
    st.caption("Avanza di livello per sbloccare arene sempre più epiche!")
    level = rivals_data["player_level"]

    for arena in ARENE:
        is_unlocked = level>=arena["min_level"]
        is_current  = arena["min_level"]<=level<=arena["max_level"]
        col1,col2   = st.columns([1,3])
        with col1:
            op = "opacity:.35;filter:grayscale(80%)" if not is_unlocked else ""
            anim_cls = "arena-badge-anim" if is_current else ""
            st.markdown("""
            <div class="arena-badge {css} {anim}" style="{op}">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-family:'Orbitron',sans-serif;font-size:.65rem;font-weight:700;color:{color}">LV.{mn}-{mx}</div>
            </div>
            """.format(css=arena["css"] if is_unlocked else "arena-badge",
                       anim=anim_cls,op=op,
                       icon=arena["icon"] if is_unlocked else "🔒",
                       color=arena["color"] if is_unlocked else "#555",
                       mn=arena["min_level"],mx=arena["max_level"]),unsafe_allow_html=True)
        with col2:
            badge  = " 🔴 ATTUALE" if is_current else (" ✅ SBLOCCATA" if is_unlocked else " 🔒")
            extra  = '<div style="font-size:.65rem;color:#ffd700;margin-top:4px">⚡ Combatti qui per ricompense speciali!</div>' if is_current else ""
            # Preview animata se sbloccata e cliccata
            st.markdown("""
            <div style="padding:12px 0">
                <div style="font-family:'Orbitron',sans-serif;font-weight:700;color:{color};font-size:.9rem">{name}{badge}</div>
                <div style="font-size:.7rem;color:#666;margin-top:4px">Livelli {mn} – {mx}</div>
                {extra}
            </div>
            """.format(color=arena["color"] if is_unlocked else "#555",
                       name=arena["name"],badge=badge,
                       mn=arena["min_level"],mx=arena["max_level"],extra=extra),unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>",unsafe_allow_html=True)


# ─── POWERS TAB ───────────────────────────────────────────────────────────────

def _render_powers_tab(rivals_data):
    st.markdown("## 💪 Super Poteri")
    st.caption("Potenzia i tuoi super poteri spendendo MBT Coins")
    coins      = rivals_data.get("mbt_coins",0)
    superpowers= rivals_data.setdefault("superpowers",{})
    for power in SUPERPOWERS:
        cur  = superpowers.get(power["id"],0)
        mx   = power["max_level"]
        cost = power["cost_per_level"]
        col1,col2,col3 = st.columns([3,1,1])
        with col1:
            bars = "█"*cur+"░"*(mx-cur)
            st.markdown("""
            <div style="background:#10101e;border:1px solid #1e1e3a;border-radius:8px;padding:12px;margin-bottom:8px">
                <div style="font-family:'Orbitron',sans-serif;font-size:.8rem;font-weight:700;color:#ffd700">
                    {name} <span style="font-size:.65rem;color:#888">LV.{cur}/{mx}</span>
                </div>
                <div style="font-size:.65rem;color:#888;margin:4px 0">{desc}</div>
                <div style="font-size:1rem;color:#ffd700;letter-spacing:2px">{bars}</div>
            </div>
            """.format(name=power["name"],cur=cur,mx=mx,desc=power["desc"],bars=bars),unsafe_allow_html=True)
        with col2:
            if cur<mx: st.metric("Costo","🪙 {}".format(cost))
        with col3:
            if cur<mx:
                if st.button("⬆️",key="up_pow_{}".format(power["id"]),disabled=coins<cost,use_container_width=True,help="Potenzia"):
                    superpowers[power["id"]] = cur+1
                    rivals_data["mbt_coins"] -= cost; st.rerun()
            else:
                st.markdown('<div style="color:#ffd700;text-align:center;padding:20px 0">✅ MAX</div>',unsafe_allow_html=True)



# ─── ADMIN TAB ───────────────────────────────────────────────────────────────

def _render_admin_tab(state, cards_db, rivals_data):
    st.markdown("## ⚙️ Pannello Admin — Cards Creator")
    admin_tabs = st.tabs(["➕ Crea Carta","⚡ Aggiungi Carta Rapida","📋 Gestisci Carte","🎁 Gestisci Coins"])
    with admin_tabs[0]: _render_card_creator(state,cards_db,rivals_data)
    with admin_tabs[1]: _render_quick_add_card(state,cards_db,rivals_data)
    with admin_tabs[2]: _render_card_manager(cards_db)
    with admin_tabs[3]: _render_coins_manager(rivals_data)


def _save_new_card(cards_db, card_obj, rivals_data=None, add_to_collection=False):
    """Salva una nuova carta nel DB, opzionalmente aggiungendola alla collezione."""
    new_id = "card_{}_{}".format(cards_db["next_id"],random.randint(1000,9999))
    cards_db["next_id"] += 1
    card_obj["id"] = new_id
    if "created_at" not in card_obj:
        card_obj["created_at"] = datetime.now().isoformat()
    cards_db["cards"].append(card_obj)
    save_cards_db(cards_db)
    st.session_state.cards_db = cards_db
    if add_to_collection and rivals_data is not None:
        rivals_data["collection"].append(new_id)
    return new_id


def _render_card_creator(state, cards_db, rivals_data=None):
    st.markdown("### ✏️ Crea Nuova Carta — Editor Completo")
    col_form,col_preview = st.columns([2,1])

    with col_form:
        nome    = st.text_input("Nome",key="cc_nome")
        cognome = st.text_input("Cognome",key="cc_cognome")
        ruolo   = st.selectbox("Ruolo",ROLES,key="cc_ruolo")
        st.markdown("---")
        st.markdown("**Statistiche (0–125) — OVR calcolato automaticamente**")
        c1,c2 = st.columns(2)
        with c1:
            atk = st.slider("⚡ Attacco", 0,125,70,key="cc_atk")
            dif = st.slider("🛡️ Difesa",  0,125,68,key="cc_dif")
            ric = st.slider("🤲 Ricezione",0,125,65,key="cc_ric")
        with c2:
            bat = st.slider("🏐 Battuta", 0,125,67,key="cc_bat")
            mur = st.slider("🧱 Muro",    0,125,62,key="cc_mur")
            alz = st.slider("🎯 Alzata",  0,125,60,key="cc_alz")

        overall      = calcola_ovr_da_stats(atk,dif,ric,bat,mur,alz)
        tier_preview = get_tier_by_ovr(overall)
        tier_color   = CARD_TIERS.get(tier_preview,{}).get("color","#ffd700")

        # Colore trainer speciale
        if _is_trainer({"ruolo":ruolo}):
            tp = TRAINER_POWERS.get(ruolo,{})
            tier_color = tp.get("color",tier_color)

        st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:.9rem;color:{};margin-bottom:4px;font-weight:700">OVR: {} | Tier: {}</div>'.format(tier_color,overall,tier_preview),unsafe_allow_html=True)
        st.markdown("---")
        foto_file = st.file_uploader("📷 Upload Foto Atleta",type=["png","jpg","jpeg"],key="cc_foto")
        foto_path = ""
        if foto_file:
            os.makedirs(ASSETS_ICONS_DIR,exist_ok=True)
            ext = foto_file.name.rsplit(".",1)[-1].lower()
            foto_path = os.path.join(ASSETS_ICONS_DIR,"{}_{}_{}.{}".format(
                nome or "player",cognome or "card",random.randint(1000,9999),ext))
            with open(foto_path,"wb") as f: f.write(foto_file.read())
            st.success("📷 Foto salvata: {}".format(foto_path))

        atleti_nomi = ["-- Nessuno --"]+[a["nome"] for a in state.get("atleti",[])]
        sel_atleta  = st.selectbox("🔗 Collega a Atleta Torneo (opzionale)",atleti_nomi,key="cc_atleta")
        atleta_id_linked = None
        if sel_atleta!="-- Nessuno --":
            linked = next((a for a in state.get("atleti",[]) if a["nome"]==sel_atleta),None)
            if linked:
                atleta_id_linked = linked["id"]
                try:
                    from data_manager import calcola_overall_fifa
                    real_ovr = calcola_overall_fifa(linked)
                    st.info("📊 OVR reale dall'app torneo: **{}**".format(real_ovr))
                except Exception: pass

    with col_preview:
        st.markdown("#### 👁️ Anteprima Carta")
        preview_card = {
            "id":"preview","nome":nome or "NOME","cognome":cognome or "",
            "overall":overall,"ruolo":ruolo,
            "attacco":atk,"difesa":dif,"battuta":bat,"muro":mur,"ricezione":ric,"alzata":alz,
            "foto_path":foto_path,
        }
        st.markdown('<div class="creator-preview-wrap">{}</div>'.format(render_card_html(preview_card,size="large")),unsafe_allow_html=True)
        st.markdown('<div style="background:#10101e;border:1px solid {tc};border-radius:8px;padding:10px;text-align:center;margin-top:10px"><div style="font-family:Orbitron,sans-serif;font-size:.7rem;color:{tc};font-weight:700">{tier}</div><div style="font-size:.6rem;color:#888;margin-top:2px">OVR {ovr}</div></div>'.format(tc=tier_color,tier=tier_preview,ovr=overall),unsafe_allow_html=True)

    st.markdown("---")
    col_s1,col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 SALVA nel Database",use_container_width=True,type="primary"):
            if not nome:
                st.error("Inserisci il nome!")
            else:
                new_card = {
                    "nome":nome,"cognome":cognome,"overall":overall,"ruolo":ruolo,
                    "attacco":atk,"difesa":dif,"muro":mur,"ricezione":ric,"battuta":bat,"alzata":alz,
                    "foto_path":foto_path,"tier":tier_preview,"atleta_id":atleta_id_linked,
                }
                nid = _save_new_card(cards_db,new_card)
                st.success("✅ Carta **{} {}** (OVR {} · {}) salvata! ID: {}".format(nome,cognome,overall,tier_preview,nid))
                st.rerun()
    with col_s2:
        if st.button("💾 Salva e AGGIUNGI a Collezione",use_container_width=True):
            if not nome:
                st.error("Inserisci il nome!")
            else:
                new_card = {
                    "nome":nome,"cognome":cognome,"overall":overall,"ruolo":ruolo,
                    "attacco":atk,"difesa":dif,"muro":mur,"ricezione":ric,"battuta":bat,"alzata":alz,
                    "foto_path":foto_path,"tier":tier_preview,"atleta_id":atleta_id_linked,
                }
                nid = _save_new_card(cards_db,new_card,rivals_data,add_to_collection=True)
                st.success("✅ Carta **{} {}** salvata e aggiunta alla collezione!".format(nome,cognome))
                st.rerun()


def _render_quick_add_card(state, cards_db, rivals_data):
    """Aggiungi Carta Rapida: inserisci le stats e salva/aggiungi in 1 click senza compilare tutto il form."""
    st.markdown("### ⚡ Aggiungi Carta Rapida")
    st.caption("Inserisci velocemente le statistiche di una carta e aggiungila direttamente alla collezione.")

    q1,q2 = st.columns(2)
    with q1:
        q_nome    = st.text_input("Nome",key="qa_nome",placeholder="Es: Marco")
        q_cognome = st.text_input("Cognome",key="qa_cognome",placeholder="Es: Rossi")
        q_ruolo   = st.selectbox("Ruolo",ROLES,key="qa_ruolo")
    with q2:
        q_atk = st.number_input("ATK",0,125,70,key="qa_atk")
        q_dif = st.number_input("DIF",0,125,68,key="qa_dif")
        q_bat = st.number_input("BAT",0,125,67,key="qa_bat")
        q_mur = st.number_input("MUR",0,125,62,key="qa_mur")
        q_ric = st.number_input("RIC",0,125,65,key="qa_ric")
        q_alz = st.number_input("ALZ",0,125,60,key="qa_alz")

    q_ovr  = calcola_ovr_da_stats(int(q_atk),int(q_dif),int(q_ric),int(q_bat),int(q_mur),int(q_alz))
    q_tier = get_tier_by_ovr(q_ovr)
    tc     = CARD_TIERS.get(q_tier,{}).get("color","#ffd700")
    st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:.85rem;color:{};font-weight:700;margin:8px 0">OVR: {} | Tier: {}</div>'.format(tc,q_ovr,q_tier),unsafe_allow_html=True)

    # Anteprima compatta
    prev_card = {
        "id":"qa_prev","nome":q_nome or "?","cognome":q_cognome or "",
        "overall":q_ovr,"ruolo":q_ruolo,
        "attacco":int(q_atk),"difesa":int(q_dif),"battuta":int(q_bat),
        "muro":int(q_mur),"ricezione":int(q_ric),"alzata":int(q_alz),"foto_path":"",
    }
    cols_prev = st.columns([1,3])
    with cols_prev[0]:
        st.markdown(render_card_html(prev_card,size="small"),unsafe_allow_html=True)
    with cols_prev[1]:
        st.markdown("**ATK** {} | **DIF** {} | **BAT** {} | **MUR** {} | **RIC** {} | **ALZ** {}".format(
            int(q_atk),int(q_dif),int(q_bat),int(q_mur),int(q_ric),int(q_alz)))
        foto_file2 = st.file_uploader("📷 Foto (opzionale)",type=["png","jpg","jpeg"],key="qa_foto")
        q_foto_path = ""
        if foto_file2:
            os.makedirs(ASSETS_ICONS_DIR,exist_ok=True)
            ext = foto_file2.name.rsplit(".",1)[-1].lower()
            q_foto_path = os.path.join(ASSETS_ICONS_DIR,"{}_{}_{}.{}".format(
                q_nome or "quick",q_cognome or "card",random.randint(1000,9999),ext))
            with open(q_foto_path,"wb") as f: f.write(foto_file2.read())

    qa1,qa2 = st.columns(2)
    with qa1:
        if st.button("⚡ AGGIUNGI ALLA COLLEZIONE",use_container_width=True,type="primary"):
            if not q_nome:
                st.error("Inserisci il nome!")
            else:
                nc = {
                    "nome":q_nome,"cognome":q_cognome,"overall":q_ovr,"ruolo":q_ruolo,
                    "attacco":int(q_atk),"difesa":int(q_dif),"muro":int(q_mur),
                    "ricezione":int(q_ric),"battuta":int(q_bat),"alzata":int(q_alz),
                    "foto_path":q_foto_path,"tier":q_tier,"atleta_id":None,
                }
                _save_new_card(cards_db,nc,rivals_data,add_to_collection=True)
                st.success("✅ {} {} aggiunto alla collezione!".format(q_nome,q_cognome))
                st.rerun()
    with qa2:
        if st.button("💾 Solo Salva nel DB",use_container_width=True):
            if not q_nome:
                st.error("Inserisci il nome!")
            else:
                nc = {
                    "nome":q_nome,"cognome":q_cognome,"overall":q_ovr,"ruolo":q_ruolo,
                    "attacco":int(q_atk),"difesa":int(q_dif),"muro":int(q_mur),
                    "ricezione":int(q_ric),"battuta":int(q_bat),"alzata":int(q_alz),
                    "foto_path":q_foto_path,"tier":q_tier,"atleta_id":None,
                }
                _save_new_card(cards_db,nc)
                st.success("✅ {} {} salvato nel database!".format(q_nome,q_cognome))
                st.rerun()


def _render_card_manager(cards_db):
    st.markdown("### 📋 Carte nel Database")
    all_cards = cards_db.get("cards",[])
    if not all_cards:
        st.info("Nessuna carta. Creane una con il Card Creator!")
        return

    st.caption("Totale: {} carte".format(len(all_cards)))
    mf1,mf2 = st.columns(2)
    with mf1:
        filter_tier = st.selectbox("Filtra Tier",["Tutte"]+list(CARD_TIERS.keys()),key="mgr_filter")
    with mf2:
        filter_type = st.selectbox("Tipo",["Tutte","Solo Trainer","Solo Giocatori"],key="mgr_type")

    filtered = all_cards
    if filter_tier!="Tutte":
        filtered = [c for c in filtered if get_tier_by_ovr(c.get("overall",40))==filter_tier]
    if filter_type=="Solo Trainer":
        filtered = [c for c in filtered if _is_trainer(c)]
    elif filter_type=="Solo Giocatori":
        filtered = [c for c in filtered if not _is_trainer(c)]

    # Paginazione manager
    mg_key  = "mgr_pg"
    mg_pg   = st.session_state.get(mg_key,0)
    per_page= 15
    start   = mg_pg*per_page
    end     = start+per_page
    page_f  = filtered[start:end]
    total_pg= max(1,(len(filtered)+per_page-1)//per_page)

    if total_pg>1:
        pc1,pc2,pc3 = st.columns([1,3,1])
        with pc1:
            if mg_pg>0 and st.button("◀",key="mgr_prev"): st.session_state[mg_key]=mg_pg-1; st.rerun()
        with pc2:
            st.caption("Pagina {}/{} — {} carte totali".format(mg_pg+1,total_pg,len(filtered)))
        with pc3:
            if mg_pg<total_pg-1 and st.button("▶",key="mgr_next"): st.session_state[mg_key]=mg_pg+1; st.rerun()

    for i,card in enumerate(page_f):
        tier  = get_tier_by_ovr(card.get("overall",40))
        tc    = CARD_TIERS.get(tier,{}).get("color","#888")
        if _is_trainer(card):
            tp_info = TRAINER_POWERS.get(card.get("ruolo",""),{})
            tc      = tp_info.get("color",tc)
        col1,col2,col3 = st.columns([1,3,1])
        with col1:
            st.markdown(render_card_html(card,size="small",show_special_effects=False),unsafe_allow_html=True)
        with col2:
            atk = card.get("attacco",40); dif = card.get("difesa",40); bat = card.get("battuta",40)
            mur = card.get("muro",40);   ric = card.get("ricezione",40); alz = card.get("alzata",40)
            trainer_badge = ""
            if _is_trainer(card):
                tp_info = TRAINER_POWERS.get(card.get("ruolo",""),{})
                trainer_badge = '<span style="font-size:.55rem;background:{bg};color:{c};border:1px solid {c};border-radius:3px;padding:1px 5px;margin-left:4px">{lbl}</span>'.format(
                    bg=tp_info.get("bg","transparent"),c=tc,lbl=tp_info.get("label","TRAINER"))
            st.markdown("""
            <div style="padding:8px 0">
                <div style="font-family:Orbitron,sans-serif;font-weight:700;color:{tc}">{nome} {cog}{tbadge}</div>
                <div style="font-size:.7rem;color:#888">OVR {ovr} · {tier} · {ruolo}</div>
                <div style="font-size:.6rem;color:#666;margin-top:4px">ATK:{atk}|DIF:{dif}|BAT:{bat}|MUR:{mur}|RIC:{ric}|ALZ:{alz}</div>
            </div>
            """.format(tc=tc,nome=card.get("nome",""),cog=card.get("cognome",""),
                       tbadge=trainer_badge,ovr=card.get("overall",40),tier=tier,
                       ruolo=card.get("ruolo",""),atk=atk,dif=dif,bat=bat,mur=mur,ric=ric,alz=alz),
                unsafe_allow_html=True)
            with st.expander("✏️ Modifica Stats"):
                ec1,ec2 = st.columns(2)
                cid6 = card.get("id","x")[:6]
                with ec1:
                    n_atk = st.slider("ATK",0,125,int(atk),key="e_atk_{}_{}".format(i,cid6))
                    n_dif = st.slider("DEF",0,125,int(dif),key="e_dif_{}_{}".format(i,cid6))
                    n_ric = st.slider("RIC",0,125,int(ric),key="e_ric_{}_{}".format(i,cid6))
                with ec2:
                    n_bat = st.slider("BAT",0,125,int(bat),key="e_bat_{}_{}".format(i,cid6))
                    n_mur = st.slider("MUR",0,125,int(mur),key="e_mur_{}_{}".format(i,cid6))
                    n_alz = st.slider("ALZ",0,125,int(alz),key="e_alz_{}_{}".format(i,cid6))
                n_ovr = calcola_ovr_da_stats(n_atk,n_dif,n_ric,n_bat,n_mur,n_alz)
                st.caption("OVR: {} | Tier: {}".format(n_ovr,get_tier_by_ovr(n_ovr)))
                if st.button("💾 Salva",key="sv_card_{}_{}".format(i,cid6)):
                    card["attacco"]=n_atk;card["difesa"]=n_dif;card["ricezione"]=n_ric
                    card["battuta"]=n_bat;card["muro"]=n_mur;card["alzata"]=n_alz
                    card["overall"]=n_ovr;card["tier"]=get_tier_by_ovr(n_ovr)
                    save_cards_db(cards_db); st.session_state.cards_db=cards_db
                    st.success("✅ Aggiornato!"); st.rerun()
        with col3:
            if st.button("🗑️",key="del_{}_{}_{}".format(i,start,card.get("id","x")[:8]),help="Elimina"):
                cards_db["cards"]=[c for c in all_cards if c.get("id")!=card.get("id")]
                save_cards_db(cards_db); st.session_state.cards_db=cards_db; st.rerun()
        st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>",unsafe_allow_html=True)


def _render_coins_manager(rivals_data):
    st.markdown("### 🎁 Gestione Coins & XP")
    c1,c2 = st.columns(2)
    with c1:
        add_coins = st.number_input("Aggiungi MBT Coins",0,99999,500,key="adm_coins")
        if st.button("➕ Aggiungi Coins",key="adm_btn_c"):
            rivals_data["mbt_coins"] += add_coins
            st.success("✅ +{} coins! Totale: {}".format(add_coins,rivals_data["mbt_coins"]))
    with c2:
        add_xp = st.number_input("Aggiungi XP",0,99999,100,key="adm_xp")
        if st.button("➕ Aggiungi XP",key="adm_btn_x"):
            rivals_data["player_xp"] += add_xp
            _check_level_up(rivals_data)
            st.success("✅ +{} XP! Level: {}".format(add_xp,rivals_data["player_level"]))
    st.markdown("---")
    st.markdown("""
    **Stato attuale:**
    - MBT Coins: **{coins}**
    - XP: **{xp}** / Level: **{lv}**
    - Trofei: **{trofei}** | Vittorie: **{wins}**
    - Carte in collezione: **{ncards}**
    - Trainer schierato: **{trainer}**
    """.format(
        coins=rivals_data["mbt_coins"],xp=rivals_data["player_xp"],
        lv=rivals_data["player_level"],trofei=rivals_data["trofei_rivals"],
        wins=rivals_data["battle_wins"],
        ncards=len(rivals_data.get("collection",[])),
        trainer=rivals_data.get("equipped_trainer","Nessuno")
    ))
    if st.button("🔄 Reset Dati Rivals",key="adm_reset"):
        st.session_state.rivals_data = empty_rivals_state()
        st.session_state.rivals_data["mbt_coins"] = 1000
        save_rivals_data(st.session_state.rivals_data)
        st.success("✅ Dati resettati con 1000 Coins di partenza.")
        st.rerun()

