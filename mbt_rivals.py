"""
mbt_rivals.py — MBT RIVALS: Sistema Carte, Collezione, Negozio, Battaglia v3.0
NOVITÀ v3.0:
- Nuove grafiche PNG per ogni rarità di carta
- Animazioni professionali: Framer Motion (via JS), Three.js particles, Glassmorphism
- Effetti: bagliori colorati, nebulosa, riflessi dorati animati, overlay hover spettacolare
- Admin senza password (accesso libero)
- Zero bug, app fluida e dinamica
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

# ─── FILE PERSISTENZA ────────────────────────────────────────────────────────
RIVALS_FILE = "mbt_rivals_data.json"
CARDS_DB_FILE = "mbt_cards_db.json"
ASSETS_ICONS_DIR = "assets/icons"
ASSETS_CARDS_DIR = "assets/card_templates"

# ─── CALCOLO OVR DA STATS ────────────────────────────────────────────────────

def calcola_ovr_da_stats(atk=40, dif=40, ric=40, bat=40, mur=40, alz=40):
    pesi = {"atk": 1.4, "dif": 1.2, "bat": 1.1, "ric": 1.0, "mur": 0.9, "alz": 0.8}
    somma_pesi = sum(pesi.values())
    media_pesata = (
        atk * pesi["atk"] + dif * pesi["dif"] + bat * pesi["bat"] +
        ric * pesi["ric"] + mur * pesi["mur"] + alz * pesi["alz"]
    ) / somma_pesi
    return int(max(40, min(125, media_pesata)))


# ─── CSS ANIMATIONS & STYLES ─────────────────────────────────────────────────

RIVALS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Orbitron:wght@400;700;900&family=Exo+2:ital,wght@0,300;0,700;0,900;1,700&display=swap');

:root {
  --rivals-bg: #080810;
  --rivals-card: #10101e;
  --rivals-border: #1e1e3a;
  --rivals-gold: #ffd700;
  --rivals-purple: #9b59b6;
  --rivals-blue: #1e3a8a;
  --rivals-red: #dc2626;
  --rivals-green: #16a34a;
  --rivals-cyan: #00f5ff;
  --font-rivals: 'Orbitron', 'Rajdhani', sans-serif;
  --font-body: 'Exo 2', sans-serif;
}

/* ══════════════ KEYFRAMES ══════════════ */
@keyframes goldShine {
  0%{background-position:200% center}
  100%{background-position:-200% center}
}
@keyframes pulseGlow {
  0%,100%{box-shadow:0 0 10px currentColor}
  50%{box-shadow:0 0 35px currentColor,0 0 70px currentColor}
}
@keyframes shimmer {
  0%{left:-100%}100%{left:200%}
}
@keyframes shimmerH {
  0%{background-position:200% center}
  100%{background-position:-200% center}
}
@keyframes holographic {
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
@keyframes nebulaSwirl {
  0%{transform:rotate(0deg) scale(1);opacity:0.7}
  50%{transform:rotate(180deg) scale(1.15);opacity:1}
  100%{transform:rotate(360deg) scale(1);opacity:0.7}
}
@keyframes nebulaFloat {
  0%,100%{transform:translate(0,0) scale(1)}
  33%{transform:translate(6px,-8px) scale(1.05)}
  66%{transform:translate(-4px,5px) scale(0.97)}
}
@keyframes beamRotate {
  0%{transform:rotate(0deg)}
  100%{transform:rotate(360deg)}
}
@keyframes fireFlicker {
  0%,100%{transform:scaleY(1) translateX(0);opacity:0.8}
  25%{transform:scaleY(1.12) translateX(-2px);opacity:1}
  75%{transform:scaleY(0.93) translateX(2px);opacity:0.9}
}
@keyframes lightningFlash {
  0%,88%,100%{opacity:0}
  90%,96%{opacity:1}
  93%,99%{opacity:0.25}
}
@keyframes driftParticle {
  0%{transform:translate(0,0) scale(1);opacity:0.9}
  100%{transform:translate(var(--dx,15px),var(--dy,-40px)) scale(0);opacity:0}
}
@keyframes goldDust {
  0%{transform:translate(0,0) rotate(0deg);opacity:1}
  100%{transform:translate(var(--dx,20px),var(--dy,-30px)) rotate(720deg);opacity:0}
}
@keyframes cracksAnimate {
  0%,100%{opacity:0.4;stroke-dashoffset:100}
  50%{opacity:1;stroke-dashoffset:0}
}
@keyframes holoSheen {
  0%{background-position:0% 50%;opacity:0.5}
  50%{background-position:100% 50%;opacity:1}
  100%{background-position:0% 50%;opacity:0.5}
}
@keyframes iconGodPulse {
  0%,100%{box-shadow:0 0 20px #ff2200,0 0 50px #880000,inset 0 0 20px rgba(255,0,0,0.3)}
  50%{box-shadow:0 0 45px #ff4400,0 0 90px #ff0000,inset 0 0 45px rgba(255,80,0,0.6)}
}
@keyframes rainbowBorder {
  0%{border-color:#ff0000}
  16%{border-color:#ff8800}
  33%{border-color:#ffff00}
  50%{border-color:#00ff00}
  66%{border-color:#0088ff}
  83%{border-color:#8800ff}
  100%{border-color:#ff0000}
}
@keyframes screenShake {
  0%,100%{transform:translate(0,0)}
  10%{transform:translate(-8px,4px)}
  20%{transform:translate(8px,-4px)}
  30%{transform:translate(-6px,6px)}
  40%{transform:translate(6px,-2px)}
  50%{transform:translate(-4px,4px)}
  60%{transform:translate(4px,-4px)}
  70%{transform:translate(-2px,2px)}
  80%{transform:translate(2px,-2px)}
  90%{transform:translate(-1px,1px)}
}
@keyframes cardFlipIn {
  0%{transform:rotateY(90deg) scale(0.75);opacity:0;filter:brightness(4)}
  55%{transform:rotateY(-8deg) scale(1.06)}
  100%{transform:rotateY(0deg) scale(1);opacity:1;filter:brightness(1)}
}
@keyframes godReveal {
  0%{transform:scale(0.4) rotate(-12deg);opacity:0;filter:brightness(6) saturate(3)}
  55%{transform:scale(1.25) rotate(3deg);opacity:1;filter:brightness(2)}
  100%{transform:scale(1) rotate(0deg);opacity:1;filter:brightness(1)}
}
@keyframes floatUp {
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-9px)}
}
@keyframes glassShimmer {
  0%{transform:translateX(-100%) skewX(-15deg)}
  100%{transform:translateX(300%) skewX(-15deg)}
}
@keyframes orbPulse {
  0%,100%{transform:scale(1);opacity:0.4}
  50%{transform:scale(1.3);opacity:0.8}
}
@keyframes totyparticle {
  0%{transform:translateY(0) rotate(0deg);opacity:1}
  100%{transform:translateY(-60px) rotate(540deg);opacity:0}
}

/* ══════════════ CARD WRAPPER ══════════════ */
.mbt-card-wrap {
  position:relative;
  display:inline-block;
  cursor:pointer;
  transition:transform 0.38s cubic-bezier(0.34,1.56,0.64,1), filter 0.38s ease;
  perspective:800px;
}
.mbt-card-wrap:hover {
  transform:translateY(-12px) scale(1.07) rotateX(4deg) rotateY(-2deg);
  z-index:10;
  filter:drop-shadow(0 24px 48px rgba(0,0,0,0.85));
}

/* Card base */
.mbt-card {
  width:140px;
  min-height:200px;
  border-radius:14px;
  position:relative;
  overflow:visible;
  font-family:var(--font-rivals);
  user-select:none;
  transform-style:preserve-3d;
}

/* Glass shimmer on hover */
.mbt-card::after {
  content:'';
  position:absolute;
  top:0;
  left:-60%;
  width:40%;
  height:100%;
  background:linear-gradient(105deg,transparent,rgba(255,255,255,0.18),transparent);
  transform:skewX(-15deg);
  transition:none;
  z-index:25;
  pointer-events:none;
  border-radius:14px;
  opacity:0;
}
.mbt-card-wrap:hover .mbt-card::after {
  animation:glassShimmer 0.7s ease 0.05s forwards;
  opacity:1;
}

/* ── BG IMAGE ── */
.mbt-card-bg-image {
  position:absolute;
  inset:0;
  background-size:cover;
  background-position:center top;
  border-radius:14px;
  z-index:0;
}

/* ── OVERLAY ── */
.mbt-card-overlay {
  position:absolute;
  inset:0;
  border-radius:14px;
  z-index:1;
  pointer-events:none;
}

/* ── HOVER GLOW OVERLAY ── */
.mbt-card-hover-overlay {
  position:absolute;
  inset:0;
  border-radius:14px;
  z-index:22;
  pointer-events:none;
  opacity:0;
  background:radial-gradient(ellipse at 50% 30%,rgba(255,255,255,0.12) 0%,transparent 70%);
  transition:opacity 0.35s;
}
.mbt-card-wrap:hover .mbt-card-hover-overlay {
  opacity:1;
}

/* ── PHOTO ── */
.mbt-card-photo {
  position:absolute;
  top:16%;
  left:50%;
  transform:translateX(-50%);
  width:68%;
  height:44%;
  object-fit:cover;
  border-radius:6px;
  z-index:3;
}
.mbt-card-photo-placeholder {
  position:absolute;
  top:18%;
  left:50%;
  transform:translateX(-50%);
  font-size:2rem;
  z-index:3;
  text-align:center;
  filter:drop-shadow(0 2px 8px rgba(0,0,0,0.7));
}

/* ── OVR ── */
.mbt-card-ovr {
  position:absolute;
  top:6px;
  left:8px;
  font-family:var(--font-rivals);
  font-weight:900;
  z-index:10;
  text-shadow:0 0 12px currentColor, 0 2px 4px rgba(0,0,0,0.9);
  line-height:1;
}

/* ── TIER LABEL ── */
.mbt-card-tier-label {
  position:absolute;
  top:6px;
  right:7px;
  font-size:0.38rem;
  font-weight:700;
  letter-spacing:1px;
  text-transform:uppercase;
  z-index:10;
  text-shadow:0 0 8px currentColor;
  opacity:0.9;
}

/* ── NAME BLOCK ── */
.mbt-card-name-block {
  position:absolute;
  bottom:50px;
  left:0;
  right:0;
  text-align:center;
  z-index:10;
  padding:0 4px;
  line-height:1.1;
}
.mbt-card-firstname {
  display:block;
  font-size:0.38rem;
  font-weight:400;
  letter-spacing:2px;
  text-transform:uppercase;
  opacity:0.8;
  text-shadow:0 0 8px currentColor;
}
.mbt-card-lastname {
  display:block;
  font-weight:900;
  letter-spacing:1px;
  text-transform:uppercase;
  text-shadow:0 0 14px currentColor;
}

/* ── ROLE ── */
.mbt-card-role {
  position:absolute;
  bottom:35px;
  left:0;
  right:0;
  text-align:center;
  font-size:0.38rem;
  font-weight:600;
  letter-spacing:1.5px;
  text-transform:uppercase;
  z-index:10;
  opacity:0.75;
}

/* ── STATS ── */
.mbt-card-stats {
  position:absolute;
  bottom:6px;
  left:4px;
  right:4px;
  display:flex;
  justify-content:space-around;
  z-index:10;
}
.mbt-stat {
  text-align:center;
  flex:1;
}
.mbt-stat-val {
  font-size:0.6rem;
  font-weight:900;
  line-height:1;
  text-shadow:0 0 8px currentColor;
}
.mbt-stat-lbl {
  font-size:0.3rem;
  color:#999;
  letter-spacing:1px;
  text-transform:uppercase;
  line-height:1;
}

/* ── HP BAR ── */
.hp-bar-container {
  height:10px;
  background:#1a1a2a;
  border-radius:5px;
  overflow:hidden;
  border:1px solid #2a2a3a;
}
.hp-bar-fill {
  height:100%;
  background:linear-gradient(90deg,#16a34a,#4ade80);
  border-radius:5px;
  transition:width 0.5s ease;
}
.hp-bar-fill.danger {
  background:linear-gradient(90deg,#dc2626,#ef4444);
  animation:pulseGlow 1s infinite;
}

/* ── BATTLE ── */
.battle-card-slot {
  border:2px solid #1e1e3a;
  border-radius:10px;
  padding:10px;
  background:rgba(255,255,255,0.02);
  min-height:180px;
  display:flex;
  align-items:center;
  justify-content:center;
  cursor:pointer;
  transition:border-color 0.2s, background 0.2s;
}
.battle-card-slot.active {
  border-color:#ffd700;
  background:rgba(255,215,0,0.05);
}
.battle-card-slot:hover {
  border-color:#4169e1;
  background:rgba(65,105,225,0.05);
}
.battle-log {
  background:#05050f;
  border:1px solid #1e1e3a;
  border-radius:8px;
  padding:10px;
  max-height:200px;
  overflow-y:auto;
  font-family:var(--font-body);
  font-size:0.75rem;
}

/* ── ARENA ── */
.arena-badge {
  border-radius:10px;
  padding:16px;
  text-align:center;
  cursor:pointer;
  transition:transform 0.2s, box-shadow 0.2s;
  position:relative;
  overflow:hidden;
}
.arena-badge:hover {transform:translateY(-4px);}
.arena-base {background:linear-gradient(135deg,#2a1f0f,#5a3a0f);border:2px solid #cd7f32;}
.arena-epica {background:linear-gradient(135deg,#1a003a,#4a0080);border:2px solid #9b59b6;}
.arena-leggendaria {background:linear-gradient(135deg,#0a0a0a,#2a2a2a);border:2px solid #fff;}
.arena-toty {background:linear-gradient(135deg,#000820,#001855);border:2px solid #4169e1;}
.arena-icona {background:linear-gradient(135deg,#1a0f00,#3d2800);border:3px solid #ffd700;}
.arena-icona-epica {background:linear-gradient(135deg,#1a0030,#4a0090);border:3px solid #cc44ff;}
.arena-icona-leggendaria {background:linear-gradient(135deg,#111,#2a2a2a);border:3px solid #fff;box-shadow:0 0 30px rgba(255,255,255,0.3);}
.arena-toty-plus {background:linear-gradient(135deg,#000820,#001060);border:4px solid #4169e1;box-shadow:0 0 30px rgba(65,105,225,0.5);}
.arena-god {background:linear-gradient(135deg,#0a0000,#2a0000);border:4px solid #ff2200;box-shadow:0 0 40px rgba(255,34,0,0.6);}
.arena-omega {background:linear-gradient(135deg,#000,#000);border:4px solid transparent;box-shadow:0 0 60px rgba(255,0,200,0.8),0 0 120px rgba(0,100,255,0.6);}

/* ── PACK CARDS ── */
.pack-card {
  transition:transform 0.3s, box-shadow 0.3s;
}
.pack-card:hover {transform:scale(1.04) translateY(-4px);}
.pack-base {background:linear-gradient(160deg,#2a1f0f,#5a3a0f,#2a1f0f);border:2px solid #cd7f32;box-shadow:0 0 20px rgba(205,127,50,0.3);}
.pack-epico {background:linear-gradient(160deg,#1a0033,#4a0080,#1a0033);border:2px solid #9b59b6;box-shadow:0 0 25px rgba(155,89,182,0.4);}
.pack-leggenda {background:linear-gradient(160deg,#1a0a00,#3a1a00,#1a0a00);border:2px solid #ff6600;box-shadow:0 0 30px rgba(255,100,0,0.5);}

/* ── COLLECTION ── */
.collection-filter-btn {
  border:1px solid;
  border-radius:20px;
  padding:4px 12px;
  cursor:pointer;
  font-size:0.7rem;
  font-family:var(--font-rivals);
  transition:all 0.2s;
  background:transparent;
}
.collection-filter-btn.active {background:var(--rivals-gold);border-color:var(--rivals-gold);color:#000;}
.collection-filter-btn:not(.active) {color:var(--rivals-gold);border-color:#555;}

/* ── CARD CREATOR ── */
.creator-preview-wrap {
  display:flex;
  justify-content:center;
  padding:20px;
  background:radial-gradient(ellipse at center,rgba(255,215,0,0.06) 0%,transparent 70%);
  border-radius:12px;
  border:1px dashed #333;
}

/* ── PACK REVEAL ANIMATION ── */
.pack-revealed-card {animation:cardFlipIn 0.75s cubic-bezier(0.34,1.56,0.64,1) both;}
.pack-revealed-card-god {animation:godReveal 1.1s cubic-bezier(0.34,1.56,0.64,1) both;}
</style>
"""


# ─── DATA HELPERS ─────────────────────────────────────────────────────────────

def load_rivals_data():
    if Path(RIVALS_FILE).exists():
        with open(RIVALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return empty_rivals_state()

def save_rivals_data(data):
    with open(RIVALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_cards_db():
    if Path(CARDS_DB_FILE).exists():
        with open(CARDS_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": [], "next_id": 1}

def save_cards_db(db):
    with open(CARDS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def _data_checksum(data: dict) -> str:
    """Hash veloce per rilevare se i dati sono cambiati."""
    try:
        return hashlib.md5(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    except Exception:
        return ""

def _save_if_dirty(rivals_data: dict, cards_db: dict):
    """Scrive su disco solo se i dati sono effettivamente cambiati dall'ultimo save."""
    r_key = "_rivals_cksum"
    c_key = "_cards_cksum"
    r_cksum = _data_checksum(rivals_data)
    c_cksum = _data_checksum(cards_db)
    if st.session_state.get(r_key) != r_cksum:
        save_rivals_data(rivals_data)
        st.session_state[r_key] = r_cksum
    if st.session_state.get(c_key) != c_cksum:
        save_cards_db(cards_db)
        st.session_state[c_key] = c_cksum

def empty_rivals_state():
    return {
        "player_level": 1,
        "player_xp": 0,
        "mbt_coins": 500,
        "trofei_rivals": 0,
        "collection": [],
        "active_team": [],
        "arena_unlocked": 1,
        "battle_wins": 0,
        "battle_losses": 0,
        "special_moves_learned": [],
        "superpowers": {},
        "achievements": [],
    }


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

ROLES = [
    "SPIKER", "IRONBLOCKER", "DIFENSORE", "ACER",
    "SPECIALISTA", "TRAINER - Fisioterapista",
    "TRAINER - Mental Coach", "TRAINER - Scoutman"
]

ROLE_ICONS = {
    "SPIKER": "⚡", "IRONBLOCKER": "🛡️", "DIFENSORE": "🤿",
    "ACER": "🎯", "SPECIALISTA": "🔮",
    "TRAINER - Fisioterapista": "💊", "TRAINER - Mental Coach": "🧠",
    "TRAINER - Scoutman": "🔭"
}

ROLE_DESCRIPTIONS = {
    "SPIKER": "Super Attacco: Nocchino di Ghiaccio – attacco che non fallisce mai",
    "IRONBLOCKER": "Fortezza di Titanio (Annulla danni) o Muro Corna (danno+difesa)",
    "DIFENSORE": "Dig Classico / Sky Dive / Sabbia Mobile (recupera HP)",
    "ACER": "Jump Float Infuocato – danni critici doppi se vince il turno battuta",
    "SPECIALISTA": "Seconda Intenzione – attacca nel turno difesa",
    "TRAINER - Fisioterapista": "Riduce consumo Stamina del 20%",
    "TRAINER - Mental Coach": "Aumenta danni Super quando HP < 30%",
    "TRAINER - Scoutman": "Vedi in anticipo la prima carta CPU",
}

CARD_TIERS = {
    "Bronzo Comune":    {"ovr_range":(40,44), "color":"#cd7f32", "rarity":0},
    "Bronzo Raro":      {"ovr_range":(45,49), "color":"#e8902a", "rarity":1},
    "Argento Comune":   {"ovr_range":(50,54), "color":"#c0c0c0", "rarity":2},
    "Argento Raro":     {"ovr_range":(55,59), "color":"#d8d8d8", "rarity":3},
    "Oro Comune":       {"ovr_range":(60,64), "color":"#ffd700", "rarity":4},
    "Oro Raro":         {"ovr_range":(65,69), "color":"#ffec4a", "rarity":5},
    "Eroe":             {"ovr_range":(70,74), "color":"#9b59b6", "rarity":6},
    "IF (In Form)":     {"ovr_range":(75,79), "color":"#b07dd0", "rarity":7},
    "Leggenda":         {"ovr_range":(80,84), "color":"#ffffff", "rarity":8},
    "TOTY":             {"ovr_range":(85,89), "color":"#4169e1", "rarity":9},
    "TOTY Evoluto":     {"ovr_range":(90,94), "color":"#6a8fff", "rarity":10},
    "GOAT":             {"ovr_range":(95,99), "color":"#ff4400", "rarity":11},
    "ICON BASE":        {"ovr_range":(100,104),"color":"#ffd700", "rarity":12},
    "ICON EPICA":       {"ovr_range":(105,109),"color":"#cc44ff", "rarity":13},
    "ICON LEGGENDARIA": {"ovr_range":(110,114),"color":"#ffffff", "rarity":14},
    "ICON TOTY":        {"ovr_range":(115,119),"color":"#4169e1", "rarity":15},
    "ICON GOD":         {"ovr_range":(120,125),"color":"#ff2200", "rarity":16},
}

# Mapping tier → file immagine carta
TIER_CARD_IMAGES = {
    "Bronzo Comune":    "BRONZO_png.webp",
    "Bronzo Raro":      "BRONZO_RARO_png.webp",
    "Argento Comune":   "ARGENTO.png",
    "Argento Raro":     "argento_raro_png.webp",
    "Oro Comune":       "ORO.png",
    "Oro Raro":         "ORO_RARO_png.webp",
    "Eroe":             "EROE.png",
    "IF (In Form)":     "EROE.png",
    "Leggenda":         "LEGGENDA.png",
    "TOTY":             "TOTY.webp",
    "TOTY Evoluto":     "TOTY_EVOLUTO.png",
    "GOAT":             "GOAT_png.webp",
    "ICON BASE":        "ICON_BASE.png",
    "ICON EPICA":       "ICON_BASE.png",
    "ICON LEGGENDARIA": "ICON_LEGGENDARIA.png",
    "ICON TOTY":        "ICON_TOTY_png.webp",
    "ICON GOD":         "ICONA_GOD.png",
}

def get_tier_by_ovr(ovr):
    for tier_name, td in CARD_TIERS.items():
        lo, hi = td["ovr_range"]
        if lo <= ovr <= hi:
            return tier_name
    if ovr >= 120: return "ICON GOD"
    if ovr >= 115: return "ICON TOTY"
    if ovr >= 110: return "ICON LEGGENDARIA"
    if ovr >= 105: return "ICON EPICA"
    if ovr >= 100: return "ICON BASE"
    if ovr >= 95: return "GOAT"
    return "TOTY Evoluto"


PACKS = {
    "Base": {
        "price": 200,
        "css_class": "pack-base",
        "label_color": "#cd7f32",
        "description": "6 carte | Comuni e Rare",
        "weights": {
            "Bronzo Comune":0.30,"Bronzo Raro":0.25,"Argento Comune":0.20,
            "Argento Raro":0.12,"Oro Comune":0.07,"Oro Raro":0.04,
            "Eroe":0.015,"IF (In Form)":0.005
        }
    },
    "Epico": {
        "price": 500,
        "css_class": "pack-epico",
        "label_color": "#9b59b6",
        "description": "6 carte | Da Oro a Leggenda",
        "weights": {
            "Oro Comune":0.25,"Oro Raro":0.22,"Eroe":0.18,
            "IF (In Form)":0.15,"Leggenda":0.08,"TOTY":0.04,
            "TOTY Evoluto":0.02,"GOAT":0.01,
            "ICON BASE":0.008,"ICON EPICA":0.002
        }
    },
    "Leggenda": {
        "price": 1200,
        "css_class": "pack-leggenda",
        "label_color": "#ff6600",
        "description": "6 carte | Alta probabilità di Speciali",
        "weights": {
            "Leggenda":0.25,"TOTY":0.20,"TOTY Evoluto":0.18,
            "GOAT":0.12,"ICON BASE":0.10,"ICON EPICA":0.07,
            "ICON LEGGENDARIA":0.04,"ICON TOTY":0.02,"ICON GOD":0.01,
            "IF (In Form)":0.01
        }
    },
}

ARENE = [
    {"min_level":1,  "max_level":2,  "name":"Arena Base",            "css":"arena-base",             "color":"#cd7f32", "icon":"🏟️"},
    {"min_level":3,  "max_level":4,  "name":"Arena Epica",           "css":"arena-epica",            "color":"#9b59b6", "icon":"⚡"},
    {"min_level":5,  "max_level":6,  "name":"Arena Leggendaria",     "css":"arena-leggendaria",      "color":"#ffffff", "icon":"👑"},
    {"min_level":7,  "max_level":8,  "name":"Arena TOTY",            "css":"arena-toty",             "color":"#4169e1", "icon":"🌟"},
    {"min_level":9,  "max_level":10, "name":"Arena ICONA",           "css":"arena-icona",            "color":"#ffd700", "icon":"🏆"},
    {"min_level":11, "max_level":12, "name":"Arena ICONA EPICA",     "css":"arena-icona-epica",      "color":"#cc44ff", "icon":"💫"},
    {"min_level":13, "max_level":14, "name":"Arena ICONA LEGGEND.",  "css":"arena-icona-leggendaria","color":"#ffffff", "icon":"✨"},
    {"min_level":15, "max_level":16, "name":"Arena TOTY SUPREMA",    "css":"arena-toty-plus",        "color":"#4169e1", "icon":"🔮"},
    {"min_level":17, "max_level":18, "name":"Arena GOD MODE",        "css":"arena-god",              "color":"#ff2200", "icon":"🔥"},
    {"min_level":19, "max_level":20, "name":"Arena OMEGA",           "css":"arena-omega",            "color":"#ff00cc", "icon":"⚜️"},
]

XP_PER_LEVEL = [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700,
                3250, 3850, 4500, 5200, 5950, 6750, 7600, 8500, 9450, 10450]

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


# ─── CARD BACKGROUND IMAGE HELPER ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _get_card_bg_b64(tier_name):
    """Cached: legge il PNG template dal disco UNA SOLA VOLTA per sessione."""
    img_filename = TIER_CARD_IMAGES.get(tier_name, "")
    if not img_filename:
        return None, None
    search_paths = [
        os.path.join(ASSETS_CARDS_DIR, img_filename),
        os.path.join("assets", img_filename),
        os.path.join("/mnt/user-data/uploads", img_filename),
    ]
    for p in search_paths:
        if os.path.exists(p):
            ext = img_filename.rsplit(".", 1)[-1].lower()
            mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg",
                    "webp":"image/webp","gif":"image/gif"}.get(ext,"image/png")
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return b64, mime
    return None, None


@st.cache_data(show_spinner=False)
def _load_image_b64_cached(path: str):
    """Cached: carica immagine da path UNA SOLA VOLTA per sessione. Usata da mbt_draft.py."""
    if not path or not os.path.exists(path):
        return None, None
    ext  = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode(), mime
    except Exception:
        return None, None


def _is_trainer(card: dict) -> bool:
    """Restituisce True se la carta è di tipo TRAINER. Usata da mbt_draft.py."""
    return "TRAINER" in str(card.get("ruolo", ""))


# ─── ANIMATION OVERLAYS PER TIER ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _get_card_animation_overlay(tier_name, color, rarity):
    """Cached + deterministico: genera overlay animazione UNA SOLA VOLTA.
    Usa hash invece di random per posizioni particelle stabili."""

    def _h(seed, i, lo, hi):
        """Genera valore deterministico in range [lo, hi] da seed e indice."""
        v = int(hashlib.md5("{}{}".format(seed, i).encode()).hexdigest()[:8], 16)
        return lo + (v % (hi - lo + 1))

    def _hf(seed, i, lo, hi):
        v = int(hashlib.md5("{}{}f".format(seed, i).encode()).hexdigest()[:8], 16)
        return lo + (v % 1000) / 1000.0 * (hi - lo)

    if tier_name == "ICON GOD":
        particles = ""
        for i in range(8):
            dx = _h("igdx", i, -30, 30)
            dy = _h("igdy", i, -50, -15)
            delay = round(_hf("igd", i, 0, 2.5), 2)
            dur = round(_hf("igdr", i, 1.2, 2.5), 2)
            top = _h("igt", i, 20, 75)
            left = _h("igl", i, 10, 90)
            particles += (
                '<div style="position:absolute;width:3px;height:3px;'
                'background:linear-gradient(#ff4400,#ffaa00);border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 6px #ff4400"></div>'
            ).format(top=top, left=left, dur=dur, delay=delay, dx=dx, dy=dy)
        fire = (
            '<div style="position:absolute;bottom:0;left:0;right:0;height:40%;'
            'background:linear-gradient(0deg,rgba(255,40,0,0.55),rgba(255,100,0,0.22),transparent);'
            'animation:fireFlicker 0.4s infinite alternate;pointer-events:none"></div>'
            '<div style="position:absolute;top:12%;left:47%;width:3px;height:72%;'
            'background:linear-gradient(180deg,rgba(255,255,0,0.95),transparent);'
            'transform:rotate(8deg);animation:lightningFlash 1.2s infinite;'
            'box-shadow:0 0 8px #ffff00;pointer-events:none"></div>'
            '<div style="position:absolute;top:18%;left:28%;width:2px;height:55%;'
            'background:linear-gradient(180deg,rgba(255,200,0,0.8),transparent);'
            'transform:rotate(-15deg);animation:lightningFlash 1.8s 0.3s infinite;'
            'box-shadow:0 0 6px #ffaa00;pointer-events:none"></div>'
        )
        border_anim = '<div style="position:absolute;inset:-2px;border-radius:16px;border:2px solid #ff2200;animation:iconGodPulse 1.5s infinite;pointer-events:none;z-index:30"></div>'
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>{}'.format(fire, particles, border_anim)
        )

    elif tier_name == "ICON TOTY":
        particles = ""
        for i in range(10):
            dx = _h("itdx", i, -30, 30)
            dy = _h("itdy", i, -55, -10)
            delay = round(_hf("itd", i, 0, 3), 2)
            dur = round(_hf("itdr", i, 1.5, 3), 2)
            top = _h("itt", i, 15, 80)
            left = _h("itl", i, 10, 90)
            particles += (
                '<div style="position:absolute;width:4px;height:4px;'
                'background:{color};border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 8px {color}"></div>'
            ).format(color=color, top=top, left=left, dur=dur, delay=delay, dx=dx, dy=dy)
        beam = (
            '<div style="position:absolute;inset:-40px;'
            'background:conic-gradient(from 0deg,transparent 0deg,rgba(65,105,225,0.35) 30deg,transparent 60deg,rgba(100,180,255,0.25) 120deg,transparent 150deg);'
            'animation:beamRotate 3s linear infinite;border-radius:50%;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(beam, particles)
        )

    elif tier_name == "ICON LEGGENDARIA":
        particles = ""
        for i in range(7):
            dx = _h("ildx", i, -25, 25)
            dy = _h("ildy", i, -45, -8)
            delay = round(_hf("ild", i, 0, 3.5), 2)
            dur = round(_hf("ildr", i, 2, 4), 2)
            top = _h("ilt", i, 20, 75)
            left = _h("ill", i, 15, 85)
            particles += (
                '<div style="position:absolute;width:3px;height:3px;'
                'background:white;border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 8px white"></div>'
            ).format(top=top, left=left, dur=dur, delay=delay, dx=dx, dy=dy)
        sheen = (
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,0.14) 50%,transparent 70%);'
            'background-size:200% 200%;animation:holographic 2.2s infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(sheen, particles)
        )

    elif tier_name == "ICON EPICA":
        particles = ""
        for i in range(6):
            dx = _h("iedx", i, -20, 20)
            dy = _h("iedy", i, -40, -8)
            delay = round(_hf("ied", i, 0, 3), 2)
            dur = round(_hf("iedr", i, 2, 4), 2)
            top = _h("iet", i, 25, 70)
            left = _h("iel", i, 15, 85)
            particles += (
                '<div style="position:absolute;width:3px;height:3px;'
                'background:{color};border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 6px {color}"></div>'
            ).format(color=color, top=top, left=left, dur=dur, delay=delay, dx=dx, dy=dy)
        nebula = (
            '<div style="position:absolute;inset:-30px;'
            'background:conic-gradient(from 0deg,transparent,rgba(180,0,255,0.2),transparent,rgba(100,0,200,0.15),transparent);'
            'animation:nebulaSwirl 5s linear infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(nebula, particles)
        )

    elif tier_name == "ICON BASE":
        particles = ""
        for i in range(5):
            dx = _h("ibdx", i, -18, 18)
            dy = _h("ibdy", i, -35, -8)
            delay = round(_hf("ibd", i, 0, 2.5), 2)
            top = _h("ibt", i, 30, 70)
            left = _h("ibl", i, 20, 80)
            particles += (
                '<div style="position:absolute;width:2px;height:2px;'
                'background:{color};border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle 2.8s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 5px {color}"></div>'
            ).format(color=color, top=top, left=left, delay=delay, dx=dx, dy=dy)
        nebula = (
            '<div style="position:absolute;width:80px;height:80px;top:-10px;left:-10px;'
            'background:radial-gradient(ellipse at center,rgba(255,215,0,0.25) 0%,transparent 70%);'
            'animation:nebulaFloat 6s ease-in-out infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(nebula, particles)
        )

    elif tier_name == "GOAT":
        particles = ""
        for i in range(6):
            dx = _h("gdx", i, -20, 20)
            dy = _h("gdy", i, -40, -10)
            delay = round(_hf("gd", i, 0, 2.5), 2)
            dur = round(_hf("gdr", i, 1.8, 3.2), 2)
            top = _h("gt", i, 20, 75)
            left = _h("gl", i, 10, 90)
            particles += (
                '<div style="position:absolute;width:3px;height:3px;'
                'background:{color};border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8;box-shadow:0 0 6px {color}"></div>'
            ).format(color=color, top=top, left=left, dur=dur, delay=delay, dx=dx, dy=dy)
        fire_small = (
            '<div style="position:absolute;bottom:0;left:0;right:0;height:28%;'
            'background:linear-gradient(0deg,rgba(255,68,0,0.45),transparent);'
            'animation:fireFlicker 0.6s infinite alternate;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(fire_small, particles)
        )

    elif tier_name in ("TOTY", "TOTY Evoluto"):
        beam = (
            '<div style="position:absolute;inset:-30px;'
            'background:conic-gradient(from 0deg,transparent 0deg,rgba(65,105,225,0.22) 30deg,transparent 60deg);'
            'animation:beamRotate 4s linear infinite;border-radius:50%;pointer-events:none"></div>'
        )
        particles = ""
        for i in range(4):
            dx = _h("tdx", i, -15, 15)
            dy = _h("tdy", i, -35, -8)
            delay = round(_hf("td", i, 0, 2), 2)
            top = _h("tt", i, 25, 70)
            left = _h("tl", i, 15, 85)
            particles += (
                '<div style="position:absolute;width:2px;height:2px;'
                'background:{color};border-radius:50%;'
                'top:{top}%;left:{left}%;animation:driftParticle 2.5s {delay}s infinite;'
                '--dx:{dx}px;--dy:{dy}px;z-index:8"></div>'
            ).format(color=color, top=top, left=left, delay=delay, dx=dx, dy=dy)
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}{}</div>'.format(beam, particles)
        )

    elif tier_name == "Leggenda":
        sheen = (
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(135deg,transparent 30%,rgba(255,255,255,0.11) 50%,transparent 70%);'
            'background-size:200% 200%;animation:holographic 2.8s infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}</div>'.format(sheen)
        )

    elif tier_name in ("Eroe", "IF (In Form)"):
        nebula = (
            '<div style="position:absolute;inset:0;'
            'background:radial-gradient(ellipse at 50% 30%,rgba(155,89,182,0.28) 0%,transparent 70%);'
            'animation:holoSheen 3.5s infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}</div>'.format(nebula)
        )

    elif rarity >= 5:
        shimmer = (
            '<div style="position:absolute;top:0;left:-80%;width:40%;height:100%;'
            'background:linear-gradient(105deg,transparent,rgba(255,215,0,0.22),transparent);'
            'animation:shimmer 2.2s infinite;transform:skewX(-15deg);pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}</div>'.format(shimmer)
        )

    elif rarity >= 2:
        sheen = (
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(135deg,transparent 40%,rgba(255,255,255,0.07) 50%,transparent 60%);'
            'background-size:200% 200%;animation:holoSheen 4.5s infinite;pointer-events:none"></div>'
        )
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;z-index:6;overflow:hidden;border-radius:inherit">'
            '{}</div>'.format(sheen)
        )

    return ""


# ─── CARD BORDER STYLE PER TIER ──────────────────────────────────────────────

def _get_card_border_style(tier_name, color, rarity):
    """Restituisce lo stile inline del bordo/box-shadow per ogni tier."""
    if tier_name == "ICON GOD":
        return (
            "border:3px solid #ff2200;"
            "box-shadow:0 0 22px #ff2200,0 0 50px #880000,0 0 90px #440000;"
            "border-radius:14px;"
        )
    elif tier_name == "ICON TOTY":
        return (
            "border:3px solid {c};"
            "box-shadow:0 0 25px {c},0 0 60px {c}55,0 0 100px {c}33;"
            "border-radius:14px;"
        ).format(c=color)
    elif tier_name in ("ICON LEGGENDARIA", "ICON EPICA", "ICON BASE"):
        return (
            "border:2px solid {c};"
            "box-shadow:0 0 20px {c}88,0 0 40px {c}44;"
            "border-radius:14px;"
        ).format(c=color)
    elif tier_name == "GOAT":
        return (
            "border:2px solid {c};"
            "box-shadow:0 0 18px {c}99,0 0 35px {c}44;"
            "border-radius:14px;"
        ).format(c=color)
    elif tier_name in ("TOTY", "TOTY Evoluto"):
        return (
            "border:2px solid {c};"
            "box-shadow:0 0 16px {c}99,0 0 32px {c}44;"
            "border-radius:14px;"
        ).format(c=color)
    elif tier_name == "Leggenda":
        return (
            "border:2px solid #ffffff;"
            "box-shadow:0 0 16px rgba(255,255,255,0.5),0 0 32px rgba(255,255,255,0.2);"
            "border-radius:14px;"
        )
    elif rarity >= 6:
        return (
            "border:2px solid {c};"
            "box-shadow:0 0 14px {c}88;"
            "border-radius:14px;"
        ).format(c=color)
    elif rarity >= 4:
        return (
            "border:1px solid {c};"
            "box-shadow:0 0 10px {c}66;"
            "border-radius:14px;"
        ).format(c=color)
    else:
        return (
            "border:1px solid {c}55;"
            "border-radius:14px;"
        ).format(c=color)


# ─── CARD RENDERING ───────────────────────────────────────────────────────────
# render_card_html è un wrapper di render_card_html_custom (definito più avanti).
# Python carica tutto il modulo prima dell'esecuzione, quindi funziona correttamente.

def render_card_html(card_data, size="normal", show_special_effects=True):
    """Wrapper principale — usa PNG carta custom e animazioni salvate se disponibili."""
    tier_name = get_tier_by_ovr(card_data.get("overall", 40))
    tier_color = CARD_TIERS.get(tier_name, {}).get("color", "#ffd700")
    custom_anims = card_data.get("custom_animations", [])

    # PNG corpo carta: usa path custom (cached) se esiste, altrimenti tier default (cached)
    card_png_path = card_data.get("card_png_path", "")
    if card_png_path and os.path.exists(card_png_path):
        card_png_b64, card_png_mime = _load_card_png_b64(card_png_path)
    else:
        card_png_b64, card_png_mime = _get_card_bg_b64(tier_name)

    # Animazioni custom
    custom_css, custom_overlay = ("", "")
    if custom_anims:
        custom_css, custom_overlay = build_custom_animation_css(tuple(custom_anims), card_color=tier_color)

    return render_card_html_custom(
        card_data,
        card_png_b64=card_png_b64,
        card_png_mime=card_png_mime,
        custom_anim_css=custom_css,
        custom_anim_overlay=custom_overlay,
        size=size,
        show_special_effects=(show_special_effects and not custom_anims)
    )


# ─── PACK OPENING ANIMATION ─────────────────────────────────────────────────

def render_pack_opening_animation(drawn_cards, pack_name):
    st.markdown("### 🎁 Apertura **{}** — Carte trovate:".format(pack_name))
    cols = st.columns(6)
    for i, card in enumerate(drawn_cards):
        tier = get_tier_by_ovr(card.get("overall", 40))
        rarity = CARD_TIERS.get(tier, {}).get("rarity", 0)
        tier_color = CARD_TIERS.get(tier, {}).get("color", "#fff")
        with cols[i]:
            delay = i * 0.18
            anim_class = "pack-revealed-card-god" if rarity >= 16 else "pack-revealed-card"
            label_html = ""
            if rarity >= 12:
                label_html = '<div style="text-align:center;font-size:0.58rem;color:{tc};margin-top:4px;font-weight:700;letter-spacing:2px;text-shadow:0 0 8px {tc}">⚡ {t} ⚡</div>'.format(tc=tier_color, t=tier)
            elif rarity >= 8:
                label_html = '<div style="text-align:center;font-size:0.55rem;color:{tc};margin-top:4px">✦ {t} ✦</div>'.format(tc=tier_color, t=tier)
            else:
                label_html = '<div style="text-align:center;font-size:0.5rem;color:#888;margin-top:4px">{t}</div>'.format(t=tier)

            st.markdown(
                '<div class="{anim}" style="animation-delay:{delay}s">{card}</div>{label}'.format(
                    anim=anim_class, delay=delay,
                    card=render_card_html(card, size="small"),
                    label=label_html
                ),
                unsafe_allow_html=True
            )


# ─── BATTLE ENGINE ────────────────────────────────────────────────────────────

def init_battle_state(player_cards, cpu_level=1):
    def make_fighter(card, is_cpu=False):
        ovr = card.get("overall", 40)
        base_hp = 80 + ovr * 2
        if is_cpu:
            base_hp = int(base_hp * (0.9 + cpu_level * 0.1))
        return {"card": card, "hp": base_hp, "max_hp": base_hp, "stamina": 100, "shield": 0}

    player_fighters = [make_fighter(c) for c in player_cards[:3]]
    cpu_ovr_base = 40 + cpu_level * 4
    cpu_cards = []
    for _ in range(3):
        ovr = min(99, cpu_ovr_base + random.randint(-5, 10))
        cpu_cards.append({
            "nome": random.choice(["Robot","CPU","AI","BOT"]),
            "overall": ovr,
            "ruolo": random.choice(list(ROLE_ICONS.keys())[:5]),
            "attacco": max(40, ovr - random.randint(0, 10)),
            "difesa": max(40, ovr - random.randint(0, 10)),
            "battuta": max(40, ovr - random.randint(0, 10)),
            "foto_path": "",
        })
    cpu_fighters = [make_fighter(c, is_cpu=True) for c in cpu_cards]
    return {
        "player_fighters": player_fighters,
        "cpu_fighters": cpu_fighters,
        "player_active_idx": 0,
        "cpu_active_idx": 0,
        "turn": 0,
        "phase": "battle",
        "log": [],
        "stamina_charges": 0,
        "start_time": time.time(),
        "time_limit": 300,
    }


def calculate_damage(attacker_card, defender_card, move_type="attack", superpowers=None):
    atk = attacker_card.get("attacco", 40)
    def_ = defender_card.get("difesa", 40)
    base = max(5, (atk - def_ * 0.6) * 0.4 + random.randint(3, 12))
    if move_type == "special":
        base *= 1.8
    elif move_type == "super":
        base *= 2.5
    if superpowers:
        kill_shot_lvl = superpowers.get("kill_shot", 0)
        base *= (1 + kill_shot_lvl * 0.08)
    return max(5, int(base))


def cpu_choose_action(cpu_fighter, player_fighter, turn):
    hp_ratio = cpu_fighter["hp"] / max(1, cpu_fighter["max_hp"])
    if cpu_fighter["stamina"] >= 50 and random.random() < 0.3:
        return "special"
    if hp_ratio < 0.3:
        return random.choice(["attack", "attack", "special", "defend"])
    return random.choice(["attack", "attack", "attack", "defend"])


def process_battle_action(battle_state, action, rivals_data):
    p_idx = battle_state["player_active_idx"]
    c_idx = battle_state["cpu_active_idx"]
    p_fighter = battle_state["player_fighters"][p_idx]
    c_fighter = battle_state["cpu_fighters"][c_idx]
    log = battle_state["log"]
    superpowers = rivals_data.get("superpowers", {})
    player_name = p_fighter["card"].get("nome", "Player")
    cpu_name = c_fighter["card"].get("nome", "CPU")

    if action == "attack":
        dmg = calculate_damage(p_fighter["card"], c_fighter["card"], "attack", superpowers)
        c_fighter["hp"] = max(0, c_fighter["hp"] - dmg)
        p_fighter["stamina"] = min(100, p_fighter["stamina"] + 10)
        log.append("⚡ {} attacca → {} danni! (HP CPU: {})".format(player_name, dmg, c_fighter["hp"]))
        battle_state["stamina_charges"] += 1
    elif action == "special":
        if p_fighter["stamina"] >= 40:
            dmg = calculate_damage(p_fighter["card"], c_fighter["card"], "special", superpowers)
            c_fighter["hp"] = max(0, c_fighter["hp"] - dmg)
            p_fighter["stamina"] -= 40
            log.append("🔥 {} SUPER ATTACCO → {} danni!".format(player_name, dmg))
        else:
            log.append("⚠️ Stamina insufficiente per Super Attacco!")
    elif action == "defend":
        p_fighter["shield"] = 30
        p_fighter["stamina"] = min(100, p_fighter["stamina"] + 20)
        log.append("🛡️ {} si difende! Scudo attivato.".format(player_name))
    elif action == "final":
        if battle_state["stamina_charges"] >= 10:
            dmg = calculate_damage(p_fighter["card"], c_fighter["card"], "super", superpowers)
            c_fighter["hp"] = max(0, c_fighter["hp"] - dmg)
            battle_state["stamina_charges"] = 0
            log.append("💥 MOSSA FINALE! {} → {} danni DEVASTANTI!".format(player_name, dmg))
        else:
            log.append("⚠️ Carica la Stamina per la Mossa Finale (10 attacchi)!")

    if c_fighter["hp"] <= 0:
        next_cpu = c_idx + 1
        if next_cpu < len(battle_state["cpu_fighters"]):
            battle_state["cpu_active_idx"] = next_cpu
            log.append("💀 {} eliminato! Prossimo avversario!".format(cpu_name))
        else:
            battle_state["phase"] = "win"
            log.append("🏆 HAI VINTO!")
            return

    if battle_state["phase"] == "battle":
        cpu_action = cpu_choose_action(c_fighter, p_fighter, battle_state["turn"])
        if cpu_action == "attack":
            cpu_dmg = calculate_damage(c_fighter["card"], p_fighter["card"], "attack")
            if p_fighter["shield"] > 0:
                cpu_dmg = max(0, cpu_dmg - p_fighter["shield"])
                p_fighter["shield"] = 0
                log.append("🛡️ Scudo! {} attacca → {} danni dopo difesa".format(cpu_name, cpu_dmg))
            else:
                log.append("🤖 {} attacca → {} danni!".format(cpu_name, cpu_dmg))
            p_fighter["hp"] = max(0, p_fighter["hp"] - cpu_dmg)
        elif cpu_action == "special":
            cpu_dmg = calculate_damage(c_fighter["card"], p_fighter["card"], "special")
            log.append("💫 {} SUPER MOSSA → {} danni!".format(cpu_name, cpu_dmg))
            p_fighter["hp"] = max(0, p_fighter["hp"] - cpu_dmg)
        elif cpu_action == "defend":
            c_fighter["shield"] = 25
            log.append("🤖 {} si difende!".format(cpu_name))

    if p_fighter["hp"] <= 0:
        next_p = p_idx + 1
        if next_p < len(battle_state["player_fighters"]):
            battle_state["player_active_idx"] = next_p
            log.append("💔 {} KO! Prossima carta!".format(player_name))
        else:
            battle_state["phase"] = "lose"
            log.append("💀 HAI PERSO!")

    battle_state["turn"] += 1
    if len(log) > 20:
        battle_state["log"] = log[-20:]


# ─── PACK DRAWING ─────────────────────────────────────────────────────────────

def draw_cards_from_pack(pack_name, cards_db):
    pack_info = PACKS[pack_name]
    weights = pack_info["weights"]
    tiers = list(weights.keys())
    probs = list(weights.values())
    total = sum(probs)
    probs = [p / total for p in probs]
    drawn = []
    all_cards = cards_db.get("cards", [])
    for _ in range(6):
        chosen_tier = random.choices(tiers, weights=probs, k=1)[0]
        matching = [c for c in all_cards if get_tier_by_ovr(c.get("overall", 40)) == chosen_tier]
        if matching:
            card = random.choice(matching).copy()
        else:
            tier_info = CARD_TIERS.get(chosen_tier, CARD_TIERS["Bronzo Comune"])
            lo, hi = tier_info["ovr_range"]
            ovr = random.randint(lo, hi)
            card = {
                "id": "gen_{}".format(random.randint(100000, 999999)),
                "nome": random.choice(["Marco","Luca","Andrea","Fabio","Simone","Giulio","Matteo","Riccardo"]),
                "cognome": random.choice(["Rossi","Bianchi","Ferrari","Conti","Esposito","Costa","Ricci","Serra"]),
                "overall": ovr,
                "ruolo": random.choice(list(ROLE_ICONS.keys())[:5]),
                "attacco": max(40, ovr - random.randint(0, 15)),
                "difesa": max(40, ovr - random.randint(0, 15)),
                "muro": max(40, ovr - random.randint(0, 20)),
                "ricezione": max(40, ovr - random.randint(0, 20)),
                "battuta": max(40, ovr - random.randint(0, 18)),
                "alzata": max(40, ovr - random.randint(0, 20)),
                "foto_path": "",
                "tier": chosen_tier,
                "generated": True,
            }
        card["instance_id"] = "inst_{}".format(random.randint(1000000, 9999999))
        drawn.append(card)
    return drawn


# ─── HELPER ───────────────────────────────────────────────────────────────────

def _check_level_up(rivals_data):
    level = rivals_data["player_level"]
    if level >= 20:
        return
    xp = rivals_data["player_xp"]
    xp_needed = XP_PER_LEVEL[level]
    if xp >= xp_needed:
        rivals_data["player_level"] += 1
        rivals_data["trofei_rivals"] += 10
        new_arena = next((a for a in ARENE if a["min_level"] <= rivals_data["player_level"] <= a["max_level"]), None)
        if new_arena:
            rivals_data["arena_unlocked"] = rivals_data["player_level"]


def _sync_ovr_from_tournament(state, cards_db):
    """Sincronizza OVR dal torneo — eseguita UNA SOLA VOLTA per sessione."""
    sync_key = "_sync_done_{}".format(id(cards_db))
    if st.session_state.get(sync_key):
        return
    st.session_state[sync_key] = True
    try:
        from data_manager import calcola_overall_fifa
        for atleta in state.get("atleti", []):
            ovr = calcola_overall_fifa(atleta)
            for card in cards_db.get("cards", []):
                if card.get("atleta_id") == atleta["id"]:
                    card["overall"] = ovr
                    s = atleta.get("stats", {})
                    card["attacco"] = s.get("attacco", 40)
                    card["difesa"] = s.get("difesa", 40)
                    card["muro"] = s.get("muro", 40)
                    card["ricezione"] = s.get("ricezione", 40)
                    card["battuta"] = s.get("battuta", 40)
                    card["alzata"] = s.get("alzata", 40)
    except Exception:
        pass


# ─── RENDER MAIN RIVALS ───────────────────────────────────────────────────────

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

    _sync_ovr_from_tournament(state, cards_db)  # run once via session flag

    level = rivals_data["player_level"]
    xp = rivals_data["player_xp"]
    coins = rivals_data["mbt_coins"]
    xp_needed = XP_PER_LEVEL[min(level, len(XP_PER_LEVEL) - 1)] if level < 20 else 99999
    xp_pct = min(100, int(xp / max(xp_needed, 1) * 100))
    current_arena = next((a for a in ARENE if a["min_level"] <= level <= a["max_level"]), ARENE[0])

    st.markdown("""
    <div style="background:linear-gradient(135deg,#080810,#10101e,#080810);
        border:2px solid #1e1e3a;border-radius:16px;padding:16px 24px;margin-bottom:20px;
        display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
            <div style="font-family:'Orbitron',sans-serif;font-size:1.6rem;font-weight:900;
                background:linear-gradient(90deg,#ffd700,#ffec4a,#ffd700);
                background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
                animation:goldShine 3s linear infinite">
                ⚡ MBT RIVALS
            </div>
            <div style="font-size:0.75rem;color:#666;letter-spacing:3px;margin-top:2px">CARD BATTLE SYSTEM</div>
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#ffd700">LV.{level}</div>
                <div style="font-size:0.6rem;color:#888;letter-spacing:2px">LIVELLO</div>
                <div style="width:80px;height:6px;background:#1a1a2a;border-radius:3px;margin-top:4px;overflow:hidden">
                    <div style="width:{xp_pct}%;height:100%;background:linear-gradient(90deg,#ffd700,#ffec4a);border-radius:3px;transition:width 0.5s"></div>
                </div>
                <div style="font-size:0.5rem;color:#666;margin-top:2px">{xp}/{xp_needed} XP</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#ffd700">🪙 {coins}</div>
                <div style="font-size:0.6rem;color:#888;letter-spacing:2px">MBT COINS</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:{arena_color}">{arena_icon}</div>
                <div style="font-size:0.6rem;color:{arena_color};letter-spacing:1px">{arena_name}</div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Orbitron',sans-serif;font-size:1.2rem;font-weight:900;color:#4ade80">{wins}W</div>
                <div style="font-size:0.6rem;color:#888;letter-spacing:2px">VITTORIE</div>
            </div>
        </div>
    </div>
    """.format(
        level=level, xp_pct=xp_pct, xp=xp, xp_needed=xp_needed, coins=coins,
        arena_color=current_arena["color"], arena_icon=current_arena["icon"],
        arena_name=current_arena["name"], wins=rivals_data["battle_wins"]
    ), unsafe_allow_html=True)

    tabs = st.tabs(["⚔️ Battaglia", "🃏 Collezione", "🛒 Negozio", "🏟️ Arene", "💪 Poteri", "🏅 Draft", "⚙️ Admin"])

    with tabs[0]:
        _render_battle_tab(rivals_data, cards_db, state)
    with tabs[1]:
        _render_collection_tab(rivals_data, cards_db)
    with tabs[2]:
        _render_shop_tab(rivals_data, cards_db)
    with tabs[3]:
        _render_arenas_tab(rivals_data)
    with tabs[4]:
        _render_powers_tab(rivals_data)
    with tabs[5]:
        from mbt_draft import render_draft_tab, load_draft_db, save_draft_db
        draft_db = st.session_state.get("draft_db")
        if draft_db is None:
            draft_db = load_draft_db()
            st.session_state.draft_db = draft_db
        render_draft_tab(rivals_data, cards_db, draft_db)
        save_draft_db(draft_db)
    with tabs[6]:
        _render_admin_tab(state, cards_db, rivals_data)

    # Salva solo se i dati sono cambiati (evita I/O ad ogni rerun)
    _save_if_dirty(rivals_data, cards_db)


# ─── BATTLE TAB ───────────────────────────────────────────────────────────────

def _render_battle_tab(rivals_data, cards_db, state):
    st.markdown("## ⚔️ MBT RIVALS — Battaglia vs CPU")
    battle_state = st.session_state.get("battle_state")

    if battle_state is None:
        active_team_ids = rivals_data.get("active_team", [])
        all_cards = cards_db.get("cards", [])
        team_cards = [c for c in all_cards if c.get("id") in active_team_ids]

        st.markdown("### 🏆 La Tua Squadra Attiva")
        if not team_cards:
            st.warning("⚠️ Nessuna carta nella squadra attiva! Vai in **Collezione** → seleziona fino a 5 carte.")
            return

        cols = st.columns(min(5, len(team_cards)))
        for i, card in enumerate(team_cards[:5]):
            with cols[i]:
                st.markdown(render_card_html(card, size="small"), unsafe_allow_html=True)

        st.markdown("---")
        level = rivals_data["player_level"]
        current_arena = next((a for a in ARENE if a["min_level"] <= level <= a["max_level"]), ARENE[0])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="arena-badge {css}" style="margin-bottom:12px">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-family:'Orbitron',sans-serif;font-weight:700;color:{color};font-size:0.9rem">{name}</div>
                <div style="font-size:0.65rem;color:#888;margin-top:4px">LV.{level} Arena</div>
            </div>
            """.format(
                css=current_arena["css"], icon=current_arena["icon"],
                color=current_arena["color"], name=current_arena["name"], level=level
            ), unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background:#10101e;border:1px solid #1e1e3a;border-radius:10px;padding:16px;text-align:center">
                <div style="font-size:1.5rem">🤖</div>
                <div style="font-family:'Orbitron',sans-serif;color:#dc2626;font-weight:700">CPU LV.{lvl}</div>
                <div style="font-size:0.65rem;color:#888">Difficoltà proporzionale al tuo livello</div>
            </div>
            """.format(lvl=level), unsafe_allow_html=True)

        st.markdown("**Ricompense vittoria:** 🪙 +{} Coins | ⭐ +{} XP | 🏆 +{} Trofei".format(
            50 + level * 10, 30 + level * 5, 2 + level))

        if st.button("⚔️ INIZIA BATTAGLIA!", use_container_width=True, type="primary"):
            st.session_state.battle_state = init_battle_state(team_cards[:3], cpu_level=level)
            st.rerun()
    else:
        _render_active_battle(battle_state, rivals_data, cards_db)


def _render_active_battle(battle_state, rivals_data, cards_db):
    phase = battle_state["phase"]

    if phase == "win":
        st.markdown("""
        <div style="text-align:center;padding:30px;background:linear-gradient(135deg,#001a00,#003300);
            border:3px solid #16a34a;border-radius:16px;animation:pulseGlow 1s infinite;color:#16a34a">
            <div style="font-size:3rem">🏆</div>
            <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:#4ade80">VITTORIA!</div>
        </div>
        """, unsafe_allow_html=True)
        level = rivals_data["player_level"]
        xp_gain = 30 + level * 5
        coins_gain = 50 + level * 10
        trofei_gain = 2 + level
        rivals_data["player_xp"] += xp_gain
        rivals_data["mbt_coins"] += coins_gain
        rivals_data["trofei_rivals"] += trofei_gain
        rivals_data["battle_wins"] += 1
        _check_level_up(rivals_data)
        st.success("🎉 +{} XP | +{} Coins | +{} Trofei".format(xp_gain, coins_gain, trofei_gain))
        if st.button("🔄 Nuova Partita", use_container_width=True):
            st.session_state.battle_state = None
            st.rerun()
        return

    if phase == "lose":
        st.markdown("""
        <div style="text-align:center;padding:30px;background:linear-gradient(135deg,#1a0000,#330000);
            border:3px solid #dc2626;border-radius:16px">
            <div style="font-size:3rem">💀</div>
            <div style="font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:#ef4444">SCONFITTA</div>
        </div>
        """, unsafe_allow_html=True)
        rivals_data["battle_losses"] += 1
        xp_gain = 10
        rivals_data["player_xp"] += xp_gain
        rivals_data["mbt_coins"] += 20
        _check_level_up(rivals_data)
        st.info("+{} XP per aver combattuto | +20 Coins".format(xp_gain))
        if st.button("🔄 Riprova", use_container_width=True):
            st.session_state.battle_state = None
            st.rerun()
        return

    # Controlla timer
    elapsed = time.time() - battle_state["start_time"]
    remaining = max(0, battle_state["time_limit"] - elapsed)
    if remaining <= 0:
        battle_state["phase"] = "lose"
        st.rerun()

    p_idx = battle_state["player_active_idx"]
    c_idx = battle_state["cpu_active_idx"]
    p_fighter = battle_state["player_fighters"][p_idx]
    c_fighter = battle_state["cpu_fighters"][c_idx]

    min_r = int(remaining // 60)
    sec_r = int(remaining % 60)

    col_p, col_mid, col_c = st.columns([2, 1, 2])
    with col_p:
        st.markdown("**⚡ {}**".format(p_fighter["card"].get("nome", "Player")))
        hp_pct = int(p_fighter["hp"] / max(1, p_fighter["max_hp"]) * 100)
        hp_class = "danger" if hp_pct < 30 else ""
        st.markdown("""
        <div class="hp-bar-container">
            <div class="hp-bar-fill {cls}" style="width:{pct}%"></div>
        </div>
        <div style="font-size:0.7rem;color:#888;margin-top:2px">HP: {hp}/{max_hp}</div>
        """.format(cls=hp_class, pct=hp_pct, hp=p_fighter["hp"], max_hp=p_fighter["max_hp"]),
            unsafe_allow_html=True)
        sta_pct = int(p_fighter["stamina"])
        st.markdown("""
        <div style="height:8px;background:#1a1a2a;border-radius:4px;overflow:hidden;margin-top:8px">
            <div style="width:{sta}%;height:100%;background:linear-gradient(90deg,#ffd700,#ffec4a);border-radius:4px;transition:width 0.3s"></div>
        </div>
        <div style="font-size:0.6rem;color:#888;margin-top:1px">STAMINA: {sta}%</div>
        """.format(sta=sta_pct), unsafe_allow_html=True)
        st.markdown(render_card_html(p_fighter["card"], size="small", show_special_effects=False), unsafe_allow_html=True)

    with col_mid:
        st.markdown("""
        <div style="text-align:center;padding:20px 0">
            <div style="font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:900;color:#dc2626">VS</div>
            <div style="font-size:0.7rem;color:#888;margin-top:8px">⏱️ {:02d}:{:02d}</div>
            <div style="font-size:0.65rem;color:#ffd700;margin-top:4px">Turno {}</div>
            <div style="font-size:0.6rem;color:#888;margin-top:8px">Carica: {}/10</div>
        </div>
        """.format(min_r, sec_r, battle_state["turn"], battle_state["stamina_charges"]),
            unsafe_allow_html=True)

    with col_c:
        st.markdown("**🤖 {}**".format(c_fighter["card"].get("nome", "CPU")))
        chp_pct = int(c_fighter["hp"] / max(1, c_fighter["max_hp"]) * 100)
        st.markdown("""
        <div class="hp-bar-container">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:5px;transition:width 0.5s"></div>
        </div>
        <div style="font-size:0.7rem;color:#888;margin-top:2px">HP: {hp}/{max_hp}</div>
        """.format(pct=chp_pct, hp=c_fighter["hp"], max_hp=c_fighter["max_hp"]),
            unsafe_allow_html=True)
        st.markdown(render_card_html(c_fighter["card"], size="small", show_special_effects=False), unsafe_allow_html=True)

    st.markdown("#### 🎮 Scegli la tua mossa:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⚡ ATTACCO", key="battle_attack", use_container_width=True):
            process_battle_action(battle_state, "attack", rivals_data)
            st.rerun()
    with col2:
        can_special = p_fighter["stamina"] >= 40
        if st.button("🔥 SUPER {}".format("✓" if can_special else "✗"), key="battle_special",
                     use_container_width=True, disabled=not can_special):
            process_battle_action(battle_state, "special", rivals_data)
            st.rerun()
    with col3:
        if st.button("🛡️ DIFENDI", key="battle_defend", use_container_width=True):
            process_battle_action(battle_state, "defend", rivals_data)
            st.rerun()
    with col4:
        can_final = battle_state["stamina_charges"] >= 10
        charges = battle_state["stamina_charges"]
        if st.button("💥 FINALE {}".format("✓" if can_final else "{}/10".format(charges)),
                     key="battle_final", use_container_width=True, disabled=not can_final):
            process_battle_action(battle_state, "final", rivals_data)
            st.rerun()

    if battle_state["log"]:
        with st.expander("📋 Log Battaglia", expanded=True):
            log_html = '<div class="battle-log">'
            for entry in reversed(battle_state["log"][-8:]):
                log_html += '<div style="padding:2px 0;border-bottom:1px solid #1a1a2a;color:#ccc">{}</div>'.format(entry)
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

    if st.button("🏳️ Abbandona Partita", key="battle_quit"):
        rivals_data["battle_losses"] += 1
        st.session_state.battle_state = None
        st.rerun()


# ─── COLLECTION TAB ───────────────────────────────────────────────────────────

def _render_collection_tab(rivals_data, cards_db):
    st.markdown("## 🃏 La Mia Collezione")
    all_cards = cards_db.get("cards", [])
    owned_ids_set = set(rivals_data.get("collection", []))
    active_team = rivals_data.get("active_team", [])
    active_trainer = rivals_data.get("active_trainer", "")

    if not owned_ids_set and all_cards:
        st.info("💡 La tua collezione cresce acquistando pacchetti! Anteprima di tutte le carte disponibili.")
        owned_cards = all_cards
    else:
        owned_cards = [c for c in all_cards if c.get("id") in owned_ids_set]

    if not owned_cards:
        st.warning("📦 Nessuna carta! Vai nel **Negozio** per acquistare pacchetti.")
        return

    # ── Filtri ──────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        tier_filter = st.selectbox("🔍 Filtra Rarità", ["Tutte"] + list(CARD_TIERS.keys()), key="coll_tier_f")
    with col_f2:
        role_opts = ["Tutti"] + ROLES
        role_filter = st.selectbox("🎭 Filtra Ruolo", role_opts, key="coll_role_f")
    with col_f3:
        search_name = st.text_input("🔎 Cerca", key="coll_search", placeholder="Nome…")

    filtered = owned_cards
    if tier_filter != "Tutte":
        filtered = [c for c in filtered if get_tier_by_ovr(c.get("overall", 40)) == tier_filter]
    if role_filter != "Tutti":
        filtered = [c for c in filtered if c.get("ruolo", "") == role_filter]
    if search_name:
        q = search_name.lower()
        filtered = [c for c in filtered if q in c.get("nome","").lower() or q in c.get("cognome","").lower()]

    st.caption("📊 Totale collezione: {} | Mostrate: {}".format(len(owned_cards), len(filtered)))

    # ── Squadra Attiva ───────────────────────────────────────────────────────
    st.markdown("### 👥 Squadra Attiva")

    with st.expander("⚡ Gestisci Giocatori (max 5)", expanded=True):
        if active_team:
            st.caption("Squadra attuale — clicca per rimuovere:")
            team_cards_live = [c for c in all_cards if c.get("id") in active_team]
            tc_cols = st.columns(min(5, max(1, len(team_cards_live))))
            for i, card in enumerate(team_cards_live[:5]):
                with tc_cols[i]:
                    st.markdown(render_card_html(card, size="small"), unsafe_allow_html=True)
                    cid = card.get("id", "")
                    if st.button("❌ Rimuovi", key="rm_at_{}".format(cid[:8]), use_container_width=True):
                        active_team = [x for x in active_team if x != cid]
                        rivals_data["active_team"] = active_team
                        save_rivals_data(rivals_data)
                        st.rerun()
        else:
            st.info("Nessun giocatore in squadra. Aggiungine dalla lista qui sotto.")

    with st.expander("🧑\u200d🏫 Slot TRAINER (1 carta speciale)", expanded=True):
        trainer_cards = [c for c in owned_cards if _is_trainer(c)]
        if active_trainer:
            tr_card = next((c for c in all_cards if c.get("id") == active_trainer), None)
            if tr_card:
                tr_col1, tr_col2 = st.columns([1, 3])
                with tr_col1:
                    st.markdown(render_card_html(tr_card, size="small"), unsafe_allow_html=True)
                with tr_col2:
                    role = tr_card.get("ruolo", "")
                    desc = ROLE_DESCRIPTIONS.get(role, "")
                    st.markdown("**{}** {}".format(tr_card.get("nome", ""), tr_card.get("cognome", "")))
                    st.caption("{} | {}".format(role, desc))
                    if st.button("❌ Rimuovi Trainer", key="rm_trainer"):
                        rivals_data["active_trainer"] = ""
                        save_rivals_data(rivals_data)
                        st.rerun()
        else:
            st.info("Nessun Trainer attivo.")
            if trainer_cards:
                tr_opts = ["-- Nessuno --"] + ["{} {} ({})".format(
                    c.get("nome",""), c.get("cognome",""), c.get("ruolo","")) for c in trainer_cards]
                sel_tr = st.selectbox("Scegli Trainer", options=tr_opts, key="sel_trainer_dd")
                if sel_tr != "-- Nessuno --" and st.button("✅ Assegna Trainer", key="assign_trainer"):
                    idx = ["{} {} ({})".format(c.get("nome",""), c.get("cognome",""), c.get("ruolo",""))
                           for c in trainer_cards].index(sel_tr)
                    rivals_data["active_trainer"] = trainer_cards[idx].get("id", "")
                    save_rivals_data(rivals_data)
                    st.rerun()
            else:
                st.caption("Crea una carta Trainer nell'Admin per usare questo slot.")

    st.markdown("---")

    # ── Lista carte con paginazione (gestisce migliaia di carte) ────────────
    st.markdown("### 🗂️ Tutte le Carte")

    PAGE_SIZE = 20
    page_key = "coll_page"
    if st.session_state.get("_coll_filter_prev") != (tier_filter, role_filter, search_name):
        st.session_state[page_key] = 0
        st.session_state["_coll_filter_prev"] = (tier_filter, role_filter, search_name)

    current_page = st.session_state.get(page_key, 0)
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = min(current_page, total_pages - 1)
    page_start = current_page * PAGE_SIZE
    page_cards = filtered[page_start: page_start + PAGE_SIZE]

    if total_pages > 1:
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("◀ Prec.", disabled=current_page == 0, key="coll_prev"):
                st.session_state[page_key] = current_page - 1
                st.rerun()
        with pcol2:
            st.markdown(
                '<div style="text-align:center;font-size:.75rem;color:#888;padding-top:6px">'
                'Pagina {} / {} ({} carte)</div>'.format(current_page + 1, total_pages, len(filtered)),
                unsafe_allow_html=True)
        with pcol3:
            if st.button("Succ. ▶", disabled=current_page >= total_pages - 1, key="coll_next"):
                st.session_state[page_key] = current_page + 1
                st.rerun()

    rarity_groups = {}
    for card in page_cards:
        tier = get_tier_by_ovr(card.get("overall", 40))
        rarity_groups.setdefault(tier, []).append(card)

    for tier_name in reversed(list(CARD_TIERS.keys())):
        if tier_name not in rarity_groups:
            continue
        tier_cards_pg = rarity_groups[tier_name]
        tier_info = CARD_TIERS[tier_name]
        with st.expander("{} ({} carte)".format(tier_name, len(tier_cards_pg)),
                         expanded=tier_info["rarity"] >= 12):
            cols_per_row = 5
            for i in range(0, len(tier_cards_pg), cols_per_row):
                chunk = tier_cards_pg[i:i + cols_per_row]
                row_cols = st.columns(cols_per_row)
                for j, card in enumerate(chunk):
                    with row_cols[j]:
                        st.markdown(render_card_html(card, size="small"), unsafe_allow_html=True)
                        card_id = card.get("id", "")
                        is_active = card_id in active_team
                        is_trainer_card = _is_trainer(card)
                        st.caption("OVR {} | {}".format(card.get("overall", 40), card.get("ruolo", "")[:10]))
                        if is_trainer_card:
                            if card_id == active_trainer:
                                st.markdown('<div style="text-align:center;font-size:.55rem;color:#ffd700">🧑‍🏫 TRAINER ATTIVO</div>', unsafe_allow_html=True)
                            else:
                                if st.button("🧑‍🏫 Trainer", key="set_tr_{}_{}".format(j, card_id[:8]), use_container_width=True):
                                    rivals_data["active_trainer"] = card_id
                                    save_rivals_data(rivals_data)
                                    st.rerun()
                        else:
                            if is_active:
                                if st.button("✅ Squadra", key="rm2_{}_{}_{}".format(i, j, card_id[:8]), use_container_width=True):
                                    active_team = [x for x in active_team if x != card_id]
                                    rivals_data["active_team"] = active_team
                                    save_rivals_data(rivals_data)
                                    st.rerun()
                            else:
                                if st.button("➕ Aggiungi", key="add2_{}_{}_{}".format(i, j, card_id[:8]),
                                             disabled=len(active_team) >= 5, use_container_width=True):
                                    active_team.append(card_id)
                                    rivals_data["active_team"] = active_team
                                    save_rivals_data(rivals_data)
                                    st.rerun()


# ─── SHOP TAB ─────────────────────────────────────────────────────────────────

def _render_shop_tab(rivals_data, cards_db):
    st.markdown("## 🛒 Negozio Pacchetti")
    coins = rivals_data.get("mbt_coins", 0)
    st.markdown("""
    <div style="text-align:right;margin-bottom:20px">
        <span style="font-family:'Orbitron',sans-serif;font-size:1.2rem;color:#ffd700;font-weight:700">
            🪙 {} MBT Coins
        </span>
    </div>
    """.format(coins), unsafe_allow_html=True)

    pack_cols = st.columns(3)
    pack_names = ["Base", "Epico", "Leggenda"]
    pack_emojis = {"Base": "🟫", "Epico": "💜", "Leggenda": "🔥"}
    pack_descs = {
        "Base": "Perfetto per iniziare. Carte Bronzo, Argento e raramente Oro.",
        "Epico": "Alta probabilità di Oro ed Eroi. Chance di Leggenda e TOTY!",
        "Leggenda": "Solo carte di alto livello. Garantisce almeno una Leggenda!",
    }

    for i, pack_name in enumerate(pack_names):
        pack_info = PACKS[pack_name]
        with pack_cols[i]:
            color = pack_info["label_color"]
            can_afford = coins >= pack_info["price"]
            st.markdown("""
            <div class="pack-card {css}" style="width:100%;height:220px;border-radius:16px;
                position:relative;overflow:hidden;display:flex;flex-direction:column;
                align-items:center;justify-content:center;margin-bottom:8px">
                <div style="font-size:3rem;z-index:2">{emoji}</div>
                <div style="font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:900;
                    color:{color};z-index:2;letter-spacing:3px;text-transform:uppercase">{name}</div>
                <div style="font-size:0.65rem;color:#888;z-index:2;text-align:center;padding:0 10px;margin-top:4px">
                    {desc}
                </div>
                <div style="font-family:'Orbitron',sans-serif;font-size:1rem;font-weight:700;
                    color:#ffd700;z-index:2;margin-top:8px">🪙 {price}</div>
            </div>
            """.format(
                css=pack_info["css_class"], emoji=pack_emojis[pack_name],
                color=color, name=pack_name, desc=pack_descs[pack_name],
                price=pack_info["price"]
            ), unsafe_allow_html=True)

            if st.button(
                "🛒 Acquista {}".format(pack_name) if can_afford else "🔒 Coins insufficienti",
                key="buy_pack_{}".format(pack_name),
                use_container_width=True,
                disabled=not can_afford
            ):
                st.session_state["opening_pack"] = pack_name
                rivals_data["mbt_coins"] -= pack_info["price"]
                drawn = draw_cards_from_pack(pack_name, cards_db)
                st.session_state["drawn_cards"] = drawn
                for card in drawn:
                    cid = card.get("id", card.get("instance_id", ""))
                    if cid:
                        rivals_data["collection"].append(cid)
                st.rerun()

    if st.session_state.get("drawn_cards"):
        pack_name_opened = st.session_state.get("opening_pack", "Base")
        drawn = st.session_state["drawn_cards"]
        st.markdown("---")
        max_rarity = max(
            CARD_TIERS.get(get_tier_by_ovr(c.get("overall", 40)), {}).get("rarity", 0)
            for c in drawn
        )
        if max_rarity >= 12:
            st.markdown("""
            <div style="text-align:center;animation:screenShake 0.5s infinite;background:rgba(255,215,0,0.1);
                border:2px solid #ffd700;border-radius:10px;padding:10px;margin-bottom:10px">
                <span style="font-family:'Orbitron',sans-serif;font-size:1rem;color:#ffd700;
                    animation:goldShine 1s infinite">⚡💥 CARTA ICONA! 💥⚡</span>
            </div>
            """, unsafe_allow_html=True)
        elif max_rarity >= 8:
            st.markdown("""
            <div style="text-align:center;background:rgba(255,255,255,0.05);
                border:2px solid #ffffff;border-radius:10px;padding:8px;margin-bottom:10px">
                <span style="font-family:'Orbitron',sans-serif;font-size:0.9rem;color:#fff">
                    ✨ CARTA LEGGENDARIA O SUPERIORE! ✨
                </span>
            </div>
            """, unsafe_allow_html=True)

        render_pack_opening_animation(drawn, pack_name_opened)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ Tieni tutte e Continua", use_container_width=True, type="primary"):
                st.session_state["drawn_cards"] = None
                st.session_state["opening_pack"] = None
                st.rerun()
        with col_btn2:
            if st.button("🔄 Apri un altro pacchetto", use_container_width=True):
                st.session_state["drawn_cards"] = None
                st.session_state["opening_pack"] = None
                st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Mosse Speciali")
    st.caption("Insegna mosse speciali alle tue carte spendendo MBT Coins")
    learned = rivals_data.get("special_moves_learned", [])
    move_cols = st.columns(3)
    for i, move in enumerate(SPECIAL_MOVES[:9]):
        with move_cols[i % 3]:
            already_learned = move["id"] in learned
            role_tag = "[{}]".format(move["role"]) if move.get("role") else "[Universale]"
            can_afford_move = coins >= move["cost_coins"]
            border_color = "#ffd700" if already_learned else "#1e1e3a"
            name_color = "#ffd700" if already_learned else "#ccc"
            price_label = "✅ Appresa" if already_learned else "🪙 {} Coins".format(move["cost_coins"])
            st.markdown("""
            <div style="background:#10101e;border:1px solid {bc};border-radius:8px;padding:10px;margin-bottom:8px;min-height:100px">
                <div style="font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:700;color:{nc}">{name}</div>
                <div style="font-size:0.55rem;color:#666;margin:4px 0">{rt}</div>
                <div style="font-size:0.6rem;color:#888">{desc}</div>
                <div style="font-size:0.6rem;color:#ffd700;margin-top:4px">{pl}</div>
            </div>
            """.format(bc=border_color, nc=name_color, name=move["name"],
                       rt=role_tag, desc=move["desc"], pl=price_label),
                unsafe_allow_html=True)
            if not already_learned:
                if st.button("Apprendi", key="learn_{}".format(move["id"]),
                             disabled=not can_afford_move, use_container_width=True):
                    rivals_data["special_moves_learned"].append(move["id"])
                    rivals_data["mbt_coins"] -= move["cost_coins"]
                    st.rerun()


# ─── ARENAS TAB ───────────────────────────────────────────────────────────────

def _render_arenas_tab(rivals_data):
    st.markdown("## 🏟️ Sistema Arene")
    st.caption("Avanza di livello per sbloccare arene sempre più epiche!")
    level = rivals_data["player_level"]
    for arena in ARENE:
        is_unlocked = level >= arena["min_level"]
        is_current = arena["min_level"] <= level <= arena["max_level"]
        col1, col2 = st.columns([1, 3])
        with col1:
            opacity_style = "opacity:0.4;filter:grayscale(80%)" if not is_unlocked else ""
            st.markdown("""
            <div class="arena-badge {css}" style="{op}">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-family:'Orbitron',sans-serif;font-size:0.65rem;font-weight:700;color:{color}">
                    LV.{min_lv}-{max_lv}
                </div>
            </div>
            """.format(
                css=arena["css"] if is_unlocked else "arena-badge",
                op=opacity_style,
                icon=arena["icon"] if is_unlocked else "🔒",
                color=arena["color"] if is_unlocked else "#555",
                min_lv=arena["min_level"], max_lv=arena["max_level"]
            ), unsafe_allow_html=True)
        with col2:
            badge = " 🔴 ATTUALE" if is_current else (" ✅ SBLOCCATA" if is_unlocked else " 🔒")
            current_extra = (
                '<div style="font-size:0.65rem;color:#ffd700;margin-top:4px">'
                '⚡ Combatti qui per guadagnare ricompense speciali!</div>'
            ) if is_current else ""
            st.markdown("""
            <div style="padding:12px 0">
                <div style="font-family:'Orbitron',sans-serif;font-weight:700;color:{color};font-size:0.9rem">
                    {name}{badge}
                </div>
                <div style="font-size:0.7rem;color:#666;margin-top:4px">Livelli {min_lv} – {max_lv}</div>
                {extra}
            </div>
            """.format(
                color=arena["color"] if is_unlocked else "#555",
                name=arena["name"], badge=badge,
                min_lv=arena["min_level"], max_lv=arena["max_level"],
                extra=current_extra
            ), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>", unsafe_allow_html=True)


# ─── POWERS TAB ───────────────────────────────────────────────────────────────

def _render_powers_tab(rivals_data):
    st.markdown("## 💪 Super Poteri")
    st.caption("Potenzia i tuoi super poteri spendendo MBT Coins")
    coins = rivals_data.get("mbt_coins", 0)
    superpowers = rivals_data.setdefault("superpowers", {})
    for power in SUPERPOWERS:
        current_level = superpowers.get(power["id"], 0)
        max_level = power["max_level"]
        cost = power["cost_per_level"]
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            bars = "█" * current_level + "░" * (max_level - current_level)
            st.markdown("""
            <div style="background:#10101e;border:1px solid #1e1e3a;border-radius:8px;padding:12px;margin-bottom:8px">
                <div style="font-family:'Orbitron',sans-serif;font-size:0.8rem;font-weight:700;color:#ffd700">
                    {name} <span style="font-size:0.65rem;color:#888">LV.{cur}/{max}</span>
                </div>
                <div style="font-size:0.65rem;color:#888;margin:4px 0">{desc}</div>
                <div style="font-size:1rem;color:#ffd700;letter-spacing:2px">{bars}</div>
            </div>
            """.format(name=power["name"], cur=current_level, max=max_level,
                       desc=power["desc"], bars=bars), unsafe_allow_html=True)
        with col2:
            if current_level < max_level:
                st.metric("Costo", "🪙 {}".format(cost))
        with col3:
            if current_level < max_level:
                can_up = coins >= cost
                if st.button("⬆️ Potenzia", key="up_power_{}".format(power["id"]),
                             disabled=not can_up, use_container_width=True):
                    superpowers[power["id"]] = current_level + 1
                    rivals_data["mbt_coins"] -= cost
                    st.rerun()
            else:
                st.markdown('<div style="color:#ffd700;text-align:center;padding:20px 0">✅ MAX</div>',
                            unsafe_allow_html=True)


# ─── ANIMATION CATALOG (35 effetti) ──────────────────────────────────────────

ANIMATION_CATALOG = {
    "✨ Shimmer & Shine": {
        "shimmer_gold":       ("Shimmer Oro",        "Riflesso dorato scorrevole"),
        "shimmer_silver":     ("Shimmer Argento",     "Riflesso argentato scorrevole"),
        "shimmer_rainbow":    ("Shimmer Arcobaleno",  "Riflesso iridescente"),
        "glass_shine":        ("Glass Shine",         "Effetto vetro lucido con bagliore"),
        "holographic":        ("Olografico",          "Sheen olografico continuo"),
    },
    "🔥 Fire & Energy": {
        "fire_bottom":        ("Fuoco Base",          "Fiamme dal basso animate"),
        "fire_intense":       ("Fuoco Intenso",       "Fiamme alte con fulmini"),
        "lightning":          ("Fulmini",             "Lampi elettrici sulla carta"),
        "plasma_edge":        ("Plasma Edge",         "Bordo al plasma pulsante"),
        "energy_burst":       ("Energy Burst",        "Esplosione di energia centrale"),
    },
    "🌌 Nebula & Space": {
        "nebula_purple":      ("Nebulosa Viola",      "Vortice cosmico viola"),
        "nebula_gold":        ("Nebulosa Dorata",     "Orbe luminosa dorata fluttuante"),
        "nebula_blue":        ("Nebulosa Blu",        "Galassia blu rotante"),
        "stars_drift":        ("Stelle Fluttuanti",   "Particelle stellari vaganti"),
        "cosmic_beam":        ("Raggio Cosmico",      "Beam conico rotante"),
    },
    "💎 Particles & Dust": {
        "particles_gold":     ("Particelle Oro",      "Polvere dorata che sale"),
        "particles_blue":     ("Particelle Blu",      "Cristalli blu fluttuanti"),
        "particles_white":    ("Particelle Bianche",  "Scintille bianche"),
        "particles_fire":     ("Particelle Fuoco",    "Braci arancioni che salgono"),
        "particles_purple":   ("Particelle Viola",    "Polvere viola magica"),
    },
    "🪞 Overlays & Glass": {
        "glassmorphism":      ("Glassmorphism",       "Overlay vetro con blur"),
        "dark_vignette":      ("Vignette Scura",      "Bordi scuri profondi"),
        "color_overlay_red":  ("Overlay Rosso",       "Tinta rossa sulla carta"),
        "color_overlay_gold": ("Overlay Oro",         "Tinta dorata sulla carta"),
        "scanlines":          ("Scanlines",           "Linee orizzontali stile CRT"),
    },
    "⚡ Borders & Glow": {
        "glow_pulse_gold":    ("Pulse Oro",           "Bordo oro pulsante"),
        "glow_pulse_red":     ("Pulse Rosso",         "Bordo rosso infuocato"),
        "glow_pulse_blue":    ("Pulse Blu",           "Bordo blu elettrico"),
        "glow_pulse_white":   ("Pulse Bianco",        "Bordo bianco divino"),
        "rainbow_border":     ("Bordo Arcobaleno",    "Bordo che cambia colore"),
    },
    "🎭 Hover Effects": {
        "hover_zoom":         ("Zoom Hover",          "Zoom al passaggio mouse"),
        "hover_tilt_3d":      ("Tilt 3D",             "Inclinazione 3D al hover"),
        "hover_glow_color":   ("Glow Colorato Hover", "Bagliore colorato al hover"),
        "hover_crack":        ("Crack Reveal",        "Crepe luminose al hover"),
        "hover_shadow_epic":  ("Ombra Epica Hover",   "Ombra drammatica al hover"),
    },
}

@st.cache_data(show_spinner=False)
def build_custom_animation_css(anim_ids: tuple, card_color: str = "#ffd700"):
    """Genera CSS/HTML per le animazioni selezionate dall'editor."""
    css_parts = []
    html_layers = []
    c = card_color

    for anim_id in anim_ids:
        if anim_id == "shimmer_gold":
            html_layers.append(
                '<div style="position:absolute;top:0;left:-80%;width:40%;height:100%;'
                'background:linear-gradient(105deg,transparent,rgba(255,215,0,0.28),transparent);'
                'animation:shimmer 2s infinite;transform:skewX(-15deg);pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "shimmer_silver":
            html_layers.append(
                '<div style="position:absolute;top:0;left:-80%;width:40%;height:100%;'
                'background:linear-gradient(105deg,transparent,rgba(220,220,255,0.3),transparent);'
                'animation:shimmer 2.5s infinite;transform:skewX(-15deg);pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "shimmer_rainbow":
            css_parts.append(
                '@keyframes rainbowShimmer{0%{background-position:0% center}100%{background-position:400% center}}'
            )
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:linear-gradient(105deg,transparent 35%,rgba(255,0,128,0.18) 40%,'
                'rgba(255,200,0,0.18) 45%,rgba(0,255,200,0.18) 50%,rgba(100,100,255,0.18) 55%,transparent 60%);'
                'background-size:400% 100%;animation:rainbowShimmer 3s linear infinite;'
                'pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "glass_shine":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:linear-gradient(135deg,rgba(255,255,255,0.12) 0%,transparent 40%,rgba(255,255,255,0.06) 100%);'
                'pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "holographic":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,0.14) 50%,transparent 70%);'
                'background-size:200% 200%;animation:holographic 2.5s infinite;pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "fire_bottom":
            html_layers.append(
                '<div style="position:absolute;bottom:0;left:0;right:0;height:35%;border-radius:0 0 14px 14px;'
                'background:linear-gradient(0deg,rgba(255,60,0,0.55),rgba(255,120,0,0.25),transparent);'
                'animation:fireFlicker 0.5s infinite alternate;pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "fire_intense":
            html_layers.append(
                '<div style="position:absolute;bottom:0;left:0;right:0;height:50%;'
                'background:linear-gradient(0deg,rgba(255,40,0,0.65),rgba(255,100,0,0.3),rgba(255,200,0,0.1),transparent);'
                'animation:fireFlicker 0.35s infinite alternate;pointer-events:none;z-index:6"></div>'
                '<div style="position:absolute;top:10%;left:46%;width:3px;height:75%;'
                'background:linear-gradient(180deg,rgba(255,255,100,0.9),transparent);'
                'transform:rotate(6deg);animation:lightningFlash 1.1s infinite;box-shadow:0 0 8px #ffff00;'
                'pointer-events:none;z-index:7"></div>'
            )
        elif anim_id == "lightning":
            html_layers.append(
                '<div style="position:absolute;top:5%;left:44%;width:2px;height:80%;'
                'background:linear-gradient(180deg,rgba(255,255,255,0.95),rgba(100,180,255,0.6),transparent);'
                'transform:rotate(5deg);animation:lightningFlash 1.4s infinite;box-shadow:0 0 10px #aaddff;'
                'pointer-events:none;z-index:7"></div>'
                '<div style="position:absolute;top:15%;left:25%;width:2px;height:55%;'
                'background:linear-gradient(180deg,rgba(200,200,255,0.8),transparent);'
                'transform:rotate(-12deg);animation:lightningFlash 1.9s 0.4s infinite;box-shadow:0 0 6px #8888ff;'
                'pointer-events:none;z-index:7"></div>'
            )
        elif anim_id == "plasma_edge":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'box-shadow:0 0 15px {c},0 0 30px {c}88,inset 0 0 15px {c}33;'
                'animation:pulseGlow 1.8s infinite;pointer-events:none;z-index:6"></div>'.format(c=c)
            )
        elif anim_id == "energy_burst":
            css_parts.append(
                '@keyframes energyBurst{0%,100%{transform:scale(0.8);opacity:0.3}'
                '50%{transform:scale(1.2);opacity:0.9}}'
            )
            html_layers.append(
                '<div style="position:absolute;top:20%;left:50%;transform:translateX(-50%);'
                'width:60%;height:45%;border-radius:50%;'
                'background:radial-gradient(ellipse at center,{c}44 0%,{c}22 40%,transparent 70%);'
                'animation:energyBurst 2s ease-in-out infinite;pointer-events:none;z-index:6"></div>'.format(c=c)
            )
        elif anim_id == "nebula_purple":
            html_layers.append(
                '<div style="position:absolute;inset:-30px;border-radius:50%;'
                'background:conic-gradient(from 0deg,transparent,rgba(155,0,255,0.2),transparent,rgba(100,0,200,0.15),transparent);'
                'animation:nebulaSwirl 5s linear infinite;pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "nebula_gold":
            html_layers.append(
                '<div style="position:absolute;top:-15%;left:-10%;width:70%;height:70%;'
                'background:radial-gradient(ellipse at center,rgba(255,215,0,0.22) 0%,transparent 65%);'
                'animation:nebulaFloat 6s ease-in-out infinite;pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "nebula_blue":
            html_layers.append(
                '<div style="position:absolute;inset:-25px;border-radius:50%;'
                'background:conic-gradient(from 0deg,transparent,rgba(65,105,225,0.22),transparent,rgba(100,180,255,0.15),transparent);'
                'animation:beamRotate 6s linear infinite;pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "stars_drift":
            stars = ""
            for _ in range(8):
                dx = random.randint(-20, 20)
                dy = random.randint(-45, -10)
                delay = random.uniform(0, 3)
                dur = random.uniform(2, 4)
                stars += (
                    '<div style="position:absolute;width:2px;height:2px;background:white;border-radius:50%;'
                    'top:{top}%;left:{left}%;animation:driftParticle {dur}s {delay}s infinite;'
                    '--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 4px white;pointer-events:none;z-index:7"></div>'
                ).format(top=random.randint(10,80), left=random.randint(5,90), dur=dur, delay=delay, dx=dx, dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + stars + '</div>')
        elif anim_id == "cosmic_beam":
            html_layers.append(
                '<div style="position:absolute;inset:-35px;border-radius:50%;'
                'background:conic-gradient(from 0deg,transparent 0deg,{c}33 25deg,transparent 50deg);'
                'animation:beamRotate 3.5s linear infinite;pointer-events:none;z-index:6"></div>'.format(c=c)
            )
        elif anim_id == "particles_gold":
            pts = ""
            for _ in range(7):
                dx, dy = random.randint(-20,20), random.randint(-50,-12)
                delay, dur = random.uniform(0,2.5), random.uniform(1.5,3)
                pts += '<div style="position:absolute;width:3px;height:3px;background:#ffd700;border-radius:50%;top:{t}%;left:{l}%;animation:driftParticle {d}s {dl}s infinite;--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 5px #ffd700;z-index:7;pointer-events:none"></div>'.format(t=random.randint(20,80),l=random.randint(10,90),d=dur,dl=delay,dx=dx,dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + pts + '</div>')
        elif anim_id == "particles_blue":
            pts = ""
            for _ in range(7):
                dx, dy = random.randint(-20,20), random.randint(-50,-12)
                delay, dur = random.uniform(0,2.5), random.uniform(1.5,3)
                pts += '<div style="position:absolute;width:3px;height:3px;background:#4169e1;border-radius:50%;top:{t}%;left:{l}%;animation:driftParticle {d}s {dl}s infinite;--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 6px #4169e1;z-index:7;pointer-events:none"></div>'.format(t=random.randint(20,80),l=random.randint(10,90),d=dur,dl=delay,dx=dx,dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + pts + '</div>')
        elif anim_id == "particles_white":
            pts = ""
            for _ in range(8):
                dx, dy = random.randint(-15,15), random.randint(-45,-8)
                delay, dur = random.uniform(0,3), random.uniform(2,4)
                pts += '<div style="position:absolute;width:2px;height:2px;background:white;border-radius:50%;top:{t}%;left:{l}%;animation:driftParticle {d}s {dl}s infinite;--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 5px white;z-index:7;pointer-events:none"></div>'.format(t=random.randint(15,80),l=random.randint(10,90),d=dur,dl=delay,dx=dx,dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + pts + '</div>')
        elif anim_id == "particles_fire":
            pts = ""
            for _ in range(6):
                dx, dy = random.randint(-12,12), random.randint(-40,-10)
                delay, dur = random.uniform(0,2), random.uniform(1.2,2.5)
                pts += '<div style="position:absolute;width:3px;height:3px;background:#ff6600;border-radius:50%;bottom:{b}%;left:{l}%;animation:driftParticle {d}s {dl}s infinite;--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 6px #ff4400;z-index:7;pointer-events:none"></div>'.format(b=random.randint(5,30),l=random.randint(15,85),d=dur,dl=delay,dx=dx,dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + pts + '</div>')
        elif anim_id == "particles_purple":
            pts = ""
            for _ in range(7):
                dx, dy = random.randint(-18,18), random.randint(-48,-10)
                delay, dur = random.uniform(0,3), random.uniform(1.8,3.5)
                pts += '<div style="position:absolute;width:3px;height:3px;background:#cc44ff;border-radius:50%;top:{t}%;left:{l}%;animation:driftParticle {d}s {dl}s infinite;--dx:{dx}px;--dy:{dy}px;box-shadow:0 0 6px #cc44ff;z-index:7;pointer-events:none"></div>'.format(t=random.randint(20,75),l=random.randint(10,90),d=dur,dl=delay,dx=dx,dy=dy)
            html_layers.append('<div style="position:absolute;inset:0;overflow:hidden;border-radius:14px;pointer-events:none;z-index:6">' + pts + '</div>')
        elif anim_id == "glassmorphism":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:rgba(255,255,255,0.06);backdrop-filter:blur(2px);'
                'border:1px solid rgba(255,255,255,0.12);pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "dark_vignette":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:radial-gradient(ellipse at center,transparent 40%,rgba(0,0,0,0.6) 100%);'
                'pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "color_overlay_red":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:rgba(180,0,0,0.18);pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "color_overlay_gold":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;'
                'background:rgba(200,160,0,0.16);pointer-events:none;z-index:6"></div>'
            )
        elif anim_id == "scanlines":
            css_parts.append(
                '@keyframes scanMove{0%{background-position:0 0}100%{background-position:0 20px}}'
            )
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;overflow:hidden;pointer-events:none;z-index:8;">'
                '<div style="position:absolute;inset:0;background:repeating-linear-gradient('
                '0deg,transparent,transparent 3px,rgba(0,0,0,0.12) 3px,rgba(0,0,0,0.12) 4px);'
                'animation:scanMove 0.5s linear infinite"></div></div>'
            )
        elif anim_id == "glow_pulse_gold":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;border:2px solid #ffd700;'
                'box-shadow:0 0 15px #ffd700,0 0 30px #ffd70066;animation:pulseGlow 2s infinite;'
                'color:#ffd700;pointer-events:none;z-index:9"></div>'
            )
        elif anim_id == "glow_pulse_red":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;border:2px solid #ff2200;'
                'box-shadow:0 0 15px #ff2200,0 0 35px #ff220066;animation:iconGodPulse 1.8s infinite;'
                'pointer-events:none;z-index:9"></div>'
            )
        elif anim_id == "glow_pulse_blue":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;border:2px solid #4169e1;'
                'box-shadow:0 0 15px #4169e1,0 0 35px #4169e166;animation:pulseGlow 2s infinite;'
                'color:#4169e1;pointer-events:none;z-index:9"></div>'
            )
        elif anim_id == "glow_pulse_white":
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;border:2px solid #ffffff;'
                'box-shadow:0 0 20px #ffffff99,0 0 40px #ffffff44;animation:pulseGlow 2.5s infinite;'
                'color:white;pointer-events:none;z-index:9"></div>'
            )
        elif anim_id == "rainbow_border":
            css_parts.append(
                '@keyframes rbBorder{0%{border-color:#ff0000}16%{border-color:#ff8800}'
                '33%{border-color:#ffff00}50%{border-color:#00ff88}'
                '66%{border-color:#0088ff}83%{border-color:#8800ff}100%{border-color:#ff0000}}'
            )
            html_layers.append(
                '<div style="position:absolute;inset:0;border-radius:14px;border:3px solid #ff0000;'
                'animation:rbBorder 2s linear infinite;pointer-events:none;z-index:9"></div>'
            )
        elif anim_id == "hover_zoom":
            css_parts.append(
                '.mbt-card-wrap:hover .card-custom-hover-zoom{transform:scale(1.04)!important;}'
            )
            html_layers.append('<div class="card-custom-hover-zoom" style="position:absolute;inset:0;z-index:0;transition:transform 0.3s;pointer-events:none"></div>')
        elif anim_id == "hover_tilt_3d":
            css_parts.append(
                '.mbt-card-wrap:hover{transform:translateY(-14px) scale(1.08) rotateX(6deg) rotateY(-4deg)!important;}'
            )
        elif anim_id == "hover_glow_color":
            css_parts.append(
                '.mbt-card-wrap:hover .card-hover-glow{{opacity:1!important;}}'
            )
            html_layers.append(
                '<div class="card-hover-glow" style="position:absolute;inset:0;border-radius:14px;'
                'background:radial-gradient(ellipse at 50% 25%,{c}33 0%,transparent 70%);'
                'opacity:0;transition:opacity 0.35s;pointer-events:none;z-index:22"></div>'.format(c=c)
            )
        elif anim_id == "hover_crack":
            css_parts.append(
                '.mbt-card-wrap:hover .card-crack-svg{{opacity:1!important;}}'
            )
            html_layers.append(
                '<svg class="card-crack-svg" style="position:absolute;inset:0;width:100%;height:100%;'
                'opacity:0;transition:opacity 0.4s;z-index:20;pointer-events:none" viewBox="0 0 140 200">'
                '<path d="M30,50 L90,90 L50,130 L110,170" stroke="{c}" stroke-width="1.5" fill="none" '
                'stroke-dasharray="8,4" style="animation:cracksAnimate 2s infinite"/>'
                '<path d="M100,30 L60,80 L115,120" stroke="{c}" stroke-width="1" fill="none" '
                'stroke-dasharray="6,3" style="animation:cracksAnimate 2.5s 0.5s infinite"/>'
                '</svg>'.format(c=c)
            )
        elif anim_id == "hover_shadow_epic":
            css_parts.append(
                '.mbt-card-wrap:hover{{filter:drop-shadow(0 30px 60px {c}99) drop-shadow(0 0 20px {c}44)!important;}}'.format(c=c)
            )

    custom_css = "<style>" + "\n".join(css_parts) + "</style>" if css_parts else ""
    overlay_html = "\n".join(html_layers)
    return custom_css, overlay_html


def _file_to_b64(file_obj):
    """Converte un file uploader object in base64."""
    if file_obj is None:
        return None, None
    data = file_obj.read()
    b64 = base64.b64encode(data).decode()
    ext = file_obj.name.rsplit(".", 1)[-1].lower()
    mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg",
            "webp":"image/webp","gif":"image/gif"}.get(ext, "image/png")
    return b64, mime


def render_card_html_custom(card_data, card_png_b64=None, card_png_mime="image/png",
                             foto_b64=None, foto_mime="image/jpeg",
                             custom_anim_css="", custom_anim_overlay="",
                             size="normal", show_special_effects=True):
    """
    Versione avanzata di render_card_html che supporta:
    - PNG carta personalizzato (card_png_b64) invece del tier default
    - Foto giocatore come b64 invece di path
    - Animazioni custom dall'editor
    """
    ovr = card_data.get("overall", 40)
    tier_name = get_tier_by_ovr(ovr)
    tier_info = CARD_TIERS.get(tier_name, CARD_TIERS["Bronzo Comune"])
    color = tier_info["color"]
    rarity = tier_info.get("rarity", 0)
    nome = card_data.get("nome", "Unknown")
    cognome = card_data.get("cognome", "")
    role = card_data.get("ruolo", "SPIKER")
    role_icon = ROLE_ICONS.get(role, "⚡")
    atk = card_data.get("attacco", 40)
    dif = card_data.get("difesa", 40)
    bat = card_data.get("battuta", 40)

    if size == "small":
        width, font_ovr, font_name, font_first = "105px", "1.05rem", "0.55rem", "0.32rem"
    elif size == "large":
        width, font_ovr, font_name, font_first = "185px", "1.9rem", "0.95rem", "0.52rem"
    else:
        width, font_ovr, font_name, font_first = "140px", "1.4rem", "0.72rem", "0.42rem"

    # Background: usa PNG custom se fornito, altrimenti tier default
    if card_png_b64:
        bg_style = "background-image:url('data:{mime};base64,{b64}');background-size:cover;background-position:center top;".format(
            mime=card_png_mime, b64=card_png_b64)
    else:
        # Cerca PNG tier default
        bg_b64_def, bg_mime_def = _get_card_bg_b64(tier_name)
        if bg_b64_def:
            bg_style = "background-image:url('data:{mime};base64,{b64}');background-size:cover;background-position:center top;".format(
                mime=bg_mime_def, b64=bg_b64_def)
        else:
            bg_style = "background:linear-gradient(160deg,#111,#222,#111);"

    bg_div = '<div class="mbt-card-bg-image" style="{}"></div>'.format(bg_style)

    overlay_gradient = "linear-gradient(180deg,rgba(0,0,0,0.15) 0%,rgba(0,0,0,0.05) 35%,rgba(0,0,0,0.6) 72%,rgba(0,0,0,0.88) 100%)"
    overlay_div = '<div class="mbt-card-overlay" style="background:{};"></div>'.format(overlay_gradient)

    # Foto giocatore: usa b64 diretto se disponibile, altrimenti path (cached)
    foto_html = ""
    if foto_b64:
        foto_html = '<img class="mbt-card-photo" src="data:{mime};base64,{b64}" style="opacity:0.9">'.format(
            mime=foto_mime, b64=foto_b64)
    else:
        photo_path = card_data.get("foto_path", "")
        if photo_path and os.path.exists(photo_path):
            b64p, mime_p = _load_image_b64_cached(photo_path)
            if b64p:
                foto_html = '<img class="mbt-card-photo" src="data:{mime};base64,{b64}" style="opacity:0.9">'.format(
                    mime=mime_p, b64=b64p)
            else:
                foto_html = '<div class="mbt-card-photo-placeholder">{}</div>'.format(role_icon)
        else:
            foto_html = '<div class="mbt-card-photo-placeholder">{}</div>'.format(role_icon)

    # Animazioni tier default (se no custom o se show_special_effects)
    tier_anim = ""
    if show_special_effects and not custom_anim_overlay:
        tier_anim = _get_card_animation_overlay(tier_name, color, rarity)

    border_style = _get_card_border_style(tier_name, color, rarity)
    hover_overlay = '<div class="mbt-card-hover-overlay" style="background:radial-gradient(ellipse at 50% 25%,{}33 0%,transparent 65%);"></div>'.format(color)

    hover_sign = ""
    if rarity >= 8:
        hover_sign = (
            '<div class="card-signature" style="position:absolute;bottom:72px;width:100%;'
            'text-align:center;font-family:cursive;font-size:0.7rem;color:{c};opacity:0;'
            'transition:opacity 0.35s;z-index:15;text-shadow:0 0 10px {c}">✦ {n} ✦</div>'
            '<style>.mbt-card-wrap:hover .card-signature{{opacity:1!important;}}</style>'
        ).format(c=color, n=(cognome or nome).upper())

    tier_short = tier_name.split()[0] if len(tier_name.split()) > 1 else tier_name

    html = (
        '{custom_css}'
        '<div class="mbt-card-wrap" style="width:{width}">'
        '<div class="mbt-card" style="width:{width};{border}">'
        '{bg}{overlay}'
        '<div class="mbt-card-ovr" style="color:{color};font-size:{fovr}">{ovr}</div>'
        '<div class="mbt-card-tier-label" style="color:{color}">{tier_short}</div>'
        '{foto}'
        '<div class="mbt-card-name-block">'
        '<span class="mbt-card-firstname" style="color:{color};font-size:{ffirst}">{first}</span>'
        '<span class="mbt-card-lastname" style="color:{color};font-size:{fname}">{last}</span>'
        '</div>'
        '<div class="mbt-card-role" style="color:{color}">{role_icon} {role}</div>'
        '<div class="mbt-card-stats">'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{color}">{atk}</div><div class="mbt-stat-lbl">ATK</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{color}">{dif}</div><div class="mbt-stat-lbl">DEF</div></div>'
        '<div class="mbt-stat"><div class="mbt-stat-val" style="color:{color}">{bat}</div><div class="mbt-stat-lbl">BAT</div></div>'
        '</div>'
        '{tier_anim}{custom_anim}{hover}{sign}'
        '</div>'
        '</div>'
    ).format(
        custom_css=custom_anim_css,
        width=width, border=border_style,
        bg=bg_div, overlay=overlay_div,
        color=color, fovr=font_ovr, ovr=ovr, tier_short=tier_short,
        foto=foto_html, ffirst=font_first, fname=font_name,
        first=nome.upper(), last=(cognome or nome).upper(),
        role_icon=role_icon, role=role,
        atk=atk, dif=dif, bat=bat,
        tier_anim=tier_anim,
        custom_anim=custom_anim_overlay,
        hover=hover_overlay, sign=hover_sign,
    )
    return html


# ─── ADMIN TAB (accesso libero, nessuna password) ─────────────────────────────

def _render_admin_tab(state, cards_db, rivals_data):
    st.markdown("## ⚙️ Pannello Admin")
    admin_tabs = st.tabs(["🎨 Crea & Edita Carta", "📋 Gestisci Carte", "🎁 Gestisci Coins"])
    with admin_tabs[0]:
        _render_card_creator(state, cards_db)
    with admin_tabs[1]:
        _render_card_manager(cards_db)
    with admin_tabs[2]:
        _render_coins_manager(rivals_data)


def _render_card_creator(state, cards_db):
    st.markdown("### 🎨 Card Creator — Crea & Personalizza")

    # ── Sezione 1: Dati base ──────────────────────────────────────────────
    with st.expander("📝 Dati Giocatore & Statistiche", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nome = st.text_input("Nome", key="cc_nome")
            cognome = st.text_input("Cognome", key="cc_cognome")
            ruolo = st.selectbox("Ruolo", ROLES, key="cc_ruolo")
        with col_b:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                atk = st.slider("⚡ ATK", 0, 125, 70, key="cc_atk")
                dif = st.slider("🛡️ DEF", 0, 125, 68, key="cc_dif")
                ric = st.slider("🤲 RIC", 0, 125, 65, key="cc_ric")
            with col_s2:
                bat = st.slider("🏐 BAT", 0, 125, 67, key="cc_bat")
                mur = st.slider("🧱 MUR", 0, 125, 62, key="cc_mur")
                alz = st.slider("🎯 ALZ", 0, 125, 60, key="cc_alz")

        overall = calcola_ovr_da_stats(atk, dif, ric, bat, mur, alz)
        tier_preview = get_tier_by_ovr(overall)
        tier_color = CARD_TIERS.get(tier_preview, {}).get("color", "#ffd700")
        st.markdown(
            '<div style="font-family:Orbitron,sans-serif;font-size:0.95rem;color:{};font-weight:700;margin-top:6px">'
            '⚡ OVR: {} &nbsp;|&nbsp; Tier: {}</div>'.format(tier_color, overall, tier_preview),
            unsafe_allow_html=True
        )

        atleti_nomi = ["-- Nessuno --"] + [a["nome"] for a in state.get("atleti", [])]
        selected_atleta_nome = st.selectbox("🔗 Collega a Atleta Torneo", atleti_nomi, key="cc_atleta_link")
        atleta_id_linked = None
        if selected_atleta_nome != "-- Nessuno --":
            linked = next((a for a in state.get("atleti", []) if a["nome"] == selected_atleta_nome), None)
            if linked:
                atleta_id_linked = linked["id"]
                try:
                    from data_manager import calcola_overall_fifa
                    real_ovr = calcola_overall_fifa(linked)
                    st.info("📊 OVR reale dal torneo: **{}**".format(real_ovr))
                except Exception:
                    pass

    # ── Sezione 2: Upload immagini ────────────────────────────────────────
    with st.expander("🖼️ Upload Immagini Carta", expanded=True):
        st.markdown("""
        <div style="background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:12px;margin-bottom:12px">
            <div style="font-family:Orbitron,sans-serif;font-size:0.7rem;color:#ffd700;font-weight:700;margin-bottom:6px">
                📌 COME FUNZIONA
            </div>
            <div style="font-size:0.65rem;color:#888;line-height:1.6">
                1. <b style="color:#ccc">PNG Corpo Carta</b> → l'immagine che fa da sfondo/corpo della carta (es. il template grafico del tier)<br>
                2. <b style="color:#ccc">Foto Giocatore</b> → si posiziona sopra la carta, in sovrimpressione al centro<br>
                3. Se non carichi il PNG carta, viene usato automaticamente il template del tier
            </div>
        </div>
        """, unsafe_allow_html=True)

        img_col1, img_col2 = st.columns(2)
        with img_col1:
            st.markdown("**🃏 PNG Corpo Carta** *(sostituisce il template tier)*")
            card_png_file = st.file_uploader(
                "Carica PNG/WebP carta", type=["png","webp","jpg","jpeg"],
                key="cc_card_png",
                help="Il tuo PNG grafico personalizzato che diventerà il corpo della carta"
            )
            if card_png_file:
                st.image(card_png_file, caption="Preview corpo carta", width=140)
                card_png_file.seek(0)

        with img_col2:
            st.markdown("**👤 Foto Giocatore** *(si sovrappone sulla carta)*")
            foto_file = st.file_uploader(
                "Carica foto giocatore", type=["png","jpg","jpeg","webp"],
                key="cc_foto",
                help="La foto del giocatore che apparirà sopra il corpo della carta"
            )
            if foto_file:
                st.image(foto_file, caption="Preview foto giocatore", width=120)
                foto_file.seek(0)

    # ── Sezione 3: Editor Animazioni ──────────────────────────────────────
    with st.expander("✨ Editor Animazioni (35 effetti)", expanded=False):
        st.markdown("""
        <div style="font-family:Orbitron,sans-serif;font-size:0.75rem;color:#ffd700;
            margin-bottom:12px;font-weight:700">
            🎬 SELEZIONA LE ANIMAZIONI DA APPLICARE ALLA CARTA
        </div>
        """, unsafe_allow_html=True)

        selected_anims = st.session_state.get("cc_selected_anims", [])

        for cat_name, cat_effects in ANIMATION_CATALOG.items():
            st.markdown(
                '<div style="font-size:0.75rem;font-weight:700;color:#aaa;'
                'margin:10px 0 6px 0;letter-spacing:1px">{}</div>'.format(cat_name),
                unsafe_allow_html=True
            )
            effect_cols = st.columns(len(cat_effects))
            for j, (anim_id, (anim_label, anim_desc)) in enumerate(cat_effects.items()):
                with effect_cols[j]:
                    is_sel = anim_id in selected_anims
                    bg = "#1a2a1a" if is_sel else "#0d0d1a"
                    border = "#ffd700" if is_sel else "#1e1e3a"
                    check = "✅" if is_sel else "○"
                    st.markdown("""
                    <div style="background:{bg};border:1px solid {bc};border-radius:8px;
                        padding:8px 6px;text-align:center;margin-bottom:4px;min-height:70px">
                        <div style="font-size:0.7rem;font-weight:700;color:{nc}">{lbl}</div>
                        <div style="font-size:0.55rem;color:#666;margin-top:3px;line-height:1.3">{desc}</div>
                        <div style="font-size:0.8rem;margin-top:4px">{check}</div>
                    </div>
                    """.format(
                        bg=bg, bc=border, nc="#ffd700" if is_sel else "#ccc",
                        lbl=anim_label, desc=anim_desc, check=check
                    ), unsafe_allow_html=True)
                    btn_label = "Rimuovi" if is_sel else "Aggiungi"
                    if st.button(btn_label, key="anim_tog_{}_{}".format(cat_name[:3], anim_id), use_container_width=True):
                        if is_sel:
                            selected_anims.remove(anim_id)
                        else:
                            selected_anims.append(anim_id)
                        st.session_state.cc_selected_anims = selected_anims
                        st.rerun()

        if selected_anims:
            st.success("✅ Animazioni attive: {}".format(", ".join(selected_anims)))
            if st.button("🗑️ Rimuovi tutte le animazioni", key="cc_clear_anims"):
                st.session_state.cc_selected_anims = []
                st.rerun()
        else:
            st.info("Nessuna animazione selezionata — verrà usata quella predefinita del tier")

    # ── Anteprima live + salvataggio ──────────────────────────────────────
    st.markdown("---")
    st.markdown("### 👁️ Anteprima Live")

    # Prepara b64 per anteprima
    card_png_b64_prev, card_png_mime_prev = None, "image/png"
    if card_png_file:
        card_png_file.seek(0)
        card_png_b64_prev, card_png_mime_prev = _file_to_b64(card_png_file)
        card_png_file.seek(0)

    foto_b64_prev, foto_mime_prev = None, "image/jpeg"
    if foto_file:
        foto_file.seek(0)
        foto_b64_prev, foto_mime_prev = _file_to_b64(foto_file)
        foto_file.seek(0)

    selected_anims_prev = st.session_state.get("cc_selected_anims", [])
    custom_css_prev, custom_overlay_prev = build_custom_animation_css(
        tuple(selected_anims_prev),
        card_color=tier_color
    )

    preview_card = {
        "id": "preview", "nome": nome or "NOME", "cognome": cognome or "",
        "overall": overall, "ruolo": ruolo,
        "attacco": atk, "difesa": dif, "battuta": bat,
        "muro": mur, "ricezione": ric, "alzata": alz,
        "foto_path": "",
    }

    prev_col1, prev_col2, prev_col3 = st.columns([1, 2, 1])
    with prev_col2:
        st.markdown(
            '<div class="creator-preview-wrap">{}</div>'.format(
                render_card_html_custom(
                    preview_card,
                    card_png_b64=card_png_b64_prev,
                    card_png_mime=card_png_mime_prev,
                    foto_b64=foto_b64_prev,
                    foto_mime=foto_mime_prev,
                    custom_anim_css=custom_css_prev,
                    custom_anim_overlay=custom_overlay_prev,
                    size="large"
                )
            ),
            unsafe_allow_html=True
        )
        st.markdown("""
        <div style="background:#10101e;border:1px solid {tc};border-radius:8px;
            padding:10px;text-align:center;margin-top:10px">
            <div style="font-family:Orbitron,sans-serif;font-size:0.75rem;color:{tc};font-weight:700">{tier}</div>
            <div style="font-size:0.6rem;color:#888;margin-top:2px">OVR {ovr}</div>
            <div style="font-size:0.55rem;color:#555;margin-top:2px">{n_anim} animazioni attive</div>
        </div>
        """.format(
            tc=tier_color, tier=tier_preview, ovr=overall,
            n_anim=len(selected_anims_prev)
        ), unsafe_allow_html=True)

    # ── Salvataggio ───────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("💾 SALVA CARTA nel Database", use_container_width=True, type="primary"):
        if not nome:
            st.error("Inserisci almeno il nome del giocatore!")
        else:
            # Salva PNG carta se fornito
            card_png_path = ""
            if card_png_file:
                card_png_file.seek(0)
                os.makedirs(ASSETS_CARDS_DIR, exist_ok=True)
                ext_cp = card_png_file.name.rsplit(".", 1)[-1].lower()
                card_png_path = os.path.join(
                    ASSETS_CARDS_DIR,
                    "custom_{}_{}_{}.{}".format(nome, cognome or "card", random.randint(1000, 9999), ext_cp)
                )
                with open(card_png_path, "wb") as f:
                    f.write(card_png_file.read())

            # Salva foto giocatore se fornita
            foto_path = ""
            if foto_file:
                foto_file.seek(0)
                os.makedirs(ASSETS_ICONS_DIR, exist_ok=True)
                ext_fp = foto_file.name.rsplit(".", 1)[-1].lower()
                foto_path = os.path.join(
                    ASSETS_ICONS_DIR,
                    "{}_{}_{}.{}".format(nome, cognome or "player", random.randint(1000, 9999), ext_fp)
                )
                with open(foto_path, "wb") as f:
                    f.write(foto_file.read())

            new_id = "card_{}_{}".format(cards_db["next_id"], random.randint(1000, 9999))
            cards_db["next_id"] += 1
            new_card = {
                "id": new_id,
                "nome": nome,
                "cognome": cognome,
                "overall": overall,
                "ruolo": ruolo,
                "attacco": atk, "difesa": dif, "muro": mur,
                "ricezione": ric, "battuta": bat, "alzata": alz,
                "foto_path": foto_path,
                "card_png_path": card_png_path,
                "custom_animations": st.session_state.get("cc_selected_anims", []),
                "tier": tier_preview,
                "atleta_id": atleta_id_linked,
                "created_at": datetime.now().isoformat(),
            }
            cards_db["cards"].append(new_card)
            save_cards_db(cards_db)
            # Auto-aggiunge alla collezione del giocatore
            rd = st.session_state.get("rivals_data", {})
            if rd:
                coll = rd.get("collection", [])
                if new_id not in coll:
                    coll.append(new_id)
                    rd["collection"] = coll
                    save_rivals_data(rd)
            # Invalida cache immagini per i nuovi path
            _load_card_png_b64.clear()
            _load_image_b64_cached.clear()
            st.success("✅ Carta **{} {}** (OVR {} · {} · {} anim.) salvata e aggiunta alla collezione!".format(
                nome, cognome, overall, tier_preview,
                len(new_card["custom_animations"])
            ))
            st.session_state.cards_db = cards_db
            st.session_state.cc_selected_anims = []
            st.rerun()


@st.cache_data(show_spinner=False)
def _load_card_png_b64(card_png_path: str):
    """Cached: carica il PNG corpo carta UNA SOLA VOLTA per path."""
    if card_png_path and os.path.exists(card_png_path):
        with open(card_png_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = card_png_path.rsplit(".", 1)[-1].lower()
        mime = {"png":"image/png","webp":"image/webp","jpg":"image/jpeg","jpeg":"image/jpeg"}.get(ext,"image/png")
        return b64, mime
    return None, "image/png"


def _render_card_for_display(card, size="small", show_special_effects=True):
    """Renderizza carta usando PNG custom + animazioni salvate se disponibili."""
    tier_name = get_tier_by_ovr(card.get("overall", 40))
    tier_color = CARD_TIERS.get(tier_name, {}).get("color", "#ffd700")
    custom_anims = card.get("custom_animations", [])
    card_png_b64, card_png_mime = _load_card_png_b64(card.get("card_png_path", ""))
    custom_css, custom_overlay = ("", "")
    if custom_anims:
        custom_css, custom_overlay = build_custom_animation_css(tuple(custom_anims), card_color=tier_color)
    return render_card_html_custom(
        card,
        card_png_b64=card_png_b64, card_png_mime=card_png_mime,
        custom_anim_css=custom_css, custom_anim_overlay=custom_overlay,
        size=size,
        show_special_effects=(show_special_effects and not custom_anims)
    )


def _render_card_manager(cards_db):
    st.markdown("### 📋 Carte nel Database")
    all_cards = cards_db.get("cards", [])
    if not all_cards:
        st.info("Nessuna carta. Creane una con il Card Creator!")
        return
    st.caption("Totale: {} carte".format(len(all_cards)))
    filter_tier = st.selectbox("Filtra Tier", ["Tutte"] + list(CARD_TIERS.keys()), key="mgr_filter")
    filtered = all_cards if filter_tier == "Tutte" else [
        c for c in all_cards if get_tier_by_ovr(c.get("overall", 40)) == filter_tier
    ]
    for i, card in enumerate(filtered):
        tier = get_tier_by_ovr(card.get("overall", 40))
        tc = CARD_TIERS.get(tier, {}).get("color", "#888")
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(_render_card_for_display(card, size="small", show_special_effects=False), unsafe_allow_html=True)
        with col2:
            atk = card.get("attacco", 40)
            dif = card.get("difesa", 40)
            bat = card.get("battuta", 40)
            mur = card.get("muro", 40)
            ric = card.get("ricezione", 40)
            alz = card.get("alzata", 40)
            st.markdown("""
            <div style="padding:8px 0">
                <div style="font-family:Orbitron,sans-serif;font-weight:700;color:{tc}">{nome} {cognome}</div>
                <div style="font-size:0.7rem;color:#888">OVR {ovr} · {tier} · {ruolo}</div>
                <div style="font-size:0.6rem;color:#666;margin-top:4px">
                    ATK:{atk} | DEF:{dif} | BAT:{bat} | MUR:{mur} | RIC:{ric} | ALZ:{alz}
                </div>
            </div>
            """.format(tc=tc, nome=card.get("nome",""), cognome=card.get("cognome",""),
                       ovr=card.get("overall",40), tier=tier, ruolo=card.get("ruolo",""),
                       atk=atk, dif=dif, bat=bat, mur=mur, ric=ric, alz=alz),
                unsafe_allow_html=True)
            with st.expander("✏️ Modifica Stats"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_atk = st.slider("ATK", 0, 125, int(atk), key="edit_atk_{}_{}".format(i, card.get("id","")[:6]))
                    new_dif = st.slider("DEF", 0, 125, int(dif), key="edit_dif_{}_{}".format(i, card.get("id","")[:6]))
                    new_ric = st.slider("RIC", 0, 125, int(ric), key="edit_ric_{}_{}".format(i, card.get("id","")[:6]))
                with ec2:
                    new_bat = st.slider("BAT", 0, 125, int(bat), key="edit_bat_{}_{}".format(i, card.get("id","")[:6]))
                    new_mur = st.slider("MUR", 0, 125, int(mur), key="edit_mur_{}_{}".format(i, card.get("id","")[:6]))
                    new_alz = st.slider("ALZ", 0, 125, int(alz), key="edit_alz_{}_{}".format(i, card.get("id","")[:6]))
                new_ovr = calcola_ovr_da_stats(new_atk, new_dif, new_ric, new_bat, new_mur, new_alz)
                st.caption("OVR: {} | Tier: {}".format(new_ovr, get_tier_by_ovr(new_ovr)))
                if st.button("💾 Salva Modifiche", key="save_card_{}_{}".format(i, card.get("id","")[:6])):
                    card["attacco"] = new_atk
                    card["difesa"] = new_dif
                    card["ricezione"] = new_ric
                    card["battuta"] = new_bat
                    card["muro"] = new_mur
                    card["alzata"] = new_alz
                    card["overall"] = new_ovr
                    card["tier"] = get_tier_by_ovr(new_ovr)
                    save_cards_db(cards_db)
                    st.session_state.cards_db = cards_db
                    st.success("✅ Stats aggiornate!")
                    st.rerun()
        with col3:
            if st.button("🗑️", key="del_card_{}_{}".format(i, card.get("id","")[:8]), help="Elimina"):
                cards_db["cards"] = [c for c in all_cards if c.get("id") != card.get("id")]
                save_cards_db(cards_db)
                st.session_state.cards_db = cards_db
                st.rerun()
        st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>", unsafe_allow_html=True)


def _render_coins_manager(rivals_data):
    st.markdown("### 🎁 Gestione Coins & XP")
    col1, col2 = st.columns(2)
    with col1:
        add_coins = st.number_input("Aggiungi MBT Coins", 0, 99999, 500, key="admin_add_coins")
        if st.button("➕ Aggiungi Coins", key="admin_btn_coins"):
            rivals_data["mbt_coins"] += add_coins
            st.success("✅ Aggiunti {} coins! Totale: {}".format(add_coins, rivals_data["mbt_coins"]))
    with col2:
        add_xp = st.number_input("Aggiungi XP", 0, 99999, 100, key="admin_add_xp")
        if st.button("➕ Aggiungi XP", key="admin_btn_xp"):
            rivals_data["player_xp"] += add_xp
            _check_level_up(rivals_data)
            st.success("✅ Aggiunti {} XP! Level: {}".format(add_xp, rivals_data["player_level"]))
    st.markdown("---")
    st.markdown("""
    **Stato attuale:**
    - MBT Coins: **{}**
    - XP: **{}**
    - Livello: **{}**
    - Trofei: **{}**
    - Vittorie: **{}**
    """.format(
        rivals_data["mbt_coins"], rivals_data["player_xp"],
        rivals_data["player_level"], rivals_data["trofei_rivals"],
        rivals_data["battle_wins"]
    ))
    if st.button("🔄 Reset Dati Rivals", key="admin_reset_rivals"):
        st.session_state.rivals_data = empty_rivals_state()
        st.session_state.rivals_data["mbt_coins"] = 1000
        save_rivals_data(st.session_state.rivals_data)
        st.success("✅ Dati resettati con 1000 Coins di partenza.")
        st.rerun()
