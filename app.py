"""
app.py — MBT-BVL 2.0 (Master Ball Academy Beach Volleyball League)
Sistema ruoli: Admin (accesso completo) | Atleta Registrato | Ospite (sola lettura)
"""
import streamlit as st
import hashlib
import sys
from data_manager import load_state, save_state, get_trofei_atleta, calcola_overall_fifa, get_atleta_by_id, TROFEI_DEFINIZIONE
from theme_manager import (
    load_theme_config, save_theme_config, inject_theme_css,
    render_personalization_page, render_banner, render_sponsors_sidebar
)
from ranking_page import build_ranking_data, _render_schede_atleti, CARD_ANIMATIONS, _render_global_trophy_board

st.set_page_config(
    page_title="🏐 MBT-BVL 2.0",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA RUOLI — modifica solo queste due righe
# ═══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = "admin2025"   # ← cambia con la tua password admin
USER_PASSWORD  = ""            # ← lascia vuoto per accesso ospiti libero
#                                 oppure metti es. "ospite2025" per proteggere
# ═══════════════════════════════════════════════════════════════════════════════

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _is_admin() -> bool:
    return st.session_state.get("user_role") == "admin"

def _is_atleta() -> bool:
    """True se loggato come atleta registrato."""
    return st.session_state.get("user_role") == "atleta"

def _render_login():
    """Schermata di login con 3 tab: Admin, Atleta registrato, Ospite."""
    if "user_role" in st.session_state:
        return  # già loggato

    # Mostra form registrazione se richiesto
    if st.session_state.get("show_registrazione"):
        _state_tmp = load_state()
        from auth_manager import render_registrazione
        render_registrazione(_state_tmp)
        if "state" in st.session_state:
            save_state(st.session_state.state)
        return

    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 520px !important; padding-top: 48px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:8px 0 28px">
        <div style="font-size:3.5rem;line-height:1;margin-bottom:10px">🏐</div>
        <div style="font-family:'Barlow Condensed','Oswald',sans-serif;font-size:2.2rem;
            font-weight:900;text-transform:uppercase;letter-spacing:5px;color:#fff">MBT-BVL 2.0</div>
        <div style="color:#e8002d;font-size:0.68rem;letter-spacing:4px;text-transform:uppercase;
            font-weight:700;margin-top:4px">Master Ball Academy · Beach Volleyball League</div>
    </div>
    """, unsafe_allow_html=True)

    tab_admin, tab_atleta, tab_ospite = st.tabs(["🔑 Admin", "🏐 Atleta", "👁️ Ospite"])

    with tab_admin:
        st.caption("Accesso completo: gestione torneo, incassi, tema, impostazioni.")
        pw = st.text_input("Password Admin", type="password", key="pw_admin")
        if st.button("🔓 Entra come Admin", use_container_width=True,
                      key="btn_login_admin", type="primary"):
            if _hash(pw) == _hash(ADMIN_PASSWORD):
                st.session_state.user_role = "admin"
                st.session_state.logged_user = None
                st.rerun()
            else:
                st.error("❌ Password errata.")

    with tab_atleta:
        st.caption("Accedi con il tuo profilo atleta registrato.")
        at_email = st.text_input("Email", key="at_email", placeholder="tuaemail@esempio.com")
        at_pw    = st.text_input("Password", type="password", key="at_pw")
        if st.button("🏐 Accedi come Atleta", use_container_width=True,
                      key="btn_login_atleta", type="primary"):
            from auth_manager import login_atleta
            user = login_atleta(at_email, at_pw)
            if user:
                st.session_state.user_role = "atleta"
                st.session_state.logged_user = user
                st.rerun()
            else:
                st.error("❌ Email o password errata.")
        st.divider()
        st.caption("Non hai ancora un profilo?")
        if st.button("📝 Registrati come Atleta", use_container_width=True,
                      key="btn_goto_reg"):
            st.session_state.show_registrazione = True
            st.rerun()

    with tab_ospite:
        st.caption("Visualizza classifica, tabellone, profili atleti, tornei e segnapunti live.")
        if USER_PASSWORD:
            pw_u = st.text_input("Password Ospite", type="password", key="pw_user")
            accesso_ok = _hash(pw_u) == _hash(USER_PASSWORD)
            btn_label = "👁️ Entra come Ospite"
        else:
            accesso_ok = True
            btn_label = "👁️ Entra come Ospite (accesso libero)"

        if st.button(btn_label, use_container_width=True, key="btn_login_ospite"):
            if accesso_ok:
                st.session_state.user_role = "user"
                st.session_state.logged_user = None
                st.rerun()
            else:
                st.error("❌ Password errata.")

    st.markdown("""
    <div style="text-align:center;margin-top:28px;font-size:0.6rem;color:#444;letter-spacing:2px">
        MBT-BVL 2.0 · MASTER BALL ACADEMY
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ── Esegui il login gate prima di tutto il resto ─────────────────────────────
_render_login()

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "state" not in st.session_state:
    st.session_state.state = load_state()
if "theme_cfg" not in st.session_state:
    st.session_state.theme_cfg = load_theme_config()
if "current_page" not in st.session_state:
    st.session_state.current_page = "torneo"
if "segnapunti_open" not in st.session_state:
    st.session_state.segnapunti_open = False
if "profilo_atleta_id" not in st.session_state:
    st.session_state.profilo_atleta_id = None
if "show_atleta_popup" not in st.session_state:
    st.session_state.show_atleta_popup = None
if "show_bracket_overlay" not in st.session_state:
    st.session_state.show_bracket_overlay = False
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "show_registrazione" not in st.session_state:
    st.session_state.show_registrazione = False
if "torneo_dettaglio_id" not in st.session_state:
    st.session_state.torneo_dettaglio_id = None
if "admin_edit_torneo_id" not in st.session_state:
    st.session_state.admin_edit_torneo_id = None

state = st.session_state.state

state.setdefault("bracket_extra", [])
state["torneo"].setdefault("modalita", state["torneo"].get("tipo_tabellone", "Gironi + Playoff"))
state["torneo"].setdefault("num_gironi", 2)
state["torneo"].setdefault("squadre_per_girone_passano", 2)
state["torneo"].setdefault("sistema_qualificazione", "Prime classificate")
theme_cfg = st.session_state.theme_cfg
logo_html = inject_theme_css(theme_cfg)

is_admin  = _is_admin()
is_atleta = _is_atleta()
logged_user = st.session_state.get("logged_user")

# ── Floating button per riaprire la sidebar quando è chiusa ──────────────────
import streamlit.components.v1 as _components
_components.html("""
<script>
(function(){
    var doc = window.parent.document;

    function getSidebarBtn(){
        return doc.querySelector('[data-testid="stSidebarCollapseButton"] button')
            || doc.querySelector('[data-testid="collapsedControl"] button')
            || doc.querySelector('button[aria-label="open sidebar"]')
            || doc.querySelector('button[aria-label="Close sidebar"]');
    }

    function isSidebarCollapsed(){
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (!sb) return false;
        // Streamlit sets aria-expanded="false" when collapsed
        return sb.getAttribute('aria-expanded') === 'false';
    }

    // Create floating button in the PARENT document
    var existing = doc.getElementById('mbt-sidebar-fab');
    if (!existing) {
        var fab = doc.createElement('button');
        fab.id = 'mbt-sidebar-fab';
        fab.innerHTML = '&#x00BB;&#x00BB;';  // »»
        fab.title = 'Apri menu laterale';
        fab.style.cssText = [
            'position:fixed',
            'top:14px',
            'left:14px',
            'z-index:999999',
            'width:42px',
            'height:42px',
            'border-radius:50%',
            'background:#e8002d',
            'border:2px solid rgba(255,255,255,0.2)',
            'box-shadow:0 4px 18px rgba(232,0,45,0.5),0 2px 6px rgba(0,0,0,0.5)',
            'cursor:pointer',
            'display:none',
            'align-items:center',
            'justify-content:center',
            'font-size:1rem',
            'font-weight:900',
            'color:#fff',
            'transition:transform 0.15s,box-shadow 0.15s',
            'line-height:1'
        ].join(';');
        fab.onmouseenter = function(){ fab.style.transform='scale(1.15)'; };
        fab.onmouseleave = function(){ fab.style.transform='scale(1)'; };
        fab.onclick = function(){
            var btn = getSidebarBtn();
            if (btn) { btn.click(); }
        };
        doc.body.appendChild(fab);
    }

    function syncFab(){
        var fab = doc.getElementById('mbt-sidebar-fab');
        if (!fab) return;
        if (isSidebarCollapsed()) {
            fab.style.display = 'flex';
        } else {
            fab.style.display = 'none';
        }
    }

    // Observe sidebar attribute changes for instant response
    var sb = doc.querySelector('[data-testid="stSidebar"]');
    if (sb) {
        var observer = new MutationObserver(syncFab);
        observer.observe(sb, { attributes: true, attributeFilter: ['aria-expanded', 'style'] });
    }
    // Also poll as fallback
    setInterval(syncFab, 400);
    syncFab();
})();
</script>
""", height=0)


# ─── HELPERS UI ───────────────────────────────────────────────────────────────

def render_header():
    nome = state["torneo"]["nome"] or "Beach Volley"
    header_style = theme_cfg.get("header_style", "Grande con gradiente")
    if header_style == "Solo testo":
        st.markdown(f"<h1 style='font-family:var(--font-display);font-size:2rem;font-weight:800;text-transform:uppercase;color:var(--accent1)'>{nome}</h1>", unsafe_allow_html=True)
    else:
        compact = header_style == "Compatto minimalista"
        padding = "12px 20px" if compact else "20px 30px"
        title_size = "1.8rem" if compact else "2.8rem"
        st.markdown(f"""
        <div class="tournament-header" style="padding:{padding}">
            {logo_html}
            <div class="tournament-title" style="font-size:{title_size}">🏐 {nome}</div>
            <div class="tournament-subtitle">MBT-BVL 2.0 · Master Ball Academy</div>
        </div>
        """, unsafe_allow_html=True)
    render_banner(theme_cfg)
    fasi_ord = ["setup","gironi","eliminazione","proclamazione"]
    fase_corrente = state["fase"]
    idx_corrente = fasi_ord.index(fase_corrente)
    fasi_label = [("setup","⚙️ Setup"),("gironi","🔵 Gironi"),("eliminazione","⚡ Eliminazione"),("proclamazione","🏆 Finale")]
    html = '<div style="display:flex;justify-content:center;flex-wrap:wrap;gap:8px;margin-bottom:20px;">'
    for i, (k, label) in enumerate(fasi_label):
        if i < idx_corrente: css="fase-badge done"; icon="✓ "
        elif i == idx_corrente: css="fase-badge active"; icon=""
        else: css="fase-badge"; icon=""
        html += f'<span class="{css}">{icon}{label}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_bottom_nav():
    if not theme_cfg.get("show_bottom_nav", True):
        return
    current = st.session_state.current_page
    is_segna = st.session_state.segnapunti_open

    if is_admin:
        nav_items = [
            ("torneo","🏐","Torneo"), ("ranking","🏅","Ranking"), ("profili","👤","Profili"),
            ("incassi","💰","Incassi"), ("live","🔴" if is_segna else "📊","Live"),
            ("rivals","⚡","Rivals"), ("theme","🎨","Tema"),
        ]
    elif is_atleta:
        nav_items = [
            ("torneo","🏐","Torneo"), ("ranking","🏅","Ranking"),
            ("profilo_personale","👤","Mio Profilo"),
            ("tornei_programmati","📅","Tornei"),
            ("live","🔴" if is_segna else "📊","Live"),
        ]
    else:
        nav_items = [
            ("torneo","🏐","Torneo"), ("ranking","🏅","Ranking"), ("profili","👤","Profili"),
            ("tornei_programmati","📅","Tornei"),
            ("live","🔴" if is_segna else "📊","Live"), ("trofei","🏆","Trofei"),
        ]

    html = '<div class="bottom-nav">'
    for page_id, icon, label in nav_items:
        if page_id == "live":
            active = "active" if is_segna else ""
        else:
            active = "active" if (current == page_id and not is_segna) else ""
        html += f'<div class="bottom-nav-item {active}"><span class="nav-icon">{icon}</span><span class="nav-label">{label}</span></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    cols = st.columns(len(nav_items))
    for col, (page_id, icon, label) in zip(cols, nav_items):
        with col:
            if st.button(f"{icon} {label}", key=f"bottom_nav_{page_id}", use_container_width=True):
                if page_id == "live":
                    st.session_state.segnapunti_open = not st.session_state.segnapunti_open
                    st.session_state.current_page = "torneo"
                else:
                    st.session_state.current_page = page_id
                    st.session_state.segnapunti_open = False
                    if page_id != "profili":
                        st.session_state.profilo_atleta_id = None
                st.rerun()


def render_atleta_popup(atleta_id, ranking):
    atleta_data = next((a for a in ranking if a["id"] == atleta_id), None)
    if not atleta_data:
        return
    a = atleta_data
    foto = a["atleta"].get("foto_b64")
    foto_html = f'<img src="data:image/png;base64,{foto}" style="width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid var(--accent1);flex-shrink:0">' if foto else '<div style="width:44px;height:44px;border-radius:50%;background:var(--bg-card);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0">👤</div>'
    st.markdown(f"""
    <div style="background:var(--bg-card2);border:2px solid var(--accent1);border-radius:12px;padding:14px;margin:8px 0">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
            {foto_html}
            <div>
                <div style="font-weight:800;font-size:1rem;color:var(--text-primary)">{a['nome']}</div>
                <div style="color:var(--accent-gold);font-size:0.75rem">OVR {a['overall']} · {a['card_type'].replace('_',' ').upper()}</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:8px">
            <div style="background:var(--bg-card);border-radius:6px;padding:6px;text-align:center">
                <div style="font-weight:800;color:var(--accent-gold);font-size:0.9rem">{a['rank_pts']}</div>
                <div style="font-size:0.55rem;color:var(--text-secondary)">RANK PTS</div>
            </div>
            <div style="background:var(--bg-card);border-radius:6px;padding:6px;text-align:center">
                <div style="font-weight:800;color:var(--green);font-size:0.9rem">{a['vittorie']}</div>
                <div style="font-size:0.55rem;color:var(--text-secondary)">VITTORIE</div>
            </div>
            <div style="background:var(--bg-card);border-radius:6px;padding:6px;text-align:center">
                <div style="font-weight:800;color:var(--text-primary);font-size:0.9rem">{a['win_rate']}%</div>
                <div style="font-size:0.55rem;color:var(--text-secondary)">WIN RATE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    trofei = get_trofei_atleta(a["atleta"])
    sbloccati = [t for t, u in trofei if u]
    if sbloccati:
        icons_str = " ".join(t["icona"] for t in sbloccati[:6])
        st.markdown(f'<div style="font-size:1rem;margin:4px 0 8px">{icons_str}</div>', unsafe_allow_html=True)
    col_close, col_goto = st.columns(2)
    with col_close:
        if st.button("✕ Chiudi", key=f"close_popup_{atleta_id}", use_container_width=True):
            st.session_state.show_atleta_popup = None
            st.rerun()
    with col_goto:
        if st.button("👤 Profilo →", key=f"popup_goto_{atleta_id}", use_container_width=True):
            st.session_state.profilo_atleta_id = atleta_id
            st.session_state.current_page = "profili"
            st.session_state.show_atleta_popup = None
            st.rerun()


def render_trofei_showcase(state):
    st.markdown("## 🏆 Bacheca Trofei")
    st.markdown("""
    <style>
    .trophy-showcase-card { transition:all 0.3s ease; cursor:help; }
    .trophy-showcase-card:hover { transform:scale(1.08) translateY(-6px) !important; }
    </style>
    """, unsafe_allow_html=True)
    if is_admin:
        with st.expander("🎨 Personalizza Bacheca Trofei", expanded=False):
            col_img, col_info = st.columns([2, 2])
            with col_img:
                banner_trophy = st.file_uploader("📷 Banner superiore", type=["png","jpg","jpeg"], key="trophy_banner_up")
                if banner_trophy:
                    import base64
                    st.session_state.trophy_banner_b64 = base64.b64encode(banner_trophy.read()).decode()
                    st.rerun()
                if st.session_state.get("trophy_banner_b64") and st.button("🗑️ Rimuovi banner", key="rm_trophy_banner"):
                    st.session_state.trophy_banner_b64 = None
                    st.rerun()
            with col_info:
                st.info("Passa il cursore su un trofeo per vedere come ottenerlo. I trofei si animano all'hover!")
    if st.session_state.get("trophy_banner_b64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.trophy_banner_b64}" style="width:100%;border-radius:12px;margin-bottom:20px;max-height:200px;object-fit:cover">', unsafe_allow_html=True)
    st.markdown("### 🌟 Tutti i Trofei")
    st.caption("Passa il cursore su un trofeo per vedere come ottenerlo")
    cols_per_row = 4
    for row_start in range(0, len(TROFEI_DEFINIZIONE), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, trofeo in enumerate(TROFEI_DEFINIZIONE[row_start:row_start+cols_per_row]):
            with cols[j]:
                rarità_colors = {
                    "comune": "#cd7f32", "non comune": "#c0c0c0",
                    "raro": "#ffd700", "epico": "#e040fb", "leggendario": "#00f5ff"
                }
                tc = rarità_colors.get(trofeo["rarità"], "#888")
                st.markdown(f"""
                <div class="trophy-showcase-card" title="🎯 Come ottenerlo: {trofeo['descrizione']}"
                    style="background:{trofeo['sfondo']};border:2px solid {tc};
                    border-radius:16px;padding:20px;text-align:center;margin-bottom:12px;
                    box-shadow:0 4px 20px {tc}40">
                    <div style="font-size:3rem;margin-bottom:8px">{trofeo['icona']}</div>
                    <div style="font-weight:900;font-size:0.95rem;color:rgba(0,0,0,0.9);
                        text-transform:uppercase;letter-spacing:1px">{trofeo['nome']}</div>
                    <div style="font-size:0.68rem;margin-top:6px;color:rgba(0,0,0,0.75);
                        background:rgba(255,255,255,0.25);border-radius:6px;padding:4px 8px;
                        line-height:1.3">{trofeo['descrizione']}</div>
                    <div style="margin-top:8px;font-size:0.55rem;font-weight:700;letter-spacing:2px;
                        text-transform:uppercase;color:rgba(0,0,0,0.55)">{trofeo['rarità'].upper()}</div>
                </div>
                """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### 👥 Stato Trofei per Atleta")
    ranking = build_ranking_data(state)
    if ranking:
        _render_global_trophy_board(state, ranking)
    else:
        st.info("Completa un torneo per vedere i trofei degli atleti.")


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

with st.sidebar:

    # ── Badge ruolo + pulsante logout ────────────────────────────────────────
    if is_admin:
        role_label = "🔑 Admin"
        role_color = "#e8002d"
        role_desc  = "Accesso completo"
    elif is_atleta and logged_user:
        role_label = f"🏐 {logged_user['nome']} {logged_user['cognome']}"
        role_color = "#ffd700"
        role_desc  = "Atleta Registrato"
    else:
        role_label = "👁️ Ospite"
        role_color = "#0070f3"
        role_desc  = "Sola lettura"

    col_rb, col_lo = st.columns([3, 1])
    with col_rb:
        st.markdown(f"""
        <div style="background:{role_color}18;border:1px solid {role_color};border-radius:8px;
            padding:6px 12px;font-size:0.7rem;font-weight:700;color:{role_color};
            letter-spacing:1px;text-transform:uppercase">
            {role_label} <span style="font-weight:400;opacity:0.7;font-size:0.6rem">· {role_desc}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_lo:
        if st.button("⏏️", key="btn_logout", help="Esci / Cambia ruolo", use_container_width=True):
            del st.session_state["user_role"]
            st.rerun()

    st.markdown(f"""
    <div style="text-align:center;padding:12px 0 10px">
        {logo_html}
        <div style="font-family:var(--font-display);font-size:1.3rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:var(--text-primary)">MBT-BVL 2.0</div>
        <div style="color:var(--accent1);font-size:0.6rem;letter-spacing:4px;text-transform:uppercase;font-weight:700;margin-top:2px">Master Ball Academy</div>
    </div>
    """, unsafe_allow_html=True)

    if theme_cfg.get("banner_position") == "Nella sidebar" and theme_cfg.get("banner_b64"):
        st.markdown(f'<img src="data:image/png;base64,{theme_cfg["banner_b64"]}" style="width:100%;border-radius:8px;margin-bottom:8px">', unsafe_allow_html=True)

    st.markdown("<hr style='border-color:var(--border);margin:0 0 12px'>", unsafe_allow_html=True)

    # ── NAVIGAZIONE TORNEO ───────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">⚡ NAVIGAZIONE TORNEO</div>', unsafe_allow_html=True)

    fase_corrente = state["fase"]
    fasi_ord = ["setup","gironi","eliminazione","proclamazione"]
    idx_attuale = fasi_ord.index(fase_corrente)
    nav_items_torneo = [
        ("setup","⚙️  Setup & Iscrizioni"), ("gironi","🔵  Fase a Gironi"),
        ("eliminazione","⚡  Eliminazione Diretta"), ("proclamazione","🏆  Proclamazione"),
    ]
    for i, (k, label) in enumerate(nav_items_torneo):
        disabled = i > idx_attuale
        if disabled:
            st.markdown(f'<div style="padding:9px 14px;margin-bottom:4px;border-radius:var(--radius);border:1px solid var(--border);opacity:0.3;cursor:not-allowed;font-size:0.82rem;color:var(--text-secondary)">🔒 {label}</div>', unsafe_allow_html=True)
        else:
            is_active = (k == fase_corrente and st.session_state.current_page == "torneo" and not st.session_state.segnapunti_open)
            if is_active:
                st.markdown(f'<div style="padding:9px 14px;margin-bottom:4px;border-radius:var(--radius);background:var(--accent1);font-weight:700;font-size:0.82rem;color:white">▶ {label}</div>', unsafe_allow_html=True)
            elif is_admin:
                if st.button(label, key=f"nav_{k}", use_container_width=True):
                    state["fase"] = k; st.session_state.current_page = "torneo"
                    st.session_state.segnapunti_open = False; save_state(state); st.rerun()
            else:
                st.markdown(f'<div style="padding:9px 14px;margin-bottom:4px;border-radius:var(--radius);border:1px solid var(--border);font-size:0.82rem;color:var(--text-secondary);opacity:0.65">👁️ {label}</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color:var(--border);margin:14px 0 12px'>", unsafe_allow_html=True)

    # ── STRUMENTI (visibili a tutti) ─────────────────────────────────────────
    st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">🛠️ STRUMENTI</div>', unsafe_allow_html=True)

    segna_label = "🔴 Chiudi Segnapunti" if st.session_state.segnapunti_open else "📊 SEGNAPUNTI LIVE"
    if st.button(segna_label, use_container_width=True, key="btn_segnapunti"):
        st.session_state.segnapunti_open = not st.session_state.segnapunti_open
        st.session_state.current_page = "torneo"; st.rerun()

    bracket_label = "❌ Chiudi Tabellone" if st.session_state.get("show_bracket_overlay") else "📋 TABELLONE TORNEO"
    if st.button(bracket_label, use_container_width=True, key="btn_tabellone"):
        st.session_state.show_bracket_overlay = not st.session_state.get("show_bracket_overlay", False)
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏅 Ranking", use_container_width=True, key="btn_ranking"):
            st.session_state.current_page = "ranking"; st.session_state.segnapunti_open = False; st.rerun()
    with c2:
        if st.button("👤 Profili", use_container_width=True, key="btn_profili"):
            st.session_state.current_page = "profili"; st.session_state.segnapunti_open = False; st.rerun()

    c3, c4 = st.columns(2)
    with c3:
        if st.button("🏆 Trofei", use_container_width=True, key="btn_trofei"):
            st.session_state.current_page = "trofei"; st.session_state.segnapunti_open = False; st.rerun()
    with c4:
        if st.button("⚡ Rivals", use_container_width=True, key="btn_rivals_pub"):
            st.session_state.current_page = "rivals"; st.session_state.segnapunti_open = False; st.rerun()

    # Tornei in programma — visibile a tutti
    if st.button("📅 Tornei in Programma", use_container_width=True, key="btn_tornei_prog"):
        st.session_state.current_page = "tornei_programmati"; st.session_state.segnapunti_open = False; st.rerun()

    # Profilo personale — solo atleti registrati
    if is_atleta:
        if st.button("👤 Il Mio Profilo", use_container_width=True, key="btn_mio_profilo",
                      type="primary"):
            st.session_state.current_page = "profilo_personale"; st.session_state.segnapunti_open = False; st.rerun()

    # ── SEZIONI SOLO ADMIN ───────────────────────────────────────────────────
    if is_admin:
        st.markdown("<hr style='border-color:var(--border);margin:10px 0 8px'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:#e8002d;font-weight:700;margin-bottom:6px">🔑 SOLO ADMIN</div>', unsafe_allow_html=True)

        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("💰 Incassi", use_container_width=True, key="btn_incassi"):
                st.session_state.current_page = "incassi"; st.session_state.segnapunti_open = False; st.rerun()
        with ca2:
            if st.button("🎨 Tema", use_container_width=True, key="btn_theme"):
                st.session_state.current_page = "theme"; st.session_state.segnapunti_open = False; st.rerun()

        if st.button("📅 Gestisci Tornei in Programma", use_container_width=True, key="btn_admin_tornei_prog"):
            st.session_state.current_page = "admin_tornei_programmati"; st.session_state.segnapunti_open = False; st.rerun()

        if st.button("🔧 Ricalcola Statistiche", use_container_width=True, key="btn_ricalcola"):
            st.session_state.current_page = "ricalcola_stats"; st.session_state.segnapunti_open = False; st.rerun()

        if st.button("⚡ MBT RIVALS — Card Game", use_container_width=True, key="btn_rivals"):
            st.session_state.current_page = "rivals"; st.session_state.segnapunti_open = False; st.rerun()

    st.markdown("<hr style='border-color:var(--border);margin:14px 0 12px'>", unsafe_allow_html=True)

    # ── INFO TORNEO ATTIVO ───────────────────────────────────────────────────
    if state["torneo"]["nome"]:
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">📋 TORNEO ATTIVO</div>', unsafe_allow_html=True)
        tipo_gioco = state["torneo"].get("tipo_gioco","2x2")
        st.markdown(f"""
        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:var(--radius);padding:12px;margin-bottom:12px">
            <div style="font-family:var(--font-display);font-size:1.05rem;font-weight:700;color:var(--text-primary);margin-bottom:8px">{state['torneo']['nome']}</div>
            <div style="display:flex;flex-direction:column;gap:4px">
                <div style="font-size:0.78rem;color:var(--text-secondary)">📅 {state['torneo']['data']}</div>
                <div style="font-size:0.78rem;color:var(--text-secondary)">🏐 {tipo_gioco} · {state['torneo']['formato_set']} · Max {state['torneo']['punteggio_max']} pt</div>
                <div style="font-size:0.78rem;color:var(--text-secondary)">📊 {state['torneo']['tipo_tabellone']}</div>
                <div style="font-size:0.78rem;color:var(--text-secondary)">👥 {len(state['squadre'])} squadre · {len(state['atleti'])} atleti</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── TOP RANKING ──────────────────────────────────────────────────────────
    ranking_data = build_ranking_data(state)
    if ranking_data:
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">🏅 TOP RANKING</div>', unsafe_allow_html=True)
        popup_id = st.session_state.get("show_atleta_popup")
        if popup_id:
            render_atleta_popup(popup_id, ranking_data)
        medals = {0:"🥇",1:"🥈",2:"🥉"}
        st.caption("Clicca un nome per info rapide:")
        for i, a in enumerate(ranking_data[:5]):
            icon = medals.get(i, f"#{i+1}")
            card_icons_small = {
                "bronzo_comune":"🟫","bronzo_raro":"🟤","argento_comune":"⬜","argento_raro":"🔵",
                "oro_comune":"🟨","oro_raro":"🌟","eroe":"💜","leggenda":"🤍","dio_olimpo":"⚡"
            }
            ci = card_icons_small.get(a.get("card_type","bronzo_comune"),"")
            is_open = popup_id == a["id"]
            btn_style = "primary" if is_open else "secondary"
            if st.button(f"{icon} {ci} {a['nome']}  ·  {a['rank_pts']}pt", key=f"sidebar_rank_{a['id']}", use_container_width=True, type=btn_style):
                st.session_state.show_atleta_popup = None if is_open else a["id"]
                st.rerun()
        if st.button("→ Classifica Completa", key="btn_rank_full", use_container_width=True):
            st.session_state.current_page = "ranking"; st.rerun()

    # ── TROFEI PROSSIMI ──────────────────────────────────────────────────────
    atleti_con_dati = [a for a in state["atleti"] if a["stats"]["tornei"] > 0]
    if atleti_con_dati:
        st.markdown("<hr style='border-color:var(--border);margin:12px 0'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">🏆 TROFEI DA SBLOCCARE</div>', unsafe_allow_html=True)
        thtml = '<div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:var(--radius);padding:10px;margin-bottom:8px">'
        shown = 0
        for atleta in atleti_con_dati[:3]:
            trofei = get_trofei_atleta(atleta)
            prossimo = next((t for t, u in trofei if not u), None)
            if prossimo and shown < 3:
                thtml += f'<div style="display:flex;gap:8px;align-items:center;padding:5px 0;border-bottom:1px solid var(--border);font-size:0.73rem"><span style="font-size:1rem;opacity:0.35">{prossimo["icona"]}</span><div><div style="font-weight:600">{atleta["nome"]}</div><div style="font-size:0.58rem;color:var(--text-secondary)">{prossimo["descrizione"]}</div></div></div>'
                shown += 1
        thtml += '</div>'
        if shown > 0:
            st.markdown(thtml, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:var(--border);margin:14px 0 12px'>", unsafe_allow_html=True)
    render_sponsors_sidebar(theme_cfg)

    # ── DATI E RESET (solo admin) ────────────────────────────────────────────
    if is_admin:
        st.markdown("<hr style='border-color:var(--border);margin:14px 0 12px'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent1);font-weight:700;margin-bottom:8px">💾 DATI</div>', unsafe_allow_html=True)
        cs1, cs2 = st.columns(2)
        with cs1:
            if st.button("💾 Salva", use_container_width=True, key="btn_save"):
                save_state(state); st.toast("✅ Salvato!", icon="💾")
        with cs2:
            if st.button("⚠️ Reset", use_container_width=True, key="btn_reset_toggle"):
                st.session_state.show_reset = not st.session_state.get("show_reset", False); st.rerun()
        if st.session_state.get("show_reset", False):
            st.warning("⚠️ Cancellerà il torneo corrente. Atleti e ranking mantenuti.")
            if st.button("🔴 CONFERMA RESET", use_container_width=True, key="btn_reset_confirm"):
                from data_manager import empty_state
                atleti_bkp = state["atleti"]
                nuovo = empty_state(); nuovo["atleti"] = atleti_bkp
                st.session_state.state = nuovo; save_state(nuovo)
                st.session_state.show_reset = False; st.session_state.current_page = "torneo"; st.rerun()
        st.markdown('<div style="font-size:0.65rem;color:var(--text-secondary);text-align:center;margin-top:4px">📁 beach_volley_data.json</div>', unsafe_allow_html=True)


# ─── BRACKET OVERLAY ─────────────────────────────────────────────────────────

def render_bracket_overlay(state):
    st.markdown("""
    <div style="background:linear-gradient(90deg,rgba(232,0,45,0.12),transparent,rgba(232,0,45,0.12));
        border:2px solid var(--accent1);border-radius:12px;padding:12px 24px;margin-bottom:20px;text-align:center">
        <span style="font-family:var(--font-display);font-size:0.8rem;letter-spacing:4px;text-transform:uppercase;color:var(--accent1);font-weight:800">
            📋 TABELLONE TORNEO — {nome}
        </span>
    </div>
    """.replace("{nome}", state["torneo"]["nome"] or "Torneo"), unsafe_allow_html=True)

    gironi = state.get("gironi", [])
    bracket = state.get("bracket", [])

    if not gironi and not bracket:
        st.info("Il torneo non è ancora iniziato.")
        return

    if gironi:
        st.markdown("### 🔵 Fase a Gironi")
        cols_g = st.columns(len(gironi))
        for i, girone in enumerate(gironi):
            with cols_g[i]:
                st.markdown(f"**{girone['nome']}**")
                from data_manager import get_squadra_by_id as gsq
                squadre_ord = sorted(
                    [gsq(state, sid) for sid in girone["squadre"] if gsq(state, sid)],
                    key=lambda s: (-s["punti_classifica"], -s["vittorie"])
                )
                html = '<table style="width:100%;border-collapse:collapse;font-size:0.8rem">'
                html += '<tr><th style="text-align:left;padding:4px;color:#888">#</th><th style="text-align:left;padding:4px;color:#888">Squadra</th><th style="padding:4px;color:#888">Pts</th></tr>'
                for j, sq in enumerate(squadre_ord):
                    q_mark = "🟢 " if j < 2 else ""
                    ghost_style = "opacity:0.5;" if sq.get("is_ghost") else ""
                    html += f'<tr style="{ghost_style}"><td style="padding:3px 4px;color:#888">{j+1}</td><td style="padding:3px 4px;font-weight:600;text-align:left">{q_mark}{sq["nome"]}</td><td style="padding:3px 4px;text-align:center;color:#ffd700;font-weight:700">{sq["punti_classifica"]}</td></tr>'
                html += '</table>'
                st.markdown(html, unsafe_allow_html=True)
                for p in girone["partite"]:
                    sq1 = gsq(state, p["sq1"]); sq2 = gsq(state, p["sq2"])
                    if sq1 and sq2:
                        confirmed = "✅" if p["confermata"] else "🔴"
                        score = f"{p['set_sq1']}-{p['set_sq2']}" if p["confermata"] else "vs"
                        st.markdown(f"""<div style="background:var(--bg-card2);border-radius:6px;padding:6px 10px;margin:4px 0;font-size:0.78rem;display:flex;justify-content:space-between;align-items:center">
                        <span style="color:var(--accent1);font-weight:600">{sq1['nome']}</span>
                        <span style="color:#fff;font-weight:800;background:var(--bg-card);padding:2px 8px;border-radius:4px">{confirmed} {score}</span>
                        <span style="color:var(--accent2);font-weight:600">{sq2['nome']}</span>
                        </div>""", unsafe_allow_html=True)

    if bracket:
        st.markdown("---")
        st.markdown("### ⚡ Eliminazione Diretta")
        n = len(bracket)
        if n == 1: round_labels = ["🏆 FINALE"]; rounds = [bracket]
        elif n == 2: round_labels = ["🥇 SEMIFINALI"]; rounds = [bracket]
        elif n <= 4: round_labels = ["⚡ QUARTI", "🏆 SEMIFINALI/FINALE"]; half = n//2; rounds = [bracket[:half], bracket[half:]]
        else: round_labels = ["⚡ Eliminazione"]; rounds = [bracket]

        from data_manager import get_squadra_by_id as gsq2
        for r_label, r_partite in zip(round_labels, rounds):
            st.markdown(f"**{r_label}**")
            cols_br = st.columns(max(len(r_partite), 1))
            for ci, p in enumerate(r_partite):
                sq1 = gsq2(state, p["sq1"]); sq2 = gsq2(state, p["sq2"])
                if sq1 and sq2:
                    with cols_br[ci]:
                        confirmed = "✅" if p["confermata"] else "🔴"
                        score = f"{p['set_sq1']} — {p['set_sq2']}" if p["confermata"] else "vs"
                        vincitore_id = p.get("vincitore")
                        v_name = gsq2(state, vincitore_id)["nome"] if vincitore_id and gsq2(state, vincitore_id) else ""
                        st.markdown(f"""
                        <div style="background:var(--bg-card);border:2px solid {'var(--green)' if p['confermata'] else 'var(--border)'};
                            border-radius:10px;padding:14px;text-align:center;margin-bottom:8px">
                            <div style="font-size:0.65rem;color:#888;margin-bottom:8px;letter-spacing:2px">{confirmed} {r_label}</div>
                            <div style="font-weight:700;font-size:1rem;color:var(--accent1)">{sq1['nome']}</div>
                            <div style="font-size:2rem;font-weight:900;color:white;margin:6px 0">{score}</div>
                            <div style="font-weight:700;font-size:1rem;color:var(--accent2)">{sq2['nome']}</div>
                            {f'<div style="margin-top:8px;font-size:0.75rem;color:var(--green);font-weight:700">🏆 {v_name}</div>' if v_name else ''}
                        </div>
                        """, unsafe_allow_html=True)

    podio = state.get("podio", [])
    if podio:
        st.markdown("---")
        st.markdown("### 🏆 Podio Finale")
        from data_manager import get_squadra_by_id as gsq3
        medals_map = {1:"🥇", 2:"🥈", 3:"🥉"}
        podio_sorted = sorted(podio, key=lambda x: x[0])
        cols_p = st.columns(len(podio_sorted))
        for ci, (pos, sq_id) in enumerate(podio_sorted):
            sq = gsq3(state, sq_id)
            if sq:
                with cols_p[ci]:
                    st.markdown(f"""
                    <div style="background:var(--bg-card);border:2px solid var(--accent-gold);border-radius:10px;padding:16px;text-align:center">
                        <div style="font-size:2.5rem">{medals_map.get(pos,'')}</div>
                        <div style="font-weight:800;font-size:1rem;color:var(--accent-gold)">{sq['nome']}</div>
                        <div style="color:#888;font-size:0.75rem">{pos}° posto</div>
                    </div>
                    """, unsafe_allow_html=True)


# ─── MAIN ROUTING ─────────────────────────────────────────────────────────────

page = st.session_state.current_page

if st.session_state.get("show_bracket_overlay"):
    render_bracket_overlay(state)
    st.markdown("---")

if st.session_state.segnapunti_open:
    from segnapunti_live import render_segnapunti_live
    st.markdown("""
    <div style="background:linear-gradient(90deg,rgba(232,0,45,0.1),transparent,rgba(232,0,45,0.1));
        border:1px solid var(--accent1);border-radius:8px;padding:8px 20px;margin-bottom:16px;text-align:center">
        <span style="font-family:var(--font-display);font-size:0.65rem;letter-spacing:4px;text-transform:uppercase;color:var(--accent1);font-weight:700">
            🔴 LIVE · SEGNAPUNTI ATTIVO
        </span>
    </div>
    """, unsafe_allow_html=True)
    render_segnapunti_live(state, theme_cfg)
    st.divider()
    st.stop()

# ── Pagine visibili a tutti ──────────────────────────────────────────────────

if page == "torneo":
    from fase_gironi import render_gironi
    from fase_eliminazione import render_eliminazione
    from fase_proclamazione import render_proclamazione
    render_header()
    fase = state["fase"]
    if fase == "setup":
        if is_admin:
            from fase_setup import render_setup
            render_setup(state)
        else:
            st.info("⚙️ Il torneo è in fase di configurazione. Torna quando inizia!")
    elif fase == "gironi":
        render_gironi(state)
    elif fase == "eliminazione":
        render_eliminazione(state)
    elif fase == "proclamazione":
        render_proclamazione(state)

elif page == "ranking":
    from ranking_page import render_ranking_page
    render_header()
    render_ranking_page(state)

elif page == "profili":
    from ranking_page import _render_carte_fifa, _render_trofei_page, _render_schede_atleti, CARD_ANIMATIONS, build_ranking_data
    render_header()
    st.markdown("## 👤 Profili Giocatori")
    ranking = build_ranking_data(state)
    if not ranking and not state["atleti"]:
        st.info("Nessun atleta registrato.")
    elif not ranking:
        st.info("Atleti senza tornei disputati — carte a OVR 40 (Bronzo Raro).")
        from data_manager import calcola_overall_fifa, get_card_type
        from ranking_page import render_card_html, CARD_ANIMATIONS
        st.markdown(CARD_ANIMATIONS, unsafe_allow_html=True)
        cards_per_row = 4
        fake_ranking = []
        for a in state["atleti"]:
            s = a["stats"]
            overall = calcola_overall_fifa(a)
            ct = get_card_type(overall)
            fake_ranking.append({
                "atleta": a, "id": a["id"], "nome": a["nome"],
                "tornei": s["tornei"], "vittorie": s["vittorie"], "sconfitte": s["sconfitte"],
                "set_vinti": s["set_vinti"], "set_persi": s["set_persi"],
                "punti_fatti": s["punti_fatti"], "punti_subiti": s["punti_subiti"],
                "quoziente_punti": 0, "quoziente_set": 0, "win_rate": 0,
                "rank_pts": 0, "oro": 0, "argento": 0, "bronzo": 0, "storico": [],
                "overall": overall, "card_type": ct,
            })
        for i in range(0, len(fake_ranking), cards_per_row):
            chunk = fake_ranking[i:i+cards_per_row]
            cols = st.columns(len(chunk))
            for col, a_data in zip(cols, chunk):
                with col:
                    st.markdown(render_card_html(a_data, size="normal", clickable=False), unsafe_allow_html=True)
    else:
        if st.session_state.get("profilo_atleta_id"):
            ptabs = st.tabs(["👤 Carriera", "🃏 Card FIFA", "🏅 Trofei"])
            with ptabs[0]: _render_schede_atleti(state, ranking)
            with ptabs[1]: _render_carte_fifa(state, ranking)
            with ptabs[2]: _render_trofei_page(state, ranking)
        else:
            ptabs = st.tabs(["🃏 Card FIFA", "🏅 Trofei", "👤 Carriera"])
            with ptabs[0]: _render_carte_fifa(state, ranking)
            with ptabs[1]: _render_trofei_page(state, ranking)
            with ptabs[2]: _render_schede_atleti(state, ranking)

elif page == "trofei":
    render_header()
    render_trofei_showcase(state)

elif page == "rivals":
    from mbt_rivals import render_mbt_rivals
    render_header()
    render_mbt_rivals(state)

elif page == "tornei_programmati":
    render_header()
    from tornei_programmati import render_tornei_in_programma
    render_tornei_in_programma(state, user=logged_user)

elif page == "profilo_personale":
    render_header()
    if is_atleta and logged_user:
        from auth_manager import render_profilo_personale
        render_profilo_personale(state)
    else:
        st.warning("🔒 Accedi come Atleta per vedere il tuo profilo personale.")

# ── Pagine solo Admin ────────────────────────────────────────────────────────

elif page == "admin_tornei_programmati":
    if is_admin:
        render_header()
        from tornei_programmati import render_admin_tornei_programmati
        render_admin_tornei_programmati(state)
    else:
        render_header()
        st.error("🔒 Sezione riservata agli amministratori.")

elif page == "incassi":
    if is_admin:
        from incassi import render_incassi
        render_header()
        render_incassi(state)
    else:
        render_header()
        st.error("🔒 Sezione riservata agli amministratori.")

elif page == "theme":
    if is_admin:
        render_personalization_page(theme_cfg)
        st.session_state.theme_cfg = theme_cfg
    else:
        render_header()
        st.error("🔒 Sezione riservata agli amministratori.")

elif page == "ricalcola_stats":
    if is_admin:
        render_header()
        st.markdown("## 🔧 Ricalcolo Statistiche Atleti")
        st.info("Azzera e ricalcola da zero attributi FIFA e statistiche di ogni atleta dallo storico tornei salvato. Usa questo per correggere dati di tornei già conclusi.")
        atleti_con_storico = [a for a in state.get("atleti",[]) if a["stats"].get("storico_posizioni")]
        if not atleti_con_storico:
            st.warning("Nessun atleta ha storico tornei. Completa prima un torneo.")
        else:
            st.markdown(f"**{len(atleti_con_storico)} atleti** con storico torneo trovati.")
            with st.expander("👁 Anteprima storico", expanded=False):
                for a in atleti_con_storico[:8]:
                    storico = a["stats"]["storico_posizioni"]
                    st.markdown(f"**{a['nome']}** — {len(storico)} torneo/i")
                    for e in storico:
                        if isinstance(e, dict):
                            st.caption(f"  → pos {e.get('pos','?')}/{e.get('n_squadre','?')} | set {e.get('set_vinti',0)}V-{e.get('set_persi',0)}P | punti {e.get('punti_fatti',0)}-{e.get('punti_subiti',0)}")
                        else:
                            pos = e[1] if len(e)>1 else "?"
                            nsq = e[2] if len(e)>2 else "?"
                            st.caption(f"  → pos {pos}/{nsq}")
                if len(atleti_con_storico) > 8:
                    st.caption(f"… e altri {len(atleti_con_storico)-8} atleti")
            conf = st.checkbox("Confermo — ricalcola tutto da zero", key="conf_ricalcola_v2")
            if conf:
                if st.button("🔄 RICALCOLA ORA", type="primary", use_container_width=True, key="btn_ricalcola_exec"):
                    from data_manager import ricalcola_stats_da_storico
                    ricalcola_stats_da_storico(state)
                    save_state(state)
                    st.success(f"✅ Statistiche ricalcolate per {len(atleti_con_storico)} atleti!")
                    st.rerun()
    else:
        render_header()
        st.error("🔒 Sezione riservata agli amministratori.")

st.markdown("<br><br>", unsafe_allow_html=True)
render_bottom_nav()
save_state(state)
