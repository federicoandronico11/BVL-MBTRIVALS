"""
mbt_draft.py — MBT RIVALS: Modalità DRAFT v1.0
La Scalata del Draft: percorso di 7 tappe con difficoltà crescente.
Carte Limited Edition esclusive con 50 forme e animazioni speciali.
Import da mbt_rivals.py: render_card_html, CARD_TIERS, get_tier_by_ovr,
  calcola_ovr_da_stats, ROLES, ROLE_ICONS, _is_trainer,
  _load_image_b64_cached, save_cards_db, ASSETS_ICONS_DIR, ASSETS_CARDS_DIR
"""

import streamlit as st
import json
import random
import os
import base64
import hashlib
from pathlib import Path
from datetime import datetime

# ─── DRAFT CONSTANTS ─────────────────────────────────────────────────────────

DRAFT_STEPS = 7  # tappe per completare un Draft

DRAFT_DIFFICULTIES = {
    "Principiante": {
        "icon": "🌱", "color": "#cd7f32", "cpu_ovr_range": (60, 70),
        "prize_weights": {"Base": 0.80, "Epica": 0.20},
        "prize_tiers": ["Bronzo Comune","Bronzo Raro","Argento Comune","Argento Raro","Oro Comune","Oro Raro"],
        "ovr_step_increase": 1, "desc": "CPU OVR 60-70 | Premio: Comune o Epica",
        "xp_bonus": 50, "coins_bonus": 100,
    },
    "Dilettante": {
        "icon": "⚽", "color": "#c0c0c0", "cpu_ovr_range": (70, 80),
        "prize_weights": {"Base": 0.60, "Epica": 0.35, "Leggenda": 0.05},
        "prize_tiers": ["Argento Raro","Oro Comune","Oro Raro","Eroe","IF (In Form)"],
        "ovr_step_increase": 2, "desc": "CPU OVR 70-80 | Premio: fino a Leggenda",
        "xp_bonus": 100, "coins_bonus": 200,
    },
    "Esperto": {
        "icon": "🏆", "color": "#ffd700", "cpu_ovr_range": (80, 90),
        "prize_weights": {"Epica": 0.50, "Leggenda": 0.45, "TOTY": 0.05},
        "prize_tiers": ["Eroe","IF (In Form)","Leggenda","TOTY"],
        "ovr_step_increase": 3, "desc": "CPU OVR 80-90 | Premio: Epica–TOTY",
        "xp_bonus": 200, "coins_bonus": 400,
    },
    "Campione": {
        "icon": "👑", "color": "#9b59b6", "cpu_ovr_range": (90, 100),
        "prize_weights": {"Leggenda": 0.70, "TOTY": 0.25, "Icona": 0.05},
        "prize_tiers": ["Leggenda","TOTY","TOTY Evoluto","GOAT","ICON BASE"],
        "ovr_step_increase": 4, "desc": "CPU OVR 90-100 | Premio: Leggenda–Icona",
        "xp_bonus": 350, "coins_bonus": 700,
    },
    "Eroe": {
        "icon": "⚡", "color": "#4169e1", "cpu_ovr_range": (100, 110),
        "prize_weights": {"TOTY": 0.60, "Icona": 0.35, "God": 0.05},
        "prize_tiers": ["TOTY Evoluto","GOAT","ICON BASE","ICON EPICA","ICON LEGGENDARIA"],
        "ovr_step_increase": 5, "desc": "CPU OVR 100-110 | Premio: TOTY–God Mode",
        "xp_bonus": 600, "coins_bonus": 1200,
    },
    "Leggenda": {
        "icon": "🔥", "color": "#ff2200", "cpu_ovr_range": (110, 125),
        "prize_weights": {"Icona": 0.50, "God": 0.40, "Omega": 0.10},
        "prize_tiers": ["ICON BASE","ICON EPICA","ICON LEGGENDARIA","ICON TOTY","ICON GOD"],
        "ovr_step_increase": 6, "desc": "CPU OVR 110-125 | Premio: Icona–Omega",
        "xp_bonus": 1000, "coins_bonus": 2000,
    },
}

# ─── 50 FORME CARTE LIMITED ───────────────────────────────────────────────────

CARD_SHAPES = {
    # ── Standard variations ──
    "classic": {
        "name": "Classic", "group": "Standard",
        "clip": "none", "border_radius": "14px",
        "extra_css": "",
    },
    "rounded_xl": {
        "name": "Rounded XL", "group": "Standard",
        "clip": "none", "border_radius": "28px",
        "extra_css": "",
    },
    "sharp": {
        "name": "Sharp Edge", "group": "Standard",
        "clip": "none", "border_radius": "2px",
        "extra_css": "",
    },
    "stadium": {
        "name": "Stadium", "group": "Standard",
        "clip": "none", "border_radius": "50% 50% 14px 14px / 30% 30% 14px 14px",
        "extra_css": "",
    },
    "hex": {
        "name": "Hexagon", "group": "Geometric",
        "clip": "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "diamond": {
        "name": "Diamond", "group": "Geometric",
        "clip": "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "pentagon": {
        "name": "Pentagon", "group": "Geometric",
        "clip": "polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "octagon": {
        "name": "Octagon", "group": "Geometric",
        "clip": "polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "shield": {
        "name": "Shield", "group": "Geometric",
        "clip": "polygon(0% 0%, 100% 0%, 100% 70%, 50% 100%, 0% 70%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "arrow_up": {
        "name": "Arrow Up", "group": "Geometric",
        "clip": "polygon(50% 0%, 100% 40%, 80% 40%, 80% 100%, 20% 100%, 20% 40%, 0% 40%)",
        "border_radius": "0",
        "extra_css": "",
    },
    # ── Torn / Exploded ──
    "exploded_tr": {
        "name": "Esplosa (angolo alto dx)", "group": "Esplose",
        "clip": "polygon(0% 0%, 72% 0%, 85% 8%, 100% 0%, 100% 100%, 0% 100%)",
        "border_radius": "4px",
        "extra_css": "filter:drop-shadow(4px -4px 6px rgba(255,100,0,.7))",
    },
    "exploded_tl": {
        "name": "Esplosa (angolo alto sx)", "group": "Esplose",
        "clip": "polygon(0% 0%, 15% 8%, 28% 0%, 100% 0%, 100% 100%, 0% 100%)",
        "border_radius": "4px",
        "extra_css": "filter:drop-shadow(-4px -4px 6px rgba(255,100,0,.7))",
    },
    "shatter_corner": {
        "name": "Frantumata (angolo)", "group": "Esplose",
        "clip": "polygon(0% 0%, 60% 0%, 65% 5%, 75% 2%, 80% 8%, 100% 0%, 100% 100%, 0% 100%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(3px -3px 8px rgba(255,200,0,.8))",
    },
    "debris_right": {
        "name": "Detriti destra", "group": "Esplose",
        "clip": "polygon(0% 0%, 100% 0%, 92% 15%, 100% 25%, 95% 40%, 100% 55%, 97% 70%, 100% 100%, 0% 100%)",
        "border_radius": "4px 0 4px 4px",
        "extra_css": "filter:drop-shadow(6px 0px 10px rgba(255,150,0,.6))",
    },
    "torn_bottom": {
        "name": "Strappata in basso", "group": "Esplose",
        "clip": "polygon(0% 0%, 100% 0%, 100% 82%, 90% 88%, 80% 83%, 70% 90%, 60% 84%, 50% 92%, 40% 85%, 30% 91%, 20% 84%, 10% 89%, 0% 83%)",
        "border_radius": "8px 8px 0 0",
        "extra_css": "filter:drop-shadow(0px 6px 10px rgba(255,80,0,.5))",
    },
    "crack_center": {
        "name": "Incrinata al centro", "group": "Esplose",
        "clip": "polygon(0% 0%, 46% 0%, 47% 45%, 53% 50%, 54% 0%, 100% 0%, 100% 100%, 54% 100%, 53% 55%, 47% 50%, 46% 100%, 0% 100%)",
        "border_radius": "8px",
        "extra_css": "filter:drop-shadow(0 0 12px rgba(255,50,50,.7))",
    },
    # ── Futuristic ──
    "cyber_cut": {
        "name": "Cyber Cut", "group": "Futuristico",
        "clip": "polygon(0% 0%, 85% 0%, 100% 15%, 100% 100%, 15% 100%, 0% 85%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "cyber_cross": {
        "name": "Cyber Cross", "group": "Futuristico",
        "clip": "polygon(0% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "holo_frame": {
        "name": "Holo Frame", "group": "Futuristico",
        "clip": "polygon(5% 0%, 95% 0%, 100% 5%, 100% 95%, 95% 100%, 5% 100%, 0% 95%, 0% 5%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "tech_left": {
        "name": "Tech Left", "group": "Futuristico",
        "clip": "polygon(12% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 12%)",
        "border_radius": "0 8px 8px 0",
        "extra_css": "",
    },
    "tech_right": {
        "name": "Tech Right", "group": "Futuristico",
        "clip": "polygon(0% 0%, 88% 0%, 100% 12%, 100% 100%, 0% 100%)",
        "border_radius": "8px 0 0 8px",
        "extra_css": "",
    },
    "blade": {
        "name": "Blade", "group": "Futuristico",
        "clip": "polygon(10% 0%, 100% 0%, 90% 100%, 0% 100%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "reverse_blade": {
        "name": "Reverse Blade", "group": "Futuristico",
        "clip": "polygon(0% 0%, 90% 0%, 100% 100%, 10% 100%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "trapezoid_tall": {
        "name": "Trapezio Alto", "group": "Futuristico",
        "clip": "polygon(8% 0%, 92% 0%, 100% 100%, 0% 100%)",
        "border_radius": "0",
        "extra_css": "",
    },
    # ── Organic / Natural ──
    "wave_right": {
        "name": "Wave Right", "group": "Organico",
        "clip": "polygon(0% 0%, 88% 0%, 100% 10%, 95% 30%, 100% 50%, 95% 70%, 100% 90%, 88% 100%, 0% 100%)",
        "border_radius": "8px 0 0 8px",
        "extra_css": "",
    },
    "wave_left": {
        "name": "Wave Left", "group": "Organico",
        "clip": "polygon(12% 0%, 100% 0%, 100% 100%, 12% 100%, 0% 90%, 5% 70%, 0% 50%, 5% 30%, 0% 10%)",
        "border_radius": "0 8px 8px 0",
        "extra_css": "",
    },
    "cloud_top": {
        "name": "Cloud Top", "group": "Organico",
        "clip": "polygon(10% 15%, 20% 5%, 35% 12%, 50% 0%, 65% 12%, 80% 5%, 90% 15%, 100% 30%, 100% 100%, 0% 100%, 0% 30%)",
        "border_radius": "0 0 8px 8px",
        "extra_css": "",
    },
    "flame_shape": {
        "name": "Fiamma", "group": "Organico",
        "clip": "polygon(50% 0%, 70% 20%, 100% 30%, 85% 60%, 90% 100%, 50% 85%, 10% 100%, 15% 60%, 0% 30%, 30% 20%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(0 0 14px rgba(255,100,0,.8))",
    },
    "leaf": {
        "name": "Foglia", "group": "Organico",
        "clip": "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
        "border_radius": "50% 0",
        "extra_css": "",
    },
    # ── Aura / Glow shapes ──
    "star_5": {
        "name": "Stella 5 punte", "group": "Speciale",
        "clip": "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(0 0 18px rgba(255,215,0,.9))",
    },
    "star_6": {
        "name": "Stella 6 punte", "group": "Speciale",
        "clip": "polygon(50% 0%, 60% 38%, 93% 25%, 72% 55%, 100% 68%, 65% 68%, 50% 100%, 35% 68%, 0% 68%, 28% 55%, 7% 25%, 40% 38%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(0 0 16px rgba(255,215,0,.8))",
    },
    "burst": {
        "name": "Burst", "group": "Speciale",
        "clip": "polygon(50% 0%, 55% 35%, 80% 10%, 65% 40%, 100% 35%, 70% 50%, 100% 65%, 65% 60%, 80% 90%, 55% 65%, 50% 100%, 45% 65%, 20% 90%, 35% 60%, 0% 65%, 30% 50%, 0% 35%, 35% 40%, 20% 10%, 45% 35%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(0 0 20px rgba(255,200,0,.9))",
    },
    "cross_shape": {
        "name": "Croce", "group": "Speciale",
        "clip": "polygon(35% 0%, 65% 0%, 65% 35%, 100% 35%, 100% 65%, 65% 65%, 65% 100%, 35% 100%, 35% 65%, 0% 65%, 0% 35%, 35% 35%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "badge": {
        "name": "Badge", "group": "Speciale",
        "clip": "polygon(15% 0%, 85% 0%, 100% 15%, 100% 75%, 50% 100%, 0% 75%, 0% 15%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "ribbon": {
        "name": "Ribbon", "group": "Speciale",
        "clip": "polygon(0% 0%, 100% 0%, 100% 80%, 50% 100%, 0% 80%)",
        "border_radius": "0",
        "extra_css": "",
    },
    # ── Distorted ──
    "glitch_h": {
        "name": "Glitch Orizzontale", "group": "Glitch",
        "clip": "polygon(0% 0%, 102% 0%, 100% 32%, 103% 33%, 100% 34%, 102% 65%, 100% 66%, 102% 67%, 100% 100%, -2% 100%, 0% 67%, -3% 66%, 0% 65%, -2% 33%, 0% 32%)",
        "border_radius": "2px",
        "extra_css": "filter:drop-shadow(3px 0 0 rgba(0,255,255,.6)) drop-shadow(-3px 0 0 rgba(255,0,255,.6))",
    },
    "glitch_v": {
        "name": "Glitch Verticale", "group": "Glitch",
        "clip": "polygon(0% 0%, 33% 0%, 34% -3%, 35% 0%, 65% 0%, 66% -2%, 67% 0%, 100% 0%, 100% 100%, 67% 100%, 66% 102%, 65% 100%, 35% 100%, 34% 103%, 33% 100%, 0% 100%)",
        "border_radius": "2px",
        "extra_css": "filter:drop-shadow(0 3px 0 rgba(0,255,200,.6)) drop-shadow(0 -3px 0 rgba(255,0,100,.6))",
    },
    "scan_lines": {
        "name": "Scan Lines", "group": "Glitch",
        "clip": "none", "border_radius": "8px",
        "extra_css": "background-image:repeating-linear-gradient(0deg,transparent,transparent 4px,rgba(0,255,255,.05) 4px,rgba(0,255,255,.05) 5px)",
    },
    "pixelated": {
        "name": "Pixel Art", "group": "Glitch",
        "clip": "none", "border_radius": "0",
        "extra_css": "image-rendering:pixelated",
    },
    # ── Premium / Luxury ──
    "oval": {
        "name": "Ovale", "group": "Premium",
        "clip": "ellipse(48% 50% at 50% 50%)",
        "border_radius": "50%",
        "extra_css": "",
    },
    "capsule": {
        "name": "Capsula", "group": "Premium",
        "clip": "none", "border_radius": "200px",
        "extra_css": "",
    },
    "vintage": {
        "name": "Vintage", "group": "Premium",
        "clip": "none", "border_radius": "50% 50% 50% 50% / 5% 5% 5% 5%",
        "extra_css": "outline:3px double #ffd700;outline-offset:3px",
    },
    "gold_frame": {
        "name": "Gold Frame", "group": "Premium",
        "clip": "none", "border_radius": "12px",
        "extra_css": "outline:4px solid #ffd700;outline-offset:2px;box-shadow:0 0 0 7px #7a5800,0 0 0 9px #ffd700",
    },
    "trophy": {
        "name": "Trofeo", "group": "Premium",
        "clip": "polygon(20% 0%, 80% 0%, 100% 20%, 100% 70%, 80% 85%, 60% 90%, 60% 100%, 40% 100%, 40% 90%, 20% 85%, 0% 70%, 0% 20%)",
        "border_radius": "0",
        "extra_css": "filter:drop-shadow(0 0 16px rgba(255,215,0,.8))",
    },
    "crown": {
        "name": "Corona", "group": "Premium",
        "clip": "polygon(0% 100%, 0% 40%, 15% 60%, 30% 20%, 50% 50%, 70% 20%, 85% 60%, 100% 40%, 100% 100%)",
        "border_radius": "0 0 8px 8px",
        "extra_css": "filter:drop-shadow(0 0 14px rgba(255,215,0,.9))",
    },
    # ── Sport ──
    "volleyball": {
        "name": "Pallone Volley", "group": "Sport",
        "clip": "ellipse(50% 50% at 50% 50%)",
        "border_radius": "50%",
        "extra_css": "",
    },
    "pennant": {
        "name": "Gagliardetto", "group": "Sport",
        "clip": "polygon(0% 0%, 100% 0%, 80% 50%, 100% 100%, 0% 100%)",
        "border_radius": "0",
        "extra_css": "",
    },
    "jersey": {
        "name": "Maglia", "group": "Sport",
        "clip": "polygon(20% 0%, 30% 10%, 50% 5%, 70% 10%, 80% 0%, 100% 15%, 85% 25%, 85% 100%, 15% 100%, 15% 25%, 0% 15%)",
        "border_radius": "0",
        "extra_css": "",
    },
}

# ─── LIMITED CARD ANIMATIONS ─────────────────────────────────────────────────

LIMITED_ANIMATIONS = {
    "sparkle_gold": {
        "name": "✨ Polvere d'Oro", "group": "Particelle",
        "css_keyframes": """
@keyframes sparkleFloat{0%{transform:translate(0,0) scale(1) rotate(0deg);opacity:1}
100%{transform:translate(var(--sdx,20px),var(--sdy,-50px)) scale(0) rotate(var(--srot,360deg));opacity:0}}""",
        "overlay_fn": "sparkle_gold",
    },
    "bubbles_color": {
        "name": "🫧 Bolle Colorate", "group": "Particelle",
        "css_keyframes": """
@keyframes bubbleRise{0%{transform:translateY(0) scale(1);opacity:.8}
100%{transform:translateY(-120px) scale(0.3);opacity:0}}""",
        "overlay_fn": "bubbles_color",
    },
    "lightning_cuts": {
        "name": "⚡ Lampi Taglienti", "group": "Energia",
        "css_keyframes": """
@keyframes lightCut{0%,88%,100%{opacity:0;transform:scaleY(1)}90%,96%{opacity:1;transform:scaleY(1.05)}93%,99%{opacity:.2}}""",
        "overlay_fn": "lightning_cuts",
    },
    "fire_intense": {
        "name": "🔥 Fuoco Intenso", "group": "Energia",
        "css_keyframes": """
@keyframes fireRise{0%,100%{transform:scaleY(1) scaleX(1);opacity:.9}
50%{transform:scaleY(1.15) scaleX(1.05);opacity:1}}""",
        "overlay_fn": "fire_intense",
    },
    "nebula_swirl": {
        "name": "🌌 Nebulosa", "group": "Spazio",
        "css_keyframes": """
@keyframes nebulaLimited{0%{transform:rotate(0deg) scale(1);opacity:.6}
50%{transform:rotate(180deg) scale(1.1);opacity:.9}
100%{transform:rotate(360deg) scale(1);opacity:.6}}""",
        "overlay_fn": "nebula_swirl",
    },
    "rainbow_wave": {
        "name": "🌈 Onda Arcobaleno", "group": "Colore",
        "css_keyframes": """
@keyframes rainbowLimited{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}""",
        "overlay_fn": "rainbow_wave",
    },
    "holographic_3d": {
        "name": "💎 Olografica 3D", "group": "Colore",
        "css_keyframes": """
@keyframes holoLimited{0%{background-position:0% 50%;opacity:.7}
33%{background-position:50% 100%;opacity:1}
66%{background-position:100% 0%;opacity:.8}
100%{background-position:0% 50%;opacity:.7}}""",
        "overlay_fn": "holographic_3d",
    },
    "glitch_effect": {
        "name": "🔊 Glitch", "group": "Digitale",
        "css_keyframes": """
@keyframes glitchAnim{0%,100%{clip-path:inset(0 0 95% 0);transform:translate(-3px,0)}
10%{clip-path:inset(10% 0 80% 0);transform:translate(3px,0)}
20%{clip-path:inset(25% 0 60% 0);transform:translate(-3px,2px)}
30%{clip-path:inset(50% 0 30% 0);transform:translate(4px,-1px)}
40%{clip-path:inset(70% 0 10% 0);transform:translate(-4px,1px)}
50%,90%{clip-path:inset(0 0 0 0);transform:translate(0,0)}}""",
        "overlay_fn": "glitch_effect",
    },
    "cosmic_beam": {
        "name": "🔮 Raggio Cosmico", "group": "Spazio",
        "css_keyframes": """
@keyframes cosmicBeam{0%{transform:rotate(0deg);opacity:.5}100%{transform:rotate(360deg);opacity:.5}}""",
        "overlay_fn": "cosmic_beam",
    },
    "ice_crystals": {
        "name": "❄️ Cristalli di Ghiaccio", "group": "Natura",
        "css_keyframes": """
@keyframes iceDrift{0%{transform:translate(0,0) rotate(0deg) scale(1);opacity:.9}
100%{transform:translate(var(--idx,10px),var(--idy,-40px)) rotate(var(--irot,180deg)) scale(0);opacity:0}}""",
        "overlay_fn": "ice_crystals",
    },
}


def _gen_limited_overlay(anim_id: str, color1: str, color2: str, card_id: str) -> str:
    """Genera overlay HTML per animazioni Limited Edition."""
    h = int(hashlib.md5((anim_id + card_id).encode()).hexdigest()[:8], 16)

    if anim_id == "sparkle_gold":
        parts = ""
        shapes = ["✦", "✧", "★", "◆", "✸", "·", "⬡"]
        for i in range(14):
            s = (h * (i + 3)) & 0xFFFF
            dx = ((s >> 1) % 61) - 30
            dy = -((s >> 3) % 56) - 10
            rot = (s >> 2) % 720
            dl = (s % 28) / 10.0
            dur = 1.5 + (s >> 4 & 15) / 10.0
            top = 5 + (s >> 5) % 85
            lft = 5 + (s >> 6) % 85
            sz = 0.45 + (s % 6) / 10.0
            shp = shapes[s % len(shapes)]
            parts += (
                '<div style="position:absolute;font-size:{sz}rem;color:{c};'
                'top:{t}%;left:{l}%;animation:sparkleFloat {dur:.1f}s {dl:.1f}s infinite;'
                '--sdx:{dx}px;--sdy:{dy}px;--srot:{rot}deg;z-index:9;'
                'text-shadow:0 0 6px {c};">{shp}</div>'
            ).format(sz=sz, c=color1, t=top, l=lft, dur=dur, dl=dl, dx=dx, dy=dy, rot=rot, shp=shp)
        return '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">{}</div>'.format(parts)

    elif anim_id == "bubbles_color":
        colors = [color1, color2, "#ff00cc", "#00ffcc", "#ffcc00", "#cc00ff"]
        parts = ""
        for i in range(10):
            s = (h * (i + 5)) & 0xFFFF
            dl = (s % 25) / 10.0
            dur = 2.0 + (s >> 3 & 15) / 10.0
            top = 50 + (s >> 4) % 45
            lft = 5 + (s >> 5) % 88
            sz = 4 + (s % 12)
            clr = colors[s % len(colors)]
            opacity = 0.5 + (s % 5) / 10.0
            parts += (
                '<div style="position:absolute;width:{sz}px;height:{sz}px;'
                'border-radius:50%;background:{c};opacity:{op:.1f};'
                'top:{t}%;left:{l}%;animation:bubbleRise {dur:.1f}s {dl:.1f}s infinite;'
                'box-shadow:0 0 8px {c};z-index:9;pointer-events:none;"></div>'
            ).format(sz=sz, c=clr, op=opacity, t=top, l=lft, dur=dur, dl=dl)
        return '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">{}</div>'.format(parts)

    elif anim_id == "lightning_cuts":
        bolts = ""
        for i in range(3):
            s = (h * (i + 7)) & 0xFFFF
            dl = (s % 18) / 10.0
            dur = 1.2 + (s >> 4 & 7) / 10.0
            left = 15 + (s % 70)
            rot = -20 + (s >> 3 & 31) - 15
            bolts += (
                '<div style="position:absolute;top:0;left:{l}%;width:2px;height:100%;'
                'background:linear-gradient(180deg,{c},transparent 60%);'
                'transform:rotate({rot}deg);transform-origin:top center;'
                'animation:lightCut {dur:.1f}s {dl:.1f}s infinite;'
                'box-shadow:0 0 6px {c},0 0 14px {c};z-index:10;pointer-events:none;"></div>'
            ).format(l=left, c=color1, rot=rot, dur=dur, dl=dl)
        return '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">{}</div>'.format(bolts)

    elif anim_id == "fire_intense":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">'
            '<div style="position:absolute;bottom:0;left:0;right:0;height:45%;'
            'background:linear-gradient(0deg,{c1} 0%,{c2}88 40%,transparent);'
            'animation:fireRise .5s infinite alternate;pointer-events:none;"></div>'
            '<div style="position:absolute;bottom:0;left:5%;right:5%;height:35%;'
            'background:linear-gradient(0deg,rgba(255,255,0,.6),transparent);'
            'animation:fireRise .4s .1s infinite alternate;pointer-events:none;filter:blur(2px);"></div>'
            '</div>'
        ).format(c1=color1, c2=color2)

    elif anim_id == "nebula_swirl":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">'
            '<div style="position:absolute;inset:-30px;'
            'background:conic-gradient(from 0deg,transparent,{c1}44,transparent,{c2}33,transparent);'
            'animation:nebulaLimited 4s linear infinite;border-radius:50%;pointer-events:none;"></div>'
            '</div>'
        ).format(c1=color1, c2=color2)

    elif anim_id == "rainbow_wave":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9;mix-blend-mode:color-dodge;">'
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(135deg,#ff0000,#ff8800,#ffff00,#00ff00,#00ffff,#0000ff,#8800ff,#ff0000);'
            'background-size:400% 400%;animation:rainbowLimited 3s ease infinite;opacity:.25;pointer-events:none;"></div>'
            '</div>'
        )

    elif anim_id == "holographic_3d":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9;">'
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(135deg,rgba(255,0,150,.2),rgba(0,255,255,.2),rgba(255,255,0,.2),rgba(150,0,255,.2));'
            'background-size:300% 300%;animation:holoLimited 2.5s ease infinite;pointer-events:none;"></div>'
            '</div>'
        )

    elif anim_id == "glitch_effect":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9;">'
            '<div style="position:absolute;inset:0;background:{c1}22;'
            'animation:glitchAnim .8s step-end infinite;pointer-events:none;mix-blend-mode:exclusion;"></div>'
            '<div style="position:absolute;inset:0;background:{c2}22;'
            'animation:glitchAnim .8s .1s step-end infinite;pointer-events:none;mix-blend-mode:exclusion;"></div>'
            '</div>'
        ).format(c1=color1, c2=color2)

    elif anim_id == "cosmic_beam":
        return (
            '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9;">'
            '<div style="position:absolute;inset:-50%;'
            'background:conic-gradient(from 0deg,transparent 0deg,{c1}55 20deg,transparent 40deg,'
            '{c2}44 120deg,transparent 140deg,{c1}33 240deg,transparent 260deg);'
            'animation:cosmicBeam 3s linear infinite;border-radius:50%;pointer-events:none;"></div>'
            '</div>'
        ).format(c1=color1, c2=color2)

    elif anim_id == "ice_crystals":
        parts = ""
        for i in range(10):
            s = (h * (i + 11)) & 0xFFFF
            dx = ((s >> 1) % 41) - 20
            dy = -((s >> 3) % 46) - 10
            rot = (s >> 2) % 360
            dl = (s % 22) / 10.0
            dur = 1.8 + (s >> 4 & 15) / 10.0
            top = 10 + (s >> 5) % 80
            lft = 5 + (s >> 6) % 88
            sz = 0.4 + (s % 5) / 10.0
            parts += (
                '<div style="position:absolute;font-size:{sz}rem;color:#aaddff;'
                'top:{t}%;left:{l}%;animation:iceDrift {dur:.1f}s {dl:.1f}s infinite;'
                '--idx:{dx}px;--idy:{dy}px;--irot:{rot}deg;z-index:9;'
                'text-shadow:0 0 8px #aaddff;">❄</div>'
            ).format(sz=sz, t=top, l=lft, dur=dur, dl=dl, dx=dx, dy=dy, rot=rot)
        return '<div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;border-radius:inherit;z-index:9">{}</div>'.format(parts)

    return ""


def _build_limited_anim_css(anim_ids: list) -> str:
    """Raccoglie i keyframes CSS per le animazioni selezionate."""
    css = ""
    for aid in anim_ids:
        if aid in LIMITED_ANIMATIONS:
            css += LIMITED_ANIMATIONS[aid].get("css_keyframes", "")
    return css


def render_limited_card_html(card_data, size="normal", show_effects=True):
    """Renderizza una carta Limited Edition con forma personalizzata e animazioni."""
    from mbt_rivals import (get_tier_by_ovr, CARD_TIERS, ROLE_ICONS,
                            _get_card_bg_b64, _load_image_b64_cached,
                            calcola_ovr_da_stats)

    ovr = int(card_data.get("overall", 40))
    tier_name = get_tier_by_ovr(ovr)
    ti = CARD_TIERS.get(tier_name, CARD_TIERS["Bronzo Comune"])
    color = card_data.get("custom_color1") or ti["color"]
    color2 = card_data.get("custom_color2") or color
    nome = card_data.get("nome", "?")
    cognome = card_data.get("cognome", "")
    role = card_data.get("ruolo", "SPIKER")
    role_icon = ROLE_ICONS.get(role, "⚡")
    photo_path = card_data.get("foto_path", "")
    card_id = card_data.get("id", "ltd") or "ltd"
    shape_id = card_data.get("card_shape", "classic")
    anim_ids = card_data.get("limited_animations", [])
    glow_size = card_data.get("glow_size", 20)
    photo_scale = card_data.get("photo_scale", 100)
    photo_top = card_data.get("photo_top", 12)

    shape = CARD_SHAPES.get(shape_id, CARD_SHAPES["classic"])
    clip = shape["clip"]
    brad = shape["border_radius"]
    extra_css_shape = shape.get("extra_css", "")

    widths = {"small": "105px", "normal": "140px", "large": "185px"}
    fovrs = {"small": "1.05rem", "normal": "1.4rem", "large": "1.9rem"}
    fnames = {"small": "0.55rem", "normal": "0.72rem", "large": "0.95rem"}
    ffirsts = {"small": "0.32rem", "normal": "0.42rem", "large": "0.52rem"}
    width = widths.get(size, "140px")
    font_ovr = fovrs.get(size, "1.4rem")
    font_name = fnames.get(size, "0.72rem")
    font_first = ffirsts.get(size, "0.42rem")

    # CSS animazioni limited
    anim_css = ""
    anim_overlays = ""
    if show_effects and anim_ids:
        anim_css = _build_limited_anim_css(anim_ids)
        for aid in anim_ids:
            anim_overlays += _gen_limited_overlay(aid, color, color2, card_id)

    # Background
    custom_bg = card_data.get("custom_bg_gradient", "")
    if custom_bg:
        bg_style = "background:{};".format(custom_bg)
    else:
        bg_b64, bg_mime = _get_card_bg_b64(tier_name)
        if bg_b64:
            bg_style = "background-image:url('data:{};base64,{}');background-size:cover;background-position:center top;".format(bg_mime, bg_b64)
        else:
            bg_style = "background:linear-gradient(160deg,{c}33,{c}66,{c}33);".format(c=color)

    bg_div = '<div style="position:absolute;inset:0;{};border-radius:inherit;z-index:0"></div>'.format(bg_style)
    overlay_div = '<div style="position:absolute;inset:0;border-radius:inherit;z-index:1;pointer-events:none;background:linear-gradient(180deg,rgba(0,0,0,.1) 0%,rgba(0,0,0,.05) 35%,rgba(0,0,0,.65) 72%,rgba(0,0,0,.9) 100%)"></div>'

    # Foto
    if photo_path and os.path.exists(str(photo_path)):
        b64_img, mime_img = _load_image_b64_cached(str(photo_path))
        if b64_img:
            foto_html = (
                '<img style="position:absolute!important;top:{tp}%!important;left:0!important;'
                'width:100%!important;height:{h}%!important;object-fit:cover!important;'
                'object-position:center top;border-radius:0!important;z-index:3;'
                'transform:scale({sc});transform-origin:top center;opacity:.93" '
                'src="data:{m};base64,{b}" alt="">'
            ).format(tp=photo_top, h=int(photo_scale * 0.5), sc=photo_scale / 100.0, m=mime_img, b=b64_img)
        else:
            foto_html = '<div style="position:absolute;top:18%;left:50%;transform:translateX(-50%);font-size:2rem;z-index:3">{}</div>'.format(role_icon)
    else:
        foto_html = '<div style="position:absolute;top:18%;left:50%;transform:translateX(-50%);font-size:2rem;z-index:3">{}</div>'.format(role_icon)

    # Stats
    atk = int(card_data.get("attacco", 40))
    dif = int(card_data.get("difesa", 40))
    bat = int(card_data.get("battuta", 40))
    mur = int(card_data.get("muro", 40))
    ric = int(card_data.get("ricezione", 40))
    alz = int(card_data.get("alzata", 40))

    stats_block = (
        '<div style="position:absolute;bottom:3px;left:3px;right:3px;z-index:10">'
        '<div style="display:flex;justify-content:space-around;margin-bottom:1px">'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{atk}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">ATK</div></div>'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{dif}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">DIF</div></div>'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{bat}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">BAT</div></div>'
        '</div>'
        '<div style="display:flex;justify-content:space-around">'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{mur}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">MUR</div></div>'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{ric}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">RIC</div></div>'
        '<div style="text-align:center;flex:1"><div style="font-size:.58rem;font-weight:900;color:{c};line-height:1;text-shadow:0 0 8px {c}">{alz}</div><div style="font-size:.28rem;color:#aaa;letter-spacing:.5px">ALZ</div></div>'
        '</div></div>'
    ).format(c=color, atk=atk, dif=dif, bat=bat, mur=mur, ric=ric, alz=alz)

    tier_short = tier_name.split()[0]

    # Bordo/glow personalizzato
    border_style = "border:2px solid {c};box-shadow:0 0 {g}px {c},0 0 {g2}px {c}55;border-radius:{br};{ex}".format(
        c=color, g=glow_size, g2=glow_size * 2, br=brad, ex=extra_css_shape)

    clip_style = "clip-path:{};".format(clip) if clip != "none" else ""

    # LIMITED badge
    ltd_badge = (
        '<div style="position:absolute;top:6px;right:7px;font-size:.32rem;font-weight:700;'
        'letter-spacing:1px;text-transform:uppercase;z-index:10;color:{c};'
        'text-shadow:0 0 8px {c};background:rgba(0,0,0,.5);padding:1px 4px;border-radius:3px;'
        'border:1px solid {c}">LIMITED</div>'
    ).format(c=color)

    style_tag = "<style>{}</style>".format(anim_css) if anim_css else ""

    html = (
        '{style}'
        '<div style="position:relative;display:inline-block;cursor:pointer;'
        'transition:transform .38s cubic-bezier(.34,1.56,.64,1),filter .38s ease;perspective:800px;'
        'width:{width}">'
        '<div style="width:{width};min-height:210px;border-radius:{br};position:relative;overflow:hidden;'
        'font-family:Orbitron,Rajdhani,sans-serif;user-select:none;{brd}{clip}">'
        '{bg}{overlay}'
        '<div style="position:absolute;top:6px;left:8px;font-family:Orbitron,sans-serif;font-weight:900;'
        'z-index:10;text-shadow:0 0 12px {c},0 2px 4px rgba(0,0,0,.9);line-height:1;'
        'font-size:{fovr};color:{c}">{ovr}</div>'
        '{ltd_badge}'
        '{foto}'
        '<div style="position:absolute;bottom:56px;left:0;right:0;text-align:center;z-index:10;padding:0 4px;line-height:1.1">'
        '<span style="display:block;font-size:{ffirst};font-weight:400;letter-spacing:2px;text-transform:uppercase;opacity:.8;text-shadow:0 0 8px {c};color:{c}">{first}</span>'
        '<span style="display:block;font-weight:900;letter-spacing:1px;text-transform:uppercase;text-shadow:0 0 14px {c};color:{c};font-size:{fname}">{last}</span>'
        '</div>'
        '<div style="position:absolute;bottom:40px;left:0;right:0;text-align:center;font-size:.38rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;z-index:10;opacity:.75;color:{c}">{role_icon} {role}</div>'
        '{stats}'
        '{anim_overlays}'
        '</div></div>'
    ).format(
        style=style_tag, width=width, br=brad, brd=border_style, clip=clip_style,
        bg=bg_div, overlay=overlay_div, c=color, fovr=font_ovr, ovr=ovr,
        ltd_badge=ltd_badge, foto=foto_html,
        ffirst=font_first, fname=font_name,
        first=nome.upper(), last=(cognome or nome).upper(),
        role_icon=role_icon, role=role,
        stats=stats_block, anim_overlays=anim_overlays,
    )
    return html


# ─── DRAFT DATA HELPERS ───────────────────────────────────────────────────────

DRAFT_DB_FILE = "mbt_draft_cards.json"


def load_draft_db():
    if Path(DRAFT_DB_FILE).exists():
        with open(DRAFT_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": [], "next_id": 1}


def save_draft_db(db):
    with open(DRAFT_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _pick_draft_prize(difficulty_name: str, draft_db: dict, cards_db: dict) -> dict:
    """Seleziona una carta premio dal DB (Limited prima, poi normale)."""
    diff = DRAFT_DIFFICULTIES[difficulty_name]
    prize_tiers = diff["prize_tiers"]

    # Prova prima con Limited Edition
    ltd_cards = [c for c in draft_db.get("cards", []) if get_tier_by_ovr(c.get("overall", 40)) in prize_tiers]
    if ltd_cards:
        return random.choice(ltd_cards).copy()

    # Fallback su carte normali
    all_normal = [c for c in cards_db.get("cards", []) if get_tier_by_ovr(c.get("overall", 40)) in prize_tiers]
    if all_normal:
        return random.choice(all_normal).copy()

    # Fallback generato
    tier = random.choice(prize_tiers)
    from mbt_rivals import CARD_TIERS
    lo, hi = CARD_TIERS.get(tier, {}).get("ovr_range", (70, 80))
    ovr = random.randint(lo, hi)
    return {
        "id": "draft_prize_{}".format(random.randint(10000, 99999)),
        "nome": random.choice(["Marco", "Luca", "Sara", "Giulia", "Andrea"]),
        "cognome": random.choice(["Rossi", "Bianchi", "Ferrari", "Costa"]),
        "overall": ovr, "ruolo": "SPIKER",
        "attacco": max(40, ovr - 5), "difesa": max(40, ovr - 8),
        "battuta": max(40, ovr - 6), "muro": max(40, ovr - 10),
        "ricezione": max(40, ovr - 7), "alzata": max(40, ovr - 9),
        "foto_path": "", "tier": tier,
    }


def get_tier_by_ovr(ovr):
    """Wrapper locale per evitare import circolari durante esecuzione."""
    try:
        from mbt_rivals import get_tier_by_ovr as _g
        return _g(ovr)
    except Exception:
        ovr = int(ovr)
        if ovr >= 120: return "ICON GOD"
        if ovr >= 115: return "ICON TOTY"
        if ovr >= 110: return "ICON LEGGENDARIA"
        if ovr >= 105: return "ICON EPICA"
        if ovr >= 100: return "ICON BASE"
        if ovr >= 95: return "GOAT"
        if ovr >= 90: return "TOTY Evoluto"
        if ovr >= 85: return "TOTY"
        if ovr >= 80: return "Leggenda"
        if ovr >= 75: return "IF (In Form)"
        if ovr >= 70: return "Eroe"
        if ovr >= 65: return "Oro Raro"
        if ovr >= 60: return "Oro Comune"
        if ovr >= 55: return "Argento Raro"
        if ovr >= 50: return "Argento Comune"
        if ovr >= 45: return "Bronzo Raro"
        return "Bronzo Comune"


# ─── DRAFT BATTLE ENGINE ─────────────────────────────────────────────────────

def init_draft_battle(player_cards: list, diff_name: str, step: int) -> dict:
    diff = DRAFT_DIFFICULTIES[diff_name]
    lo, hi = diff["cpu_ovr_range"]
    step_boost = diff["ovr_step_increase"] * step
    cpu_ovr = min(125, random.randint(lo, hi) + step_boost)

    cpu_card = {
        "nome": random.choice(["Alpha", "Titan", "Storm", "Nova", "Ace"]),
        "cognome": random.choice(["X", "ZERO", "PRIME", "MAX", "ULTRA"]),
        "overall": cpu_ovr, "ruolo": random.choice(["SPIKER", "IRONBLOCKER", "DIFENSORE", "ACER"]),
        "attacco": max(40, cpu_ovr - random.randint(0, 8)),
        "difesa": max(40, cpu_ovr - random.randint(0, 10)),
        "battuta": max(40, cpu_ovr - random.randint(0, 9)),
        "muro": max(40, cpu_ovr - random.randint(0, 12)),
        "ricezione": max(40, cpu_ovr - random.randint(0, 11)),
        "alzata": max(40, cpu_ovr - random.randint(0, 13)),
        "foto_path": "",
    }

    p_card = player_cards[0] if player_cards else cpu_card.copy()
    base_hp_p = 80 + int(p_card.get("overall", 40)) * 2
    base_hp_c = 80 + cpu_ovr * 2

    return {
        "player_card": p_card, "cpu_card": cpu_card,
        "player_hp": base_hp_p, "player_max_hp": base_hp_p,
        "cpu_hp": base_hp_c, "cpu_max_hp": base_hp_c,
        "player_stamina": 100, "turn": 0,
        "stamina_charges": 0, "phase": "battle", "log": [],
    }


def process_draft_action(bs: dict, action: str) -> dict:
    from mbt_rivals import calculate_damage
    p_card = bs["player_card"]
    c_card = bs["cpu_card"]
    log = bs["log"]
    p_name = p_card.get("nome", "Player")
    c_name = c_card.get("nome", "CPU")

    if action == "attack":
        dmg = calculate_damage(p_card, c_card, "attack")
        bs["cpu_hp"] = max(0, bs["cpu_hp"] - dmg)
        bs["player_stamina"] = min(100, bs["player_stamina"] + 10)
        bs["stamina_charges"] = min(10, bs["stamina_charges"] + 1)
        log.append("⚡ {} attacca → {} danni! (CPU HP: {})".format(p_name, dmg, bs["cpu_hp"]))
    elif action == "special":
        if bs["player_stamina"] >= 40:
            dmg = calculate_damage(p_card, c_card, "special")
            bs["cpu_hp"] = max(0, bs["cpu_hp"] - dmg)
            bs["player_stamina"] -= 40
            log.append("🔥 SUPER ATTACCO → {} danni!".format(dmg))
        else:
            log.append("⚠️ Stamina insufficiente!")
    elif action == "defend":
        bs["player_stamina"] = min(100, bs["player_stamina"] + 20)
        log.append("🛡️ {} si difende e recupera stamina!".format(p_name))
    elif action == "final":
        if bs["stamina_charges"] >= 5:
            dmg = calculate_damage(p_card, c_card, "super")
            bs["cpu_hp"] = max(0, bs["cpu_hp"] - dmg)
            bs["stamina_charges"] = 0
            log.append("💥 MOSSA FINALE! {} danni!".format(dmg))
        else:
            log.append("⚠️ Carica ancora ({}/5 cariche)!".format(bs["stamina_charges"]))

    if bs["cpu_hp"] <= 0:
        bs["phase"] = "win"
        log.append("✅ Tappa superata!")
        return bs

    # CPU move
    cpu_action = random.choices(
        ["attack", "attack", "special", "defend"],
        weights=[0.5, 0.25, 0.15, 0.10]
    )[0]
    if cpu_action in ("attack", "special"):
        move_type = "special" if cpu_action == "special" else "attack"
        cpu_dmg = calculate_damage(c_card, p_card, move_type)
        bs["player_hp"] = max(0, bs["player_hp"] - cpu_dmg)
        em = "💫" if move_type == "special" else "🤖"
        log.append("{} {} → {} danni! (Player HP: {})".format(em, c_name, cpu_dmg, bs["player_hp"]))
    else:
        log.append("🤖 {} si difende!".format(c_name))

    if bs["player_hp"] <= 0:
        bs["phase"] = "lose"
        log.append("💀 Eliminato! Draft terminato.")

    bs["turn"] += 1
    if len(log) > 15:
        bs["log"] = log[-15:]
    return bs


# ─── DRAFT CSS ────────────────────────────────────────────────────────────────

DRAFT_CSS = """
<style>
@keyframes draftCardReveal{
  0%{transform:scale(.3) rotateY(180deg);opacity:0;filter:brightness(5) blur(8px)}
  50%{transform:scale(1.2) rotateY(10deg);opacity:1;filter:brightness(2) blur(1px)}
  100%{transform:scale(1) rotateY(0deg);opacity:1;filter:brightness(1) blur(0)}
}
@keyframes mysteryPulse{
  0%,100%{box-shadow:0 0 20px #ffd700,0 0 50px #ffd70066;transform:scale(1)}
  50%{box-shadow:0 0 40px #ffd700,0 0 100px #ffd70099;transform:scale(1.04)}
}
@keyframes pathGlow{
  0%,100%{opacity:.6}50%{opacity:1}
}
@keyframes winnerGlow{
  0%{box-shadow:0 0 30px #ffd700,0 0 80px #ffd700;background:rgba(255,215,0,.1)}
  50%{box-shadow:0 0 80px #ffd700,0 0 200px #ffd700,0 0 300px #ffd70055;background:rgba(255,215,0,.2)}
  100%{box-shadow:0 0 30px #ffd700,0 0 80px #ffd700;background:rgba(255,215,0,.1)}
}
@keyframes sandBlast{
  0%{transform:translateY(0) scale(1);opacity:1}
  100%{transform:translateY(-100px) scale(2);opacity:0}
}
@keyframes draftBtnHover{
  0%,100%{transform:scale(1)}50%{transform:scale(1.03)}
}
.draft-step-node{
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-family:Orbitron,sans-serif;font-weight:900;transition:all .4s;
  position:relative;cursor:default;
}
.draft-step-done{background:#16a34a;border:3px solid #4ade80;color:#fff;box-shadow:0 0 12px #16a34a}
.draft-step-active{background:#ffd700;border:3px solid #fff;color:#000;
  box-shadow:0 0 20px #ffd700,0 0 40px #ffd70055;animation:mysteryPulse 1.5s infinite}
.draft-step-locked{background:#1a1a2a;border:2px dashed #333;color:#444}
.draft-mystery-card{
  animation:mysteryPulse 2s infinite;
  border-radius:14px;
}
.draft-card-reveal{animation:draftCardReveal 1.2s cubic-bezier(.34,1.56,.64,1) both}
.draft-winner-overlay{animation:winnerGlow 1.5s infinite;border-radius:16px;padding:30px;text-align:center}
</style>
"""


# ─── RENDER DRAFT TAB ─────────────────────────────────────────────────────────

def render_draft_tab(rivals_data: dict, cards_db: dict, draft_db: dict):
    """Punto di ingresso principale — mostra i sub-tab del Draft."""
    st.markdown(DRAFT_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="background:linear-gradient(135deg,#050510,#0a0020,#050510);
      border:2px solid #ffd700;border-radius:12px;padding:14px 20px;margin-bottom:16px">
      <div style="font-family:Orbitron,sans-serif;font-size:1.4rem;font-weight:900;
        background:linear-gradient(90deg,#ffd700,#ffec4a,#ffd700);background-size:200% auto;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        animation:goldShine 3s linear infinite">🏅 LA SCALATA DEL DRAFT</div>
      <div style="font-size:.7rem;color:#888;letter-spacing:2px;margin-top:4px">
        7 TAPPE · CARTE LIMITED EDITION ESCLUSIVE · DIFFICOLTÀ CRESCENTE
      </div>
    </div>
    """, unsafe_allow_html=True)

    d_tabs = st.tabs(["🎯 Gioca Draft", "🃏 Carte Limited", "⚙️ Admin Draft"])
    with d_tabs[0]:
        _render_draft_play(rivals_data, cards_db, draft_db)
    with d_tabs[1]:
        _render_draft_collection(rivals_data, draft_db)
    with d_tabs[2]:
        _render_draft_admin(draft_db)


# ─── DRAFT PLAY ───────────────────────────────────────────────────────────────

def _render_draft_play(rivals_data: dict, cards_db: dict, draft_db: dict):
    ds = st.session_state.get("draft_state")

    # ── Nessun draft attivo: scelta difficoltà ──
    if ds is None:
        st.markdown("### 🎯 Scegli la Difficoltà")
        st.caption("Affronta 7 tappe consecutive. Perdi una tappa → Draft finito. Vinci tutto → Carta esclusiva!")

        diff_names = list(DRAFT_DIFFICULTIES.keys())
        cols = st.columns(3)
        for i, name in enumerate(diff_names):
            diff = DRAFT_DIFFICULTIES[name]
            with cols[i % 3]:
                border = "border:3px solid {};".format(diff["color"])
                bg = "background:linear-gradient(135deg,rgba(0,0,0,.8),{}22);".format(diff["color"])
                st.markdown("""
                <div style="{bg}{border}border-radius:12px;padding:14px;margin-bottom:8px;
                  text-align:center;cursor:pointer;transition:transform .2s">
                  <div style="font-size:2rem">{icon}</div>
                  <div style="font-family:Orbitron,sans-serif;font-weight:700;
                    color:{color};font-size:.85rem;margin-top:4px">{name}</div>
                  <div style="font-size:.6rem;color:#888;margin-top:6px">{desc}</div>
                  <div style="font-size:.6rem;color:{color};margin-top:6px;font-weight:600">
                    🪙 +{coins} | ⭐ +{xp} XP
                  </div>
                </div>
                """.format(
                    bg=bg, border=border, icon=diff["icon"], color=diff["color"],
                    name=name, desc=diff["desc"], coins=diff["coins_bonus"], xp=diff["xp_bonus"]
                ), unsafe_allow_html=True)

                if st.button("{} Inizia {}".format(diff["icon"], name),
                             key="start_draft_{}".format(name), use_container_width=True):
                    # Prendi squadra attiva
                    active_ids = rivals_data.get("active_team", [])
                    all_c = cards_db.get("cards", [])
                    team = [c for c in all_c if c.get("id") in active_ids or c.get("instance_id") in active_ids]
                    if not team:
                        st.error("⚠️ Seleziona almeno una carta nella Squadra Attiva (sezione Collezione)!")
                    else:
                        prize = _pick_draft_prize(name, draft_db, cards_db)
                        st.session_state.draft_state = {
                            "difficulty": name,
                            "step": 0,           # tappa corrente (0-6)
                            "wins": 0,
                            "team": team,
                            "prize": prize,
                            "phase": "choose_action",  # choose_action | battle | win_step | lose | final_win
                            "battle": None,
                            "revealed": False,
                        }
                        st.rerun()
        return

    # ── Draft attivo ──
    _render_active_draft(ds, rivals_data, cards_db, draft_db)


def _render_active_draft(ds: dict, rivals_data: dict, cards_db: dict, draft_db: dict):
    diff_name = ds["difficulty"]
    diff = DRAFT_DIFFICULTIES[diff_name]
    step = ds["step"]
    phase = ds["phase"]

    # ── Progress bar tappe ──────────────────────────────────────────────────
    st.markdown("#### 🏅 Percorso Draft — {} | Tappa {}/{}".format(diff_name, step + 1, DRAFT_STEPS))
    node_cols = st.columns(DRAFT_STEPS)
    for i in range(DRAFT_STEPS):
        with node_cols[i]:
            if i < step:
                cls = "draft-step-done"
                lbl = "✓"
            elif i == step:
                cls = "draft-step-active"
                lbl = str(i + 1)
            else:
                cls = "draft-step-locked"
                lbl = str(i + 1)
            st.markdown(
                '<div class="draft-step-node {} " style="width:38px;height:38px;font-size:.75rem;margin:auto">{}</div>'.format(cls, lbl),
                unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Carta misteriosa in palio ──────────────────────────────────────────
    prize = ds["prize"]
    col_prize, col_battle = st.columns([1, 2])
    with col_prize:
        st.markdown("##### 🎁 Premio in palio")
        if ds.get("revealed"):
            # Mostra la carta vera con animazione
            prize_is_limited = bool(prize.get("card_shape") or prize.get("limited_animations"))
            if prize_is_limited:
                st.markdown('<div class="draft-card-reveal">{}</div>'.format(
                    render_limited_card_html(prize, size="normal")), unsafe_allow_html=True)
            else:
                from mbt_rivals import render_card_html
                st.markdown('<div class="draft-card-reveal">{}</div>'.format(
                    render_card_html(prize, size="normal")), unsafe_allow_html=True)
        else:
            # Dorso misterioso pulsante
            tier_color = diff["color"]
            progress_pct = int(step / DRAFT_STEPS * 100)
            glow_size = 10 + int(step * 8)
            st.markdown("""
            <div class="draft-mystery-card" style="
              width:140px;min-height:210px;border-radius:14px;margin:0 auto;
              background:linear-gradient(135deg,#0a0a1a,#1a0a30,#0a0a1a);
              border:2px solid {tc};
              box-shadow:0 0 {gs}px {tc},0 0 {gs2}px {tc}55;
              display:flex;flex-direction:column;align-items:center;justify-content:center;
              position:relative;overflow:hidden">
              <div style="font-size:3rem;z-index:2">🏐</div>
              <div style="font-family:Orbitron,sans-serif;font-size:.55rem;color:{tc};
                letter-spacing:2px;margin-top:8px;z-index:2">CARTA MISTERIOSA</div>
              <div style="position:absolute;bottom:0;left:0;height:{pp}%;width:100%;
                background:linear-gradient(0deg,{tc}33,transparent);transition:height 1s;z-index:1"></div>
              <div style="position:absolute;inset:0;background:linear-gradient(45deg,
                transparent 30%,{tc}15 50%,transparent 70%);
                background-size:200% 200%;animation:goldShine 3s linear infinite;z-index:1"></div>
            </div>
            """.format(tc=tier_color, gs=glow_size, gs2=glow_size * 2, pp=progress_pct), unsafe_allow_html=True)
            st.caption("Si rivelerà alla vittoria finale!")

    # ── Fase di combattimento ──────────────────────────────────────────────
    with col_battle:
        if phase == "choose_action":
            st.markdown("##### ⚔️ Tappa {} — Scegli la tua mossa".format(step + 1))
            cpu_ovr = diff["cpu_ovr_range"][0] + diff["ovr_step_increase"] * step
            st.info("🤖 CPU di questa tappa: OVR ~{} (difficoltà crescente)".format(cpu_ovr))

            team = ds["team"]
            team_cols = st.columns(min(3, len(team)))
            for ti, tc in enumerate(team[:3]):
                with team_cols[ti]:
                    from mbt_rivals import render_card_html
                    st.markdown(render_card_html(tc, size="small"), unsafe_allow_html=True)

            if st.button("⚔️ AFFRONTA TAPPA {}".format(step + 1),
                         key="draft_start_step", use_container_width=True, type="primary"):
                ds["battle"] = init_draft_battle(team, diff_name, step)
                ds["phase"] = "battle"
                st.rerun()

            if st.button("🏳️ Abbandona Draft", key="draft_quit"):
                st.session_state.draft_state = None
                st.rerun()

        elif phase == "battle" and ds.get("battle"):
            bs = ds["battle"]
            _render_draft_battle_ui(bs, ds)

        elif phase == "win_step":
            st.markdown("""
            <div style="background:linear-gradient(135deg,#001a00,#003300);
              border:2px solid #16a34a;border-radius:12px;padding:20px;text-align:center">
              <div style="font-size:2rem">✅</div>
              <div style="font-family:Orbitron,sans-serif;color:#4ade80;font-weight:700;font-size:1rem">
                TAPPA {} SUPERATA!
              </div>
              <div style="font-size:.7rem;color:#888;margin-top:6px">
                {}/{} tappe completate
              </div>
            </div>
            """.format(step, step, DRAFT_STEPS), unsafe_allow_html=True)

            if st.button("➡️ Prossima Tappa", key="draft_next", use_container_width=True, type="primary"):
                ds["step"] += 1
                ds["wins"] += 1
                ds["battle"] = None
                if ds["step"] >= DRAFT_STEPS:
                    ds["phase"] = "final_win"
                    ds["revealed"] = True
                else:
                    ds["phase"] = "choose_action"
                st.rerun()

        elif phase == "lose":
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a0000,#330000);
              border:2px solid #dc2626;border-radius:12px;padding:20px;text-align:center">
              <div style="font-size:2rem">💀</div>
              <div style="font-family:Orbitron,sans-serif;color:#ef4444;font-weight:700;font-size:1rem">
                DRAFT TERMINATO!
              </div>
              <div style="font-size:.7rem;color:#888;margin-top:6px">
                Sei arrivato alla tappa {}/{}
              </div>
            </div>
            """.format(step + 1, DRAFT_STEPS), unsafe_allow_html=True)

            cons_coins = diff["coins_bonus"] // 4
            rivals_data["mbt_coins"] = rivals_data.get("mbt_coins", 0) + cons_coins
            rivals_data["player_xp"] = rivals_data.get("player_xp", 0) + diff["xp_bonus"] // 4
            st.info("Premio consolazione: 🪙 +{} coins | ⭐ +{} XP".format(cons_coins, diff["xp_bonus"] // 4))

            if st.button("🔄 Nuovo Draft", key="draft_retry", use_container_width=True):
                st.session_state.draft_state = None
                st.rerun()

        elif phase == "final_win":
            _render_draft_final_win(ds, rivals_data, draft_db, cards_db, diff)


def _render_draft_battle_ui(bs: dict, ds: dict):
    """Interfaccia di battaglia per una singola tappa del Draft."""
    p_hp_pct = int(bs["player_hp"] / max(1, bs["player_max_hp"]) * 100)
    c_hp_pct = int(bs["cpu_hp"] / max(1, bs["cpu_max_hp"]) * 100)

    col_p, col_vs, col_c = st.columns([5, 1, 5])
    with col_p:
        from mbt_rivals import render_card_html
        st.markdown(render_card_html(bs["player_card"], size="small"), unsafe_allow_html=True)
        st.markdown('<div style="height:6px;background:#1a1a2a;border-radius:3px;overflow:hidden;margin-top:4px"><div style="width:{}%;height:100%;background:linear-gradient(90deg,{},#4ade80);border-radius:3px"></div></div>'.format(
            p_hp_pct, "#dc2626" if p_hp_pct < 30 else "#16a34a"), unsafe_allow_html=True)
        st.caption("HP: {}/{} | STA: {}%".format(bs["player_hp"], bs["player_max_hp"], bs["player_stamina"]))

    with col_vs:
        st.markdown('<div style="text-align:center;padding-top:30px;font-family:Orbitron,sans-serif;font-weight:900;color:#dc2626;font-size:1rem">VS</div>', unsafe_allow_html=True)
        st.caption("T.{}".format(bs["turn"]))

    with col_c:
        st.markdown(render_card_html(bs["cpu_card"], size="small", show_special_effects=False), unsafe_allow_html=True)
        st.markdown('<div style="height:6px;background:#1a1a2a;border-radius:3px;overflow:hidden;margin-top:4px"><div style="width:{}%;height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:3px"></div></div>'.format(c_hp_pct), unsafe_allow_html=True)
        st.caption("HP: {}/{}".format(bs["cpu_hp"], bs["cpu_max_hp"]))

    # Bottoni azione
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("⚡ Attacca", key="db_atk", use_container_width=True):
            ds["battle"] = process_draft_action(bs, "attack")
            _check_draft_battle_end(ds)
            st.rerun()
    with a2:
        can_sp = bs["player_stamina"] >= 40
        if st.button("🔥 Super" + ("✓" if can_sp else "✗"), key="db_sp",
                     disabled=not can_sp, use_container_width=True):
            ds["battle"] = process_draft_action(bs, "special")
            _check_draft_battle_end(ds)
            st.rerun()
    with a3:
        if st.button("🛡️ Difendi", key="db_def", use_container_width=True):
            ds["battle"] = process_draft_action(bs, "defend")
            st.rerun()
    with a4:
        can_fin = bs["stamina_charges"] >= 5
        if st.button("💥 Finale {}/5".format(bs["stamina_charges"]), key="db_fin",
                     disabled=not can_fin, use_container_width=True):
            ds["battle"] = process_draft_action(bs, "final")
            _check_draft_battle_end(ds)
            st.rerun()

    # Log
    if bs["log"]:
        with st.expander("📋 Log", expanded=False):
            for e in reversed(bs["log"][-6:]):
                st.markdown('<div style="font-size:.65rem;color:#ccc;padding:2px 0;border-bottom:1px solid #1a1a2a">{}</div>'.format(e), unsafe_allow_html=True)


def _check_draft_battle_end(ds: dict):
    bs = ds.get("battle", {})
    if bs and bs.get("phase") == "win":
        ds["phase"] = "win_step"
    elif bs and bs.get("phase") == "lose":
        ds["phase"] = "lose"


def _render_draft_final_win(ds: dict, rivals_data: dict, draft_db: dict, cards_db: dict, diff: dict):
    """Animazione finale e consegna carta."""
    prize = ds["prize"]
    prize_is_limited = bool(prize.get("card_shape") or prize.get("limited_animations"))

    st.markdown("""
    <div class="draft-winner-overlay" style="background:rgba(255,215,0,.1);border:3px solid #ffd700;border-radius:16px;padding:30px;text-align:center;margin-bottom:16px">
      <div style="font-size:3rem">🏆</div>
      <div style="font-family:Orbitron,sans-serif;font-size:1.6rem;font-weight:900;
        background:linear-gradient(90deg,#ffd700,#fff,#ffd700);background-size:200% auto;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        animation:goldShine 2s linear infinite">
        DRAFT COMPLETATO!
      </div>
      <div style="font-size:.75rem;color:#888;margin-top:8px">7/7 TAPPE SUPERATE — HAI VINTO!</div>
    </div>
    """, unsafe_allow_html=True)

    # Effetto sabbia che esplode + reveal carta
    st.markdown("""
    <div style="text-align:center;margin:16px 0;position:relative">
      <div style="font-size:1rem;color:#ffd700;font-family:Orbitron,sans-serif;
        letter-spacing:3px;animation:mysteryPulse 1s infinite;margin-bottom:12px">
        ✨ LA TUA CARTA ESCLUSIVA ✨
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if prize_is_limited:
            st.markdown('<div class="draft-card-reveal" style="display:flex;justify-content:center">{}</div>'.format(
                render_limited_card_html(prize, size="large")), unsafe_allow_html=True)
        else:
            from mbt_rivals import render_card_html
            st.markdown('<div class="draft-card-reveal" style="display:flex;justify-content:center">{}</div>'.format(
                render_card_html(prize, size="large")), unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;margin-top:12px"><span style="font-family:Orbitron,sans-serif;color:#ffd700;font-size:.8rem">{} {} — OVR {} — {}</span></div>'.format(
        prize.get("nome", ""), prize.get("cognome", ""),
        prize.get("overall", "?"),
        "LIMITED EDITION ⭐" if prize_is_limited else get_tier_by_ovr(prize.get("overall", 40))
    ), unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        coins_gain = diff["coins_bonus"]
        xp_gain = diff["xp_bonus"]
        st.success("🪙 +{} Coins | ⭐ +{} XP".format(coins_gain, xp_gain))
    with col_b:
        if st.button("✅ RITIRA CARTA & CONTINUA", key="draft_collect", use_container_width=True, type="primary"):
            # Aggiungi alla collezione
            pid = prize.get("id", "prize_{}".format(random.randint(10000, 99999)))
            prize["id"] = pid
            rivals_data["collection"] = rivals_data.get("collection", [])
            if pid not in rivals_data["collection"]:
                rivals_data["collection"].append(pid)
                # Aggiungi anche al cards_db se non presente
                all_ids = [c.get("id") for c in cards_db.get("cards", [])]
                if pid not in all_ids:
                    cards_db["cards"].append(prize)

            rivals_data["mbt_coins"] = rivals_data.get("mbt_coins", 0) + diff["coins_bonus"]
            rivals_data["player_xp"] = rivals_data.get("player_xp", 0) + diff["xp_bonus"]
            st.session_state.draft_state = None
            st.rerun()


# ─── DRAFT COLLECTION ─────────────────────────────────────────────────────────

def _render_draft_collection(rivals_data: dict, draft_db: dict):
    st.markdown("### 🃏 Carte Limited Edition Vinte")
    owned_ids = rivals_data.get("collection", [])
    ltd_cards = [c for c in draft_db.get("cards", [])
                 if c.get("id") in owned_ids or c.get("card_shape") or c.get("limited_animations")]

    # Mostra anche le limited vinte (già nel cards_db principale)
    st.caption("Carte Limited Edition create dall'Admin e disponibili come premi Draft.")

    all_ltd = draft_db.get("cards", [])
    if not all_ltd:
        st.info("📦 Nessuna carta Limited Edition creata ancora. L'Admin può crearne nell'**Admin Draft**.")
        return

    cols_per_row = 4
    for i in range(0, len(all_ltd), cols_per_row):
        chunk = all_ltd[i:i + cols_per_row]
        rcols = st.columns(cols_per_row)
        for j, card in enumerate(chunk):
            with rcols[j]:
                st.markdown(render_limited_card_html(card, size="normal"), unsafe_allow_html=True)
                is_owned = card.get("id") in owned_ids
                if is_owned:
                    st.markdown('<div style="text-align:center;font-size:.6rem;color:#4ade80">✅ Posseduta</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align:center;font-size:.6rem;color:#888">🔒 Vinci nel Draft</div>', unsafe_allow_html=True)


# ─── ADMIN DRAFT ──────────────────────────────────────────────────────────────

def _render_draft_admin(draft_db: dict):
    st.markdown("### ⚙️ Admin Draft — Crea Carte Limited Edition")
    st.caption("Queste carte sono ESCLUSIVE: non si trovano nei pacchetti normali. Solo il Draft le assegna come premio.")

    admin_sub = st.tabs(["➕ Crea Carta Limited", "📋 Gestisci Limited"])

    with admin_sub[0]:
        _render_limited_card_creator(draft_db)

    with admin_sub[1]:
        _render_limited_card_manager(draft_db)


def _render_limited_card_creator(draft_db: dict):
    st.markdown("#### ✨ Editor Carta Limited Edition")

    col_form, col_prev = st.columns([2, 1])

    with col_form:
        # ── Dati base ──
        with st.expander("📝 Dati Giocatore & Statistiche", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                ltd_nome = st.text_input("Nome", key="ltd_nome")
                ltd_cog = st.text_input("Cognome", key="ltd_cog")
            with c2:
                from mbt_rivals import ROLES
                ltd_ruolo = st.selectbox("Ruolo", ROLES, key="ltd_ruolo")
            c3, c4 = st.columns(2)
            with c3:
                ltd_atk = st.slider("ATK", 0, 125, 85, key="ltd_atk")
                ltd_dif = st.slider("DIF", 0, 125, 82, key="ltd_dif")
                ltd_ric = st.slider("RIC", 0, 125, 80, key="ltd_ric")
            with c4:
                ltd_bat = st.slider("BAT", 0, 125, 83, key="ltd_bat")
                ltd_mur = st.slider("MUR", 0, 125, 78, key="ltd_mur")
                ltd_alz = st.slider("ALZ", 0, 125, 76, key="ltd_alz")

            from mbt_rivals import calcola_ovr_da_stats, get_tier_by_ovr, CARD_TIERS
            ltd_ovr = calcola_ovr_da_stats(ltd_atk, ltd_dif, ltd_ric, ltd_bat, ltd_mur, ltd_alz)
            ltd_tier = get_tier_by_ovr(ltd_ovr)
            ltd_tier_color = CARD_TIERS.get(ltd_tier, {}).get("color", "#ffd700")
            st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:.85rem;color:{};font-weight:700">OVR: {} | {}</div>'.format(ltd_tier_color, ltd_ovr, ltd_tier), unsafe_allow_html=True)

        # ── Upload foto ──
        with st.expander("📷 Foto & Personalizzazione Visiva", expanded=True):
            ltd_foto_file = st.file_uploader("Foto Giocatore", type=["png", "jpg", "jpeg"], key="ltd_foto")
            ltd_foto_path = ""
            if ltd_foto_file:
                from mbt_rivals import ASSETS_ICONS_DIR
                os.makedirs(ASSETS_ICONS_DIR, exist_ok=True)
                ext = ltd_foto_file.name.rsplit(".", 1)[-1].lower()
                ltd_foto_path = os.path.join(ASSETS_ICONS_DIR, "ltd_{}_{}_{}.{}".format(
                    ltd_nome or "ltd", ltd_cog or "card", random.randint(1000, 9999), ext))
                with open(ltd_foto_path, "wb") as f:
                    f.write(ltd_foto_file.read())
                st.success("✅ Foto salvata")

            col_col1, col_col2 = st.columns(2)
            with col_col1:
                ltd_color1 = st.color_picker("Colore Primario", "#ffd700", key="ltd_c1")
                ltd_photo_scale = st.slider("Scala Foto (%)", 60, 150, 100, key="ltd_pscale")
            with col_col2:
                ltd_color2 = st.color_picker("Colore Secondario", "#ff6600", key="ltd_c2")
                ltd_photo_top = st.slider("Posizione Foto (top %)", 0, 40, 12, key="ltd_ptop")

            ltd_glow = st.slider("Intensità Glow (px)", 5, 60, 20, key="ltd_glow")

            # Gradient background custom
            ltd_use_custom_bg = st.checkbox("Usa Gradient Background custom", key="ltd_custom_bg")
            ltd_bg_grad = ""
            if ltd_use_custom_bg:
                ltd_bg_grad = st.text_input(
                    "CSS Gradient (es: linear-gradient(160deg,#1a0030,#4a0080,#1a0030))",
                    value="linear-gradient(160deg,#1a0030,#4a0080,#1a0030)", key="ltd_bg_grad_val")

        # ── Scelta forma ──
        with st.expander("🃏 Forma della Carta — Galleria 50 Stili", expanded=False):
            groups = {}
            for sid, sdata in CARD_SHAPES.items():
                g = sdata.get("group", "Altro")
                groups.setdefault(g, []).append((sid, sdata))

            for grp_name, grp_shapes in groups.items():
                st.markdown("**{}**".format(grp_name))
                gcols = st.columns(min(5, len(grp_shapes)))
                for gi, (sid, sdata) in enumerate(grp_shapes):
                    with gcols[gi % 5]:
                        is_sel = st.session_state.get("ltd_selected_shape") == sid
                        bg = "background:rgba(255,215,0,.15);border:2px solid #ffd700;" if is_sel else "background:#1a1a2a;border:1px solid #333;"
                        st.markdown("""
                        <div style="{bg}border-radius:8px;padding:8px;text-align:center;cursor:pointer;margin-bottom:4px">
                          <div style="font-size:.6rem;color:{col}font-weight:{fw}">{nm}</div>
                        </div>
                        """.format(bg=bg, col="#ffd700;" if is_sel else "#888;", fw="700" if is_sel else "400", nm=sdata["name"]), unsafe_allow_html=True)
                        if st.button("✓" if is_sel else sdata["name"][:8], key="shape_sel_{}_{}".format(grp_name, sid), use_container_width=True):
                            st.session_state.ltd_selected_shape = sid
                            st.rerun()

            selected_shape = st.session_state.get("ltd_selected_shape", "classic")
            st.info("📐 Forma selezionata: **{}**".format(CARD_SHAPES.get(selected_shape, {}).get("name", "Classic")))

        # ── Selezione animazioni ──
        with st.expander("✨ Animazioni Speciali (10 effetti)", expanded=False):
            if "ltd_sel_anims" not in st.session_state:
                st.session_state.ltd_sel_anims = []

            anim_groups = {}
            for aid, adata in LIMITED_ANIMATIONS.items():
                g = adata.get("group", "Altro")
                anim_groups.setdefault(g, []).append((aid, adata))

            for grp_name, grp_anims in anim_groups.items():
                st.markdown("**{}**".format(grp_name))
                acols = st.columns(min(3, len(grp_anims)))
                for ai, (aid, adata) in enumerate(grp_anims):
                    with acols[ai % 3]:
                        is_active = aid in st.session_state.ltd_sel_anims
                        bg = "background:rgba(255,215,0,.12);border:2px solid #ffd700;" if is_active else "background:#0a0a15;border:1px solid #1e1e3a;"
                        st.markdown("""
                        <div style="{}border-radius:8px;padding:8px;margin-bottom:4px">
                          <div style="font-size:.65rem;font-weight:700;color:{}">{}</div>
                        </div>
                        """.format(bg, "#ffd700" if is_active else "#888", adata["name"]), unsafe_allow_html=True)
                        lbl = "✅ Rimuovi" if is_active else "➕ Aggiungi"
                        if st.button(lbl, key="ltd_anim_{}_{}".format(grp_name, aid), use_container_width=True):
                            if is_active:
                                st.session_state.ltd_sel_anims.remove(aid)
                            else:
                                st.session_state.ltd_sel_anims.append(aid)
                            st.rerun()

            if st.session_state.ltd_sel_anims:
                st.markdown("**Animazioni attive:** " + " | ".join(
                    LIMITED_ANIMATIONS.get(a, {}).get("name", a) for a in st.session_state.ltd_sel_anims))
                if st.button("🗑️ Rimuovi tutte", key="ltd_clear_anims"):
                    st.session_state.ltd_sel_anims = []
                    st.rerun()

    # ── Preview live ──
    with col_prev:
        st.markdown("#### 👁️ Anteprima")
        preview_ltd = {
            "id": "ltd_preview",
            "nome": ltd_nome or "NOME",
            "cognome": ltd_cog or "",
            "overall": ltd_ovr,
            "ruolo": ltd_ruolo,
            "attacco": ltd_atk, "difesa": ltd_dif, "battuta": ltd_bat,
            "muro": ltd_mur, "ricezione": ltd_ric, "alzata": ltd_alz,
            "foto_path": ltd_foto_path,
            "custom_color1": ltd_color1,
            "custom_color2": ltd_color2,
            "card_shape": st.session_state.get("ltd_selected_shape", "classic"),
            "limited_animations": list(st.session_state.get("ltd_sel_anims", [])),
            "glow_size": ltd_glow,
            "photo_scale": ltd_photo_scale,
            "photo_top": ltd_photo_top,
            "custom_bg_gradient": ltd_bg_grad if ltd_use_custom_bg else "",
        }
        st.markdown(
            '<div style="display:flex;justify-content:center;padding:16px;'
            'background:radial-gradient(ellipse at center,rgba(255,215,0,.08) 0%,transparent 70%);'
            'border-radius:12px;border:1px dashed #333">{}</div>'.format(
                render_limited_card_html(preview_ltd, size="large")),
            unsafe_allow_html=True)

        tier_color = CARD_TIERS.get(ltd_tier, {}).get("color", "#ffd700")
        st.markdown("""
        <div style="background:#10101e;border:1px solid {tc};border-radius:8px;padding:10px;
          text-align:center;margin-top:10px">
          <div style="font-family:Orbitron,sans-serif;font-size:.7rem;color:{tc};font-weight:700">
            {tier} ⭐ LIMITED
          </div>
          <div style="font-size:.6rem;color:#888;margin-top:2px">OVR {ovr} | {na} {anim_count} animazioni</div>
        </div>
        """.format(
            tc=tier_color, tier=ltd_tier, ovr=ltd_ovr,
            na=len(st.session_state.get("ltd_sel_anims", [])),
            anim_count="— con" if st.session_state.get("ltd_sel_anims") else "— nessuna"
        ), unsafe_allow_html=True)

    # ── Salvataggio ──
    st.markdown("---")
    if st.button("💾 SALVA CARTA LIMITED EDITION", use_container_width=True, type="primary"):
        if not ltd_nome:
            st.error("Inserisci il nome!")
        else:
            new_ltd = {
                "id": "ltd_{}_{}".format(draft_db["next_id"], random.randint(1000, 9999)),
                "nome": ltd_nome, "cognome": ltd_cog,
                "overall": ltd_ovr, "ruolo": ltd_ruolo,
                "attacco": ltd_atk, "difesa": ltd_dif, "battuta": ltd_bat,
                "muro": ltd_mur, "ricezione": ltd_ric, "alzata": ltd_alz,
                "foto_path": ltd_foto_path,
                "custom_color1": ltd_color1,
                "custom_color2": ltd_color2,
                "card_shape": st.session_state.get("ltd_selected_shape", "classic"),
                "limited_animations": list(st.session_state.get("ltd_sel_anims", [])),
                "glow_size": ltd_glow,
                "photo_scale": ltd_photo_scale,
                "photo_top": ltd_photo_top,
                "custom_bg_gradient": ltd_bg_grad if ltd_use_custom_bg else "",
                "tier": ltd_tier,
                "is_limited": True,
                "created_at": datetime.now().isoformat(),
            }
            draft_db["cards"].append(new_ltd)
            draft_db["next_id"] += 1
            save_draft_db(draft_db)
            st.session_state.draft_db = draft_db
            st.session_state.ltd_sel_anims = []
            st.session_state.ltd_selected_shape = "classic"
            st.success("✅ Carta Limited **{} {}** (OVR {} · {}) salvata! Disponibile come premio Draft.".format(
                ltd_nome, ltd_cog, ltd_ovr, ltd_tier))
            st.rerun()


def _render_limited_card_manager(draft_db: dict):
    all_ltd = draft_db.get("cards", [])
    if not all_ltd:
        st.info("Nessuna carta Limited Edition creata.")
        return

    st.caption("Totale: {} carte Limited Edition".format(len(all_ltd)))

    for i, card in enumerate(all_ltd):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(render_limited_card_html(card, size="small", show_effects=False), unsafe_allow_html=True)
        with col2:
            anims = card.get("limited_animations", [])
            shape = card.get("card_shape", "classic")
            c1 = card.get("custom_color1", "#ffd700")
            c2 = card.get("custom_color2", "#ff6600")
            st.markdown("""
            <div style="padding:8px 0">
              <div style="font-family:Orbitron,sans-serif;font-weight:700;color:{c1}">{nome} {cog}
                <span style="font-size:.55rem;color:#ffd700;border:1px solid #ffd700;border-radius:3px;padding:1px 5px;margin-left:4px">LIMITED</span>
              </div>
              <div style="font-size:.7rem;color:#888">OVR {ovr} · {tier}</div>
              <div style="font-size:.6rem;color:#666;margin-top:4px">
                🃏 Forma: {shape} | 🎨 {c1}/{c2} | ✨ {na} animazioni
              </div>
            </div>
            """.format(
                c1=c1, nome=card.get("nome", ""), cog=card.get("cognome", ""),
                ovr=card.get("overall", "?"),
                tier=get_tier_by_ovr(card.get("overall", 40)),
                shape=CARD_SHAPES.get(shape, {}).get("name", shape),
                c2=c2, na=len(anims)
            ), unsafe_allow_html=True)
        with col3:
            cid = card.get("id", "x")
            if st.button("🗑️", key="del_ltd_{}_{}".format(i, cid[:8]), help="Elimina"):
                draft_db["cards"] = [c for c in all_ltd if c.get("id") != cid]
                save_draft_db(draft_db)
                st.session_state.draft_db = draft_db
                st.rerun()
        st.markdown("<hr style='border-color:#1e1e3a;margin:4px 0'>", unsafe_allow_html=True)
