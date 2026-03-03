"""
auth_manager.py — MBT-BVL 2.0
Gestione registrazione atleti, profili utente, email automatiche.
"""
import json
import hashlib
import random
import smtplib
import ssl
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

# ─── CONFIG ───────────────────────────────────────────────────────────────────
USERS_FILE = "mbt_users.json"
ADMIN_EMAIL = "masterballacademy@gmail.com"

# Credenziali SMTP — su Streamlit Cloud mettile in st.secrets
# [email]
# address  = "masterballacademy@gmail.com"
# password = "APP_PASSWORD_QUI"
# (usa una App Password di Google, non la password dell'account)

def _get_smtp_creds():
    try:
        return st.secrets["email"]["address"], st.secrets["email"]["password"]
    except Exception:
        return None, None


# ─── PERSISTENZA UTENTI ───────────────────────────────────────────────────────

def _load_users() -> dict:
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ─── EMAIL ────────────────────────────────────────────────────────────────────

def _send_email(to: str, subject: str, html_body: str):
    """Invia email HTML via Gmail SMTP. Silenzia errori se credenziali mancanti."""
    sender, password = _get_smtp_creds()
    if not sender or not password:
        return False  # credenziali non configurate, skip silenzioso

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"MBT-BVL 2.0 <{sender}>"
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())
        return True
    except Exception:
        return False


def _email_benvenuto_atleta(user: dict):
    """Email di benvenuto al nuovo atleta."""
    nome = f"{user['nome']} {user['cognome']}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#f0f0f0;border-radius:12px;overflow:hidden">
      <div style="background:linear-gradient(135deg,#e8002d,#b00020);padding:32px;text-align:center">
        <div style="font-size:3rem">🏐</div>
        <h1 style="color:#fff;margin:8px 0;font-size:1.6rem;letter-spacing:2px">MBT-BVL 2.0</h1>
        <p style="color:rgba(255,255,255,0.8);margin:0;font-size:0.9rem">Beach Volleyball League</p>
      </div>
      <div style="padding:32px">
        <h2 style="color:#e8002d">Benvenuto/a, {nome}! 🎉</h2>
        <p>La tua registrazione è avvenuta con successo. Da oggi fai parte della <strong>MBT-BVL 2.0</strong>!</p>
        <div style="background:#13131a;border:1px solid #333;border-radius:8px;padding:16px;margin:20px 0">
          <p style="margin:4px 0"><strong>Email:</strong> {user['email']}</p>
          <p style="margin:4px 0"><strong>Nome:</strong> {nome}</p>
          <p style="margin:4px 0"><strong>Data registrazione:</strong> {user.get('data_registrazione','')}</p>
        </div>
        <p>Accedi all'app per completare il tuo profilo, visualizzare le tue statistiche e iscriverti ai tornei.</p>
        <p style="color:#888;font-size:0.8rem;margin-top:24px">
          Se non hai effettuato questa registrazione, ignora questa email.<br>
          MBT-BVL 2.0 — Master Ball Academy
        </p>
      </div>
    </div>
    """
    _send_email(user["email"], "✅ Registrazione MBT-BVL 2.0 confermata", html)


def _email_admin_nuovo_atleta(user: dict):
    """Notifica all'admin di un nuovo atleta registrato."""
    nome = f"{user['nome']} {user['cognome']}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#e8002d">🏐 Nuovo Atleta Registrato — MBT-BVL 2.0</h2>
      <table style="border-collapse:collapse;width:100%;background:#f9f9f9;border-radius:8px">
        <tr><td style="padding:10px;font-weight:bold;width:40%">Nome</td><td style="padding:10px">{nome}</td></tr>
        <tr style="background:#fff"><td style="padding:10px;font-weight:bold">Email</td><td style="padding:10px">{user['email']}</td></tr>
        <tr><td style="padding:10px;font-weight:bold">Telefono</td><td style="padding:10px">{user.get('telefono','—')}</td></tr>
        <tr style="background:#fff"><td style="padding:10px;font-weight:bold">Data di nascita</td><td style="padding:10px">{user.get('data_nascita','—')}</td></tr>
        <tr><td style="padding:10px;font-weight:bold">Luogo di residenza</td><td style="padding:10px">{user.get('residenza','—')}</td></tr>
        <tr style="background:#fff"><td style="padding:10px;font-weight:bold">Codice Fiscale</td><td style="padding:10px">{user.get('codice_fiscale','—')}</td></tr>
        <tr><td style="padding:10px;font-weight:bold">Data registrazione</td><td style="padding:10px">{user.get('data_registrazione','')}</td></tr>
        <tr style="background:#fff"><td style="padding:10px;font-weight:bold">Privacy app</td><td style="padding:10px">{'✅ Accettata' if user.get('privacy_app') else '❌ Non accettata'}</td></tr>
        <tr><td style="padding:10px;font-weight:bold">Privacy commerciale</td><td style="padding:10px">{'✅ Accettata' if user.get('privacy_commerciale') else '❌ Non accettata'}</td></tr>
      </table>
    </div>
    """
    _send_email(ADMIN_EMAIL, f"🏐 Nuovo atleta: {nome}", html)


def _email_iscrizione_torneo(user: dict, torneo: dict):
    """Email di conferma iscrizione a un torneo."""
    nome = f"{user['nome']} {user['cognome']}"
    nome_torneo = torneo.get("nome", "Torneo")
    data_torneo = torneo.get("data", "—")
    formato = torneo.get("formato_set", "—")
    punteggio = torneo.get("punteggio_max", "—")
    luogo = torneo.get("luogo", "—")
    tipo = torneo.get("tipo_tabellone", "—")

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#f0f0f0;border-radius:12px;overflow:hidden">
      <div style="background:linear-gradient(135deg,#e8002d,#b00020);padding:32px;text-align:center">
        <div style="font-size:3rem">🏐</div>
        <h1 style="color:#fff;margin:8px 0;font-size:1.6rem;letter-spacing:2px">MBT-BVL 2.0</h1>
        <p style="color:rgba(255,255,255,0.8);margin:0">Conferma Iscrizione Torneo</p>
      </div>
      <div style="padding:32px">
        <h2 style="color:#e8002d">Iscrizione confermata, {nome}! 🎉</h2>
        <p>Sei stato/a iscritto/a con successo al torneo:</p>
        <div style="background:#13131a;border:2px solid #e8002d;border-radius:10px;padding:20px;margin:20px 0">
          <h3 style="color:#ffd700;margin-top:0">🏆 {nome_torneo}</h3>
          <p style="margin:6px 0">📅 <strong>Data:</strong> {data_torneo}</p>
          <p style="margin:6px 0">📍 <strong>Luogo:</strong> {luogo}</p>
          <p style="margin:6px 0">🏐 <strong>Formato:</strong> {formato} · Max {punteggio} pt</p>
          <p style="margin:6px 0">📊 <strong>Tabellone:</strong> {tipo}</p>
        </div>
        <p>Presenta questa email il giorno del torneo come conferma di iscrizione.</p>
        <p style="color:#888;font-size:0.8rem;margin-top:24px">
          Per informazioni: {ADMIN_EMAIL}<br>
          MBT-BVL 2.0 — Master Ball Academy
        </p>
      </div>
    </div>
    """
    _send_email(user["email"], f"✅ Iscrizione confermata: {nome_torneo}", html)
    # Notifica anche all'admin
    html_admin = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px">
      <h2 style="color:#e8002d">🏐 Nuova Iscrizione Torneo — MBT-BVL 2.0</h2>
      <p><strong>Atleta:</strong> {nome} ({user['email']})</p>
      <p><strong>Torneo:</strong> {nome_torneo}</p>
      <p><strong>Data torneo:</strong> {data_torneo}</p>
      <p><strong>Data iscrizione:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    """
    _send_email(ADMIN_EMAIL, f"🏐 Iscrizione: {nome} → {nome_torneo}", html_admin)


# ─── REGISTRAZIONE ────────────────────────────────────────────────────────────

def render_registrazione(state):
    """Schermata registrazione nuovo atleta con profilo completo."""
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 700px !important; padding-top: 40px !important; }
    .reg-section {
        background: #13131a;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .reg-title {
        font-size: 0.65rem; font-weight: 700;
        letter-spacing: 3px; text-transform: uppercase;
        color: #e8002d; margin-bottom: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:20px 0 28px">
        <div style="font-size:3rem">🏐</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:2rem;font-weight:900;
            text-transform:uppercase;letter-spacing:4px;color:#fff">MBT-BVL 2.0</div>
        <div style="color:#888;font-size:0.7rem;letter-spacing:3px;text-transform:uppercase;margin-top:4px">
            Registrazione Nuovo Atleta</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sezione 1: Credenziali ────────────────────────────────────────────────
    st.markdown('<div class="reg-section"><div class="reg-title">🔐 Credenziali di Accesso</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        reg_nome = st.text_input("Nome *", key="reg_nome", placeholder="Es. Marco")
    with col2:
        reg_cognome = st.text_input("Cognome *", key="reg_cognome", placeholder="Es. Rossi")
    reg_email = st.text_input("Email *", key="reg_email", placeholder="tuaemail@esempio.com")
    col_pw1, col_pw2 = st.columns(2)
    with col_pw1:
        reg_pw = st.text_input("Password *", type="password", key="reg_pw",
                                placeholder="Minimo 6 caratteri")
    with col_pw2:
        reg_pw2 = st.text_input("Conferma Password *", type="password", key="reg_pw2",
                                 placeholder="Ripeti la password")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sezione 2: Dati Anagrafici ────────────────────────────────────────────
    st.markdown('<div class="reg-section"><div class="reg-title">👤 Dati Anagrafici (Profilo Atleta)</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        reg_telefono = st.text_input("Numero di Telefono", key="reg_tel", placeholder="+39 320 1234567")
        reg_nascita  = st.text_input("Data di Nascita", key="reg_nascita", placeholder="GG/MM/AAAA")
    with col4:
        reg_cf        = st.text_input("Codice Fiscale", key="reg_cf", placeholder="RSSMRC80A01H501Z")
        reg_residenza = st.text_input("Luogo di Residenza", key="reg_res", placeholder="Città (Provincia)")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sezione 3: Privacy & Consensi ────────────────────────────────────────
    st.markdown('<div class="reg-section"><div class="reg-title">📋 Informativa Privacy e Consensi (D.lgs. 196/2003 e GDPR 679/2016)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#0a0a0f;border-radius:8px;padding:14px;margin-bottom:14px;
        font-size:0.78rem;color:#aaa;max-height:120px;overflow-y:auto;line-height:1.6">
        <strong style="color:#fff">Informativa sul trattamento dei dati personali</strong><br>
        Ai sensi del D.lgs. 196/2003 (Codice Privacy) e del Regolamento UE 679/2016 (GDPR), 
        Master Ball Academy, in qualità di titolare del trattamento, informa che i dati personali 
        raccolti saranno trattati per finalità di gestione delle attività sportive, iscrizione a 
        tornei, comunicazioni istituzionali e, previo consenso, per finalità di marketing e 
        comunicazioni commerciali. I dati non saranno ceduti a terzi senza consenso esplicito. 
        L'interessato ha diritto di accesso, rettifica, cancellazione e portabilità dei propri dati 
        scrivendo a {admin_email}. Il conferimento dei dati contrassegnati con * è obbligatorio 
        per la fruizione del servizio.
    </div>
    """.replace("{admin_email}", ADMIN_EMAIL), unsafe_allow_html=True)

    priv_app = st.checkbox(
        "✅ Acconsento al trattamento dei dati personali per l'utilizzo dell'applicazione MBT-BVL 2.0, "
        "la gestione delle iscrizioni ai tornei e le comunicazioni istituzionali. (Obbligatorio) *",
        key="reg_priv_app"
    )
    priv_comm = st.checkbox(
        "📧 Acconsento al trattamento dei dati personali per finalità commerciali e promozionali "
        "(newsletter, offerte, eventi speciali). (Facoltativo)",
        key="reg_priv_comm"
    )
    priv_img = st.checkbox(
        "📸 Acconsento all'utilizzo della mia immagine (foto/video) durante gli eventi sportivi "
        "organizzati da Master Ball Academy per finalità di comunicazione e promozione. (Facoltativo)",
        key="reg_priv_img"
    )
    priv_maggiorenne = st.checkbox(
        "🔞 Dichiaro di essere maggiorenne (18+ anni) oppure di avere il consenso "
        "del genitore/tutore legale per la partecipazione alle attività sportive. (Obbligatorio) *",
        key="reg_priv_eta"
    )
    priv_regolamento = st.checkbox(
        "📜 Dichiaro di aver letto e di accettare il Regolamento Sportivo di Master Ball Academy "
        "e le norme di partecipazione ai tornei di beach volleyball. (Obbligatorio) *",
        key="reg_priv_reg"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Pulsanti ──────────────────────────────────────────────────────────────
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button("🏐 COMPLETA REGISTRAZIONE", use_container_width=True,
                     type="primary", key="btn_completa_reg"):
            _processa_registrazione(
                state=state,
                nome=reg_nome.strip(), cognome=reg_cognome.strip(),
                email=reg_email.strip().lower(), pw=reg_pw, pw2=reg_pw2,
                telefono=reg_telefono.strip(), nascita=reg_nascita.strip(),
                cf=reg_cf.strip().upper(), residenza=reg_residenza.strip(),
                priv_app=priv_app, priv_comm=priv_comm,
                priv_img=priv_img, priv_maggiorenne=priv_maggiorenne,
                priv_regolamento=priv_regolamento,
            )
    with col_btn2:
        if st.button("← Torna al Login", use_container_width=True, key="btn_back_login"):
            st.session_state.show_registrazione = False
            st.rerun()


def _processa_registrazione(state, nome, cognome, email, pw, pw2,
                             telefono, nascita, cf, residenza,
                             priv_app, priv_comm, priv_img,
                             priv_maggiorenne, priv_regolamento):
    """Valida e salva la registrazione."""
    errors = []

    if not nome or not cognome:
        errors.append("Nome e cognome sono obbligatori.")
    if not email or "@" not in email:
        errors.append("Inserisci un'email valida.")
    if len(pw) < 6:
        errors.append("La password deve essere di almeno 6 caratteri.")
    if pw != pw2:
        errors.append("Le password non coincidono.")
    if not priv_app:
        errors.append("Devi accettare il consenso obbligatorio per l'utilizzo dell'app.")
    if not priv_maggiorenne:
        errors.append("Devi confermare la maggiore età o il consenso del tutore.")
    if not priv_regolamento:
        errors.append("Devi accettare il Regolamento Sportivo.")

    users = _load_users()
    if email in users:
        errors.append("Questa email è già registrata. Prova ad accedere.")

    if errors:
        for e in errors:
            st.error(e)
        return

    # Crea utente
    user = {
        "email": email,
        "password_hash": _hash_pw(pw),
        "nome": nome,
        "cognome": cognome,
        "telefono": telefono,
        "data_nascita": nascita,
        "codice_fiscale": cf,
        "residenza": residenza,
        "privacy_app": priv_app,
        "privacy_commerciale": priv_comm,
        "privacy_immagine": priv_img,
        "data_registrazione": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "atleta_id": None,   # verrà collegato all'atleta in data_manager
    }
    users[email] = user
    _save_users(users)

    # Crea atleta in data_manager se non esiste già con stesso nome
    nome_completo = f"{nome} {cognome}"
    esistente = next((a for a in state["atleti"]
                      if a["nome"].lower() == nome_completo.lower()), None)
    if esistente:
        user["atleta_id"] = esistente["id"]
        users[email]["atleta_id"] = esistente["id"]
        _save_users(users)
    else:
        from data_manager import new_atleta, save_state
        atleta = new_atleta(nome, cognome)
        atleta["email"] = email
        atleta["telefono"] = telefono
        atleta["data_nascita"] = nascita
        atleta["codice_fiscale"] = cf
        atleta["residenza"] = residenza
        state["atleti"].append(atleta)
        save_state(state)
        user["atleta_id"] = atleta["id"]
        users[email]["atleta_id"] = atleta["id"]
        _save_users(users)

    # Email automatiche
    _email_benvenuto_atleta(user)
    _email_admin_nuovo_atleta(user)

    st.success(f"✅ Registrazione completata! Benvenuto/a, {nome}!")
    st.info("📧 Ti abbiamo inviato un'email di conferma. Controlla anche la cartella spam.")
    st.session_state.show_registrazione = False
    st.rerun()


# ─── LOGIN ATLETA REGISTRATO ──────────────────────────────────────────────────

def login_atleta(email: str, pw: str) -> dict | None:
    """Restituisce il profilo utente se le credenziali sono corrette."""
    users = _load_users()
    user = users.get(email.lower().strip())
    if user and user.get("password_hash") == _hash_pw(pw):
        return user
    return None


def get_user_by_email(email: str) -> dict | None:
    users = _load_users()
    return users.get(email.lower().strip())


def get_all_registered_users() -> dict:
    return _load_users()


# ─── PROFILO ATLETA (pagina) ──────────────────────────────────────────────────

def render_profilo_personale(state):
    """Pagina del profilo personale dell'atleta loggato."""
    user = st.session_state.get("logged_user")
    if not user:
        st.error("Devi essere loggato come atleta per vedere il profilo.")
        return

    from data_manager import get_atleta_by_id, calcola_overall_fifa, get_card_type

    nome_completo = f"{user['nome']} {user['cognome']}"
    atleta_id = user.get("atleta_id")
    atleta = get_atleta_by_id(state, atleta_id) if atleta_id else None

    # ── Header profilo ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#13131a,#1a1a2e);border:2px solid #e8002d;
        border-radius:16px;padding:28px;margin-bottom:24px;display:flex;align-items:center;gap:20px">
        <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#e8002d,#ffd700);
            display:flex;align-items:center;justify-content:center;font-size:2rem;flex-shrink:0">🏐</div>
        <div>
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;font-weight:900;
                color:#fff;text-transform:uppercase;letter-spacing:2px">{nome_completo}</div>
            <div style="color:#888;font-size:0.75rem;letter-spacing:2px">{user['email']}</div>
            <div style="color:#e8002d;font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;margin-top:4px">
                Atleta Registrato · MBT-BVL 2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_stats, tab_anagrafica, tab_tornei = st.tabs(["📊 Statistiche", "👤 Dati Personali", "🏆 Tornei"])

    # ── Tab Statistiche ───────────────────────────────────────────────────────
    with tab_stats:
        if atleta:
            s = atleta["stats"]
            overall = calcola_overall_fifa(atleta)
            card_type = get_card_type(overall)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("OVR", overall)
            with col2:
                st.metric("Tornei", s["tornei"])
            with col3:
                st.metric("Vittorie", s["vittorie"])
            with col4:
                win_rate = round(s["vittorie"] / max(s["tornei"], 1) * 100, 1)
                st.metric("Win Rate", f"{win_rate}%")

            st.divider()
            st.markdown("#### 🎯 Attributi")
            attrs = {
                "Attacco ⚡": s.get("attacco", 40),
                "Difesa 🛡️": s.get("difesa", 40),
                "Muro 🧱": s.get("muro", 40),
                "Ricezione 🤲": s.get("ricezione", 40),
                "Battuta 🏐": s.get("battuta", 40),
                "Alzata 🙌": s.get("alzata", 40),
            }
            col_a, col_b = st.columns(2)
            for i, (attr_name, val) in enumerate(attrs.items()):
                with (col_a if i % 2 == 0 else col_b):
                    st.markdown(f"""
                    <div style="margin-bottom:10px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.82rem">
                            <span>{attr_name}</span>
                            <span style="font-weight:700;color:#ffd700">{val}</span>
                        </div>
                        <div style="background:#1a1a2e;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,#e8002d,#ffd700);
                                width:{val}%;height:8px;border-radius:4px;transition:width 0.3s"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#13131a;border:1px solid #333;border-radius:8px;
                padding:12px 16px;margin-top:8px;font-size:0.8rem;color:#888">
                🃏 Categoria carta: <strong style="color:#ffd700">{card_type.replace('_',' ').upper()}</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Nessuna statistica disponibile. Partecipa a un torneo per sbloccare le tue statistiche!")

    # ── Tab Dati Personali ────────────────────────────────────────────────────
    with tab_anagrafica:
        st.markdown("#### 👤 I tuoi dati personali")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Email:** {user.get('email','—')}")
            st.markdown(f"**Telefono:** {user.get('telefono','—')}")
            st.markdown(f"**Data di nascita:** {user.get('data_nascita','—')}")
        with col2:
            st.markdown(f"**Codice Fiscale:** {user.get('codice_fiscale','—')}")
            st.markdown(f"**Residenza:** {user.get('residenza','—')}")
            st.markdown(f"**Registrato il:** {user.get('data_registrazione','—')}")

        st.divider()
        st.markdown("#### 📋 Consensi Privacy")
        privacies = [
            ("Utilizzo app", user.get("privacy_app", False)),
            ("Marketing commerciale", user.get("privacy_commerciale", False)),
            ("Utilizzo immagine", user.get("privacy_immagine", False)),
        ]
        for label, val in privacies:
            icon = "✅" if val else "❌"
            st.markdown(f"{icon} **{label}**")

    # ── Tab Tornei ────────────────────────────────────────────────────────────
    with tab_tornei:
        st.markdown("#### 🏆 Storico Tornei")
        if atleta and atleta["stats"].get("storico_posizioni"):
            storico = atleta["stats"]["storico_posizioni"]
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            for entry in storico:
                torneo_nome, pos = entry[0], entry[1]
                icon = medals.get(pos, f"#{pos}")
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    st.markdown(f"**{icon} {torneo_nome}**")
                with col_t2:
                    st.markdown(f"<span style='color:#888'>{pos}° posto</span>", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("Nessun torneo completato ancora.")

        # Iscrizioni ai prossimi tornei
        tornei_futuri = state.get("tornei_programmati", [])
        if tornei_futuri:
            st.markdown("#### 📅 Prossimi Tornei Disponibili")
            for torneo in tornei_futuri:
                _render_card_torneo_programmato(torneo, user, state, mostra_iscrizione=True)


def _render_card_torneo_programmato(torneo: dict, user: dict, state, mostra_iscrizione=False):
    """Card visuale per un torneo programmato."""
    nome = torneo.get("nome_programmato", "Torneo")
    data = torneo.get("data_programmata", "—")
    luogo = torneo.get("luogo", "—")
    formato = torneo.get("formato_set", "—")
    desc = torneo.get("descrizione", "")
    copertina = torneo.get("copertina_b64")
    iscritti = torneo.get("iscritti", [])
    tid = torneo.get("id", "")

    # Determina se l'utente è già iscritto
    user_email = user.get("email", "") if user else ""
    gia_iscritto = user_email in iscritti

    copertina_html = ""
    if copertina:
        copertina_html = f'<img src="data:image/jpeg;base64,{copertina}" style="width:100%;height:160px;object-fit:cover;border-radius:10px 10px 0 0;display:block">'

    st.markdown(f"""
    <div style="background:#13131a;border:2px solid {'#00c851' if gia_iscritto else '#2a2a3a'};
        border-radius:12px;overflow:hidden;margin-bottom:16px">
        {copertina_html}
        <div style="padding:16px 20px">
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;font-weight:800;
                color:{'#00c851' if gia_iscritto else '#fff'};text-transform:uppercase">{nome}</div>
            <div style="color:#888;font-size:0.78rem;margin:6px 0">
                📅 {data} &nbsp;·&nbsp; 📍 {luogo} &nbsp;·&nbsp; 🏐 {formato}
            </div>
            {f'<div style="color:#aaa;font-size:0.82rem;margin-top:8px">{desc}</div>' if desc else ''}
            <div style="margin-top:10px;font-size:0.72rem;color:#666">
                {len(iscritti)} iscritti {'· <span style="color:#00c851;font-weight:700">✅ Sei iscritto/a</span>' if gia_iscritto else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mostra_iscrizione and user and not gia_iscritto:
        if st.button(f"✅ Iscriviti a {nome}", key=f"iscr_{tid}_{user_email}", use_container_width=True):
            _iscrivi_utente_torneo(torneo, user, state)
    elif mostra_iscrizione and gia_iscritto:
        if st.button(f"❌ Annulla iscrizione a {nome}", key=f"disiscr_{tid}_{user_email}",
                     use_container_width=True):
            _disiscr_utente_torneo(torneo, user, state)


def _iscrivi_utente_torneo(torneo: dict, user: dict, state):
    """Iscrive l'utente al torneo e invia email di conferma."""
    from data_manager import save_state
    iscritti = torneo.setdefault("iscritti", [])
    if user["email"] not in iscritti:
        iscritti.append(user["email"])
        save_state(state)
        _email_iscrizione_torneo(user, {
            "nome": torneo.get("nome_programmato", "Torneo"),
            "data": torneo.get("data_programmata", "—"),
            "luogo": torneo.get("luogo", "—"),
            "formato_set": torneo.get("formato_set", "—"),
            "punteggio_max": torneo.get("punteggio_max", "—"),
            "tipo_tabellone": torneo.get("tipo_tabellone", "—"),
        })
        st.success("✅ Iscrizione confermata! Ti abbiamo inviato una email di conferma.")
        st.rerun()


def _disiscr_utente_torneo(torneo: dict, user: dict, state):
    """Rimuove l'iscrizione dell'utente al torneo."""
    from data_manager import save_state
    iscritti = torneo.get("iscritti", [])
    if user["email"] in iscritti:
        iscritti.remove(user["email"])
        save_state(state)
        st.info("Iscrizione annullata.")
        st.rerun()
