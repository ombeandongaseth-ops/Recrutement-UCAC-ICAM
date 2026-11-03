import base64
import csv
import datetime
import hmac
import html
import io
import os
import random
import re
import threading
import time
import zipfile

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONSTANTES ET FICHIERS
# ---------------------------------------------------------
FICHIER_CANDIDATS = "candidats_recrutement_ucac_icam.csv"
FICHIER_ECOLES = "ecoles_recrutement.csv"
FICHIER_STANDS = "stands_recrutement.csv"
FICHIER_PLANNING = "planning_recrutement.csv"
FICHIER_DEMANDES_DESISTEMENT = "demandes_desistement.csv"
FICHIER_PRESENCE = "presence_temps_reel.csv"

ADMIN_EMAILS = [
    "ninon.ombeandonga@2030.ucac-icam.com",
    "gedidia.mabahou@2030.ucac-icam.com",
    "brainy.ngamouyi@2030.ucac-icam.com",
    "admin@ucac-icam.com",
]

STATUTS_AUTO = ["BP", "CP (Cycle Préparatoire)", "L1"]
STATUTS_MANUELS = [
    "B1",
    "L2",
    "L3",
    "Membre de l'administration",
    "Enseignant / Professeur",
]
STATUTS_POSSIBLES = STATUTS_AUTO + STATUTS_MANUELS

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
HEURES_DISPONIBLES = [f"{h:02d}h00" for h in range(7, 19)]

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

CHAMPS_CANDIDATS = ["nom", "statut_filiere", "ecole", "quartier", "role_souhaite", "jours_dispo"]
CHAMPS_PLANNING = [
    "date_mission", "heure_debut", "heure_fin", "type_mission",
    "lieu", "quartier", "arrondissement", "groupe", "date_iso",
]
CHAMPS_DESISTEMENTS = ["email", "nom", "raison", "date_demande"]

REGEX_EMAIL = re.compile(r"^[a-z0-9._%+\-]+@(2030\.)?ucac-icam\.com$")

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(page_title="Recrutement UCAC-ICAM", page_icon="🎓", layout="wide")


# ---------------------------------------------------------
# OUTILS GÉNÉRAUX
# ---------------------------------------------------------
def esc(valeur):
    """Échappe le HTML pour éviter toute injection dans les blocs unsafe_allow_html."""
    return html.escape(str(valeur if valeur is not None else ""))


def formater_date_fr(d):
    """Retourne une date en français : 'Lundi 03 novembre 2026'."""
    return f"{JOURS_FR[d.weekday()]} {d.day:02d} {MOIS_FR[d.month - 1]} {d.year}"


def heure_en_entier(h):
    """'07h00' -> 7 (0 si format inattendu)."""
    try:
        return int(str(h)[:2])
    except (ValueError, TypeError):
        return 0


@st.cache_resource
def obtenir_verrou():
    """Verrou partagé entre toutes les sessions pour éviter la corruption des données."""
    return threading.RLock()


# ---------------------------------------------------------
# COUCHE DE STOCKAGE : PostgreSQL persistant OU fichiers locaux
# ---------------------------------------------------------
# Sur un hébergement comme Streamlit Community Cloud, le disque est éphémère : les fichiers CSV
# sont effacés à chaque redémarrage / redéploiement. Quand DATABASE_URL est défini (secrets ou
# variable d'environnement), toutes les données sont donc stockées dans une base PostgreSQL
# externe. Sans DATABASE_URL, l'application garde l'ancien fonctionnement (fichiers locaux).
FICHIERS_SAUVEGARDE = [
    FICHIER_CANDIDATS,
    FICHIER_ECOLES,
    FICHIER_STANDS,
    FICHIER_PLANNING,
    FICHIER_DEMANDES_DESISTEMENT,
]

# Cache valable uniquement pour l'exécution en cours (le script est ré-exécuté à chaque interaction)
_CACHE_RUN = {"charge": False, "donnees": {}}


def obtenir_url_db():
    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return str(url)
    except Exception:
        pass
    return os.environ.get("DATABASE_URL") or None


def stockage_persistant_actif():
    return obtenir_url_db() is not None


@st.cache_resource(show_spinner=False)
def _ouvrir_connexion(url):
    import psycopg2  # nécessite `psycopg2-binary` dans requirements.txt

    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS donnees (
                nom TEXT PRIMARY KEY,
                contenu TEXT NOT NULL,
                maj TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    return conn


def _executer_db(sql, params=(), lecture=False):
    """Exécute une requête ; rouvre la connexion et réessaie une fois si elle a été coupée."""
    url = obtenir_url_db()
    derniere_erreur = None
    for _ in range(2):
        try:
            conn = _ouvrir_connexion(url)
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall() if lecture else None
        except Exception as e:
            derniere_erreur = e
            _ouvrir_connexion.clear()
    raise derniere_erreur


def _charger_tout_db():
    """Une seule requête par exécution : charge tout le contenu de la base en mémoire."""
    if not _CACHE_RUN["charge"]:
        lignes = _executer_db("SELECT nom, contenu FROM donnees", lecture=True)
        _CACHE_RUN["donnees"] = {nom: contenu for nom, contenu in lignes}
        _CACHE_RUN["charge"] = True


def lire_texte(fichier):
    """Retourne le contenu texte d'un « fichier » de données, ou None s'il n'existe pas encore."""
    if stockage_persistant_actif():
        _charger_tout_db()
        if fichier in _CACHE_RUN["donnees"]:
            return _CACHE_RUN["donnees"][fichier]
        # Migration automatique : première utilisation de la base avec d'anciens CSV locaux
        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8", newline="") as f:
                texte = f.read()
            ecrire_texte(fichier, texte)
            return texte
        return None
    if not os.path.exists(fichier):
        return None
    with open(fichier, "r", encoding="utf-8", newline="") as f:
        return f.read()


def ecrire_texte(fichier, texte):
    """Enregistre le contenu texte d'un « fichier » de données (base PostgreSQL ou fichier local)."""
    with obtenir_verrou():
        if stockage_persistant_actif():
            _executer_db(
                """
                INSERT INTO donnees (nom, contenu) VALUES (%s, %s)
                ON CONFLICT (nom) DO UPDATE SET contenu = EXCLUDED.contenu, maj = now()
                """,
                (fichier, texte),
            )
            _CACHE_RUN["donnees"][fichier] = texte
        else:
            tmp = f"{fichier}.tmp"
            with open(tmp, "w", newline="", encoding="utf-8") as f:
                f.write(texte)
            os.replace(tmp, fichier)


def ecrire_atomique(fichier, fonction_ecriture):
    """Construit le contenu en mémoire puis l'enregistre d'un seul bloc (jamais à moitié écrit)."""
    tampon = io.StringIO(newline="")
    fonction_ecriture(tampon)
    ecrire_texte(fichier, tampon.getvalue())


def verifier_stockage():
    """Stoppe l'application si la base est injoignable (évite d'écraser des données par du vide)."""
    if stockage_persistant_actif():
        try:
            _charger_tout_db()
        except Exception as e:
            st.error(
                "❌ Impossible de joindre la base de données. Par sécurité, l'application est suspendue "
                "pour ne pas écraser vos données. Vérifiez `DATABASE_URL` puis rechargez la page."
            )
            st.caption(f"Détail technique : {type(e).__name__}")
            st.stop()


def construire_sauvegarde_zip():
    """Archive ZIP contenant tous les fichiers de données (candidats, planning, écoles, stands, désistements)."""
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        for nom in FICHIERS_SAUVEGARDE:
            texte = lire_texte(nom)
            if texte is not None:
                z.writestr(nom, texte)
    return tampon.getvalue()


def restaurer_sauvegarde_zip(octets):
    """Restaure les fichiers connus depuis une archive ZIP ; retourne la liste des fichiers restaurés."""
    restaures = []
    with zipfile.ZipFile(io.BytesIO(octets)) as z:
        for nom in z.namelist():
            if nom in FICHIERS_SAUVEGARDE:
                ecrire_texte(nom, z.read(nom).decode("utf-8-sig"))
                restaures.append(nom)
    return restaures


def obtenir_mot_de_passe_admin():
    """Mot de passe admin optionnel : st.secrets['ADMIN_PASSWORD'] ou variable d'environnement."""
    try:
        mdp = st.secrets.get("ADMIN_PASSWORD")
        if mdp:
            return str(mdp)
    except Exception:
        pass
    return os.environ.get("ADMIN_PASSWORD", "") or None


# ---------------------------------------------------------
# CACHING DE L'IMAGE D'ARRIÈRE-PLAN ET DU LOGO SPLASH
# ---------------------------------------------------------
def _image_en_base64(noms_fichiers):
    for nom in noms_fichiers:
        if os.path.exists(nom):
            try:
                with open(nom, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                mime = "image/jpeg" if nom.endswith((".jpg", ".jpeg")) else "image/png"
                return f"data:{mime};base64,{encoded}"
            except Exception:
                return None
    return None


@st.cache_data(show_spinner=False)
def Obtenir_bg_base64():
    return _image_en_base64(["welcome.jpg", "welcome.jpeg", "welcome.png"])


@st.cache_data(show_spinner=False)
def Obtenir_logo_splash_base64():
    return _image_en_base64(["logo_splash.png", "logo_splash.jpg", "logo_splash.jpeg"])


# ---------------------------------------------------------
# FONCTIONS DE PERSISTANCE CSV & PRÉSENCE
# ---------------------------------------------------------
def charger_csv_liste(fichier):
    texte = lire_texte(fichier)
    if texte is None:
        return []
    try:
        with io.StringIO(texte, newline="") as f:
            items = [line.strip() for line in f.read().splitlines() if line.strip()]
            return sorted(items, key=lambda x: x.lower())
    except Exception:
        return []


def sauvegarder_csv_liste(fichier, liste_items):
    liste_triee = sorted(liste_items, key=lambda x: x.lower())

    def _ecrire(f):
        for item in liste_triee:
            f.write(f"{item}\n")

    ecrire_atomique(fichier, _ecrire)


def charger_candidats():
    texte = lire_texte(FICHIER_CANDIDATS)
    if texte is None:
        return []
    try:
        with io.StringIO(texte, newline="") as f:
            reader = csv.DictReader(f)
            candidats = []
            for row in reader:
                if not row.get("statut_filiere"):
                    row["statut_filiere"] = "L1"
                if not row.get("role_souhaite"):
                    row["role_souhaite"] = "Écoles et Stands"
                if not row.get("jours_dispo"):
                    row["jours_dispo"] = "Tous les jours"
                candidats.append(row)
            return sorted(candidats, key=lambda x: (x.get("nom") or "").lower())
    except Exception:
        return []


def sauvegarder_candidats(candidats):
    candidats_tries = sorted(candidats, key=lambda x: (x.get("nom") or "").lower())

    def _ecrire(f):
        writer = csv.DictWriter(f, fieldnames=CHAMPS_CANDIDATS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidats_tries)

    ecrire_atomique(FICHIER_CANDIDATS, _ecrire)


def charger_planning():
    texte = lire_texte(FICHIER_PLANNING)
    if texte is None:
        return []
    try:
        with io.StringIO(texte, newline="") as f:
            reader = csv.DictReader(f)
            planning = []
            for row in reader:
                if "date_mission" not in row or not row["date_mission"]:
                    row["date_mission"] = row.get("jour", "Date non précisée")
                row.setdefault("date_iso", "")
                planning.append(row)
            return planning
    except Exception:
        return []


def sauvegarder_planning(planning):
    def _ecrire(f):
        writer = csv.DictWriter(f, fieldnames=CHAMPS_PLANNING, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(planning)

    ecrire_atomique(FICHIER_PLANNING, _ecrire)


def charger_desistements():
    texte = lire_texte(FICHIER_DEMANDES_DESISTEMENT)
    if texte is None:
        return []
    try:
        with io.StringIO(texte, newline="") as f:
            desistements = list(csv.DictReader(f))
            return sorted(desistements, key=lambda x: (x.get("nom") or "").lower())
    except Exception:
        return []


def sauvegarder_desistements(desistements):
    desistements_tries = sorted(desistements, key=lambda x: (x.get("nom") or "").lower())

    def _ecrire(f):
        writer = csv.DictWriter(f, fieldnames=CHAMPS_DESISTEMENTS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(desistements_tries)

    ecrire_atomique(FICHIER_DEMANDES_DESISTEMENT, _ecrire)


def mettre_a_jour_presence(email):
    if not email:
        return
    maintenant = time.time()
    with obtenir_verrou():
        presences = {}
        try:
            texte = lire_texte(FICHIER_PRESENCE)
            if texte:
                with io.StringIO(texte, newline="") as f:
                    for row in csv.DictReader(f):
                        presences[row["email"]] = float(row["last_ping"])
        except Exception:
            pass

        if email not in presences or (maintenant - presences[email]) > 30:
            presences[email] = maintenant
            presences = {e: t for e, t in presences.items() if maintenant - t < 300}
            try:
                def _ecrire(f):
                    writer = csv.DictWriter(f, fieldnames=["email", "last_ping"])
                    writer.writeheader()
                    for e, t in presences.items():
                        writer.writerow({"email": e, "last_ping": t})

                ecrire_atomique(FICHIER_PRESENCE, _ecrire)
            except Exception:
                pass


def obtenir_utilisateurs_en_ligne():
    maintenant = time.time()
    en_ligne = []
    try:
        texte = lire_texte(FICHIER_PRESENCE)
        if texte:
            with io.StringIO(texte, newline="") as f:
                for row in csv.DictReader(f):
                    if maintenant - float(row["last_ping"]) < 300:
                        en_ligne.append(row["email"])
    except Exception:
        pass
    return sorted(en_ligne)


# ---------------------------------------------------------
# LOGIQUE MÉTIER
# ---------------------------------------------------------
def retirer_volontaire_du_planning(nom):
    """Retire un volontaire (par nom) de tous les groupes du planning, puis sauvegarde."""
    prefixe = f"{nom.strip().lower()} ("
    for p in st.session_state.planning:
        if p.get("groupe"):
            membres = [m.strip() for m in p["groupe"].split(",")]
            membres_filtres = [m for m in membres if not m.lower().startswith(prefixe)]
            p["groupe"] = ", ".join(membres_filtres)
    sauvegarder_planning(st.session_state.planning)


def nom_deja_inscrit(nom):
    nom_l = nom.strip().lower()
    return any((c.get("nom") or "").strip().lower() == nom_l for c in st.session_state.candidats)


def trier_planning(planning):
    """Tri chronologique (date ISO puis heure). Les anciennes lignes sans date ISO restent à la fin."""
    return sorted(
        planning,
        key=lambda p: (p.get("date_iso") or "9999-99-99", heure_en_entier(p.get("heure_debut"))),
    )


def trouver_conflits(date_iso, h_debut, h_fin, membres):
    """Retourne les noms de personnes déjà planifiées sur un créneau qui chevauche."""
    conflits = set()
    d1, f1 = heure_en_entier(h_debut), heure_en_entier(h_fin)
    for p in st.session_state.planning:
        if p.get("date_iso") != date_iso:
            continue
        d2, f2 = heure_en_entier(p.get("heure_debut")), heure_en_entier(p.get("heure_fin"))
        if d1 < f2 and d2 < f1:
            existants = {m.strip().lower() for m in (p.get("groupe") or "").split(",")}
            for m in membres:
                if m.strip().lower() in existants:
                    conflits.add(m)
    return sorted(conflits)


def recharger_donnees_partagees():
    """Recharge à chaque exécution les données partagées entre utilisateurs."""
    st.session_state.candidats = charger_candidats()
    st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES)
    st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS)
    st.session_state.planning = charger_planning()
    st.session_state.desistements = charger_desistements()


# ---------------------------------------------------------
# STYLES CSS SUR MESURE & ANIMATION SPLASH SCREEN
# ---------------------------------------------------------
bg_data = Obtenir_bg_base64()
bg_css = (
    f"""
.stApp {{
    background: linear-gradient(rgba(18, 20, 23, 0.70), rgba(18, 20, 23, 0.85)), url("{bg_data}");
    background-size: cover; background-position: center; background-attachment: fixed; color: #FFFFFF;
}}
"""
    if bg_data
    else ".stApp { background-color: #121417; color: #FFFFFF; }"
)

st.markdown(
    f"""
    <style>
    {bg_css}

    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}

    /* Animation du Splash Screen */
    @keyframes fadeInOut {{
        0% {{ opacity: 0; transform: scale(0.95); }}
        50% {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(1.05); }}
    }}

    .splash-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 75vh;
        text-align: center;
    }}

    .splash-image {{
        width: 160px;
        height: 160px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #1B72E8;
        box-shadow: 0 0 25px rgba(27, 114, 232, 0.5);
        animation: fadeInOut 2s ease-in-out infinite;
    }}

    .splash-title {{
        font-size: 26px;
        font-weight: bold;
        margin-top: 20px;
        color: #FFFFFF;
    }}

    .splash-subtitle {{
        font-size: 14px;
        color: #A0A5B1;
        margin-top: 8px;
    }}

    /* Positionnement et style des boutons de navigation */
    div.stButton > button {{
        width: 100% !important;
        height: 50px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        background-color: rgba(28, 32, 38, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(8px);
        transition: all 0.2s ease-in-out !important;
    }}
    div.stButton > button:hover {{
        background-color: #1B72E8 !important;
        border-color: #1B72E8 !important;
        color: #FFFFFF !important;
    }}

    /* Profil déroulant compact */
    .compact-profile-box {{
        background-color: #FFFFFF;
        color: #212529;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0px 4px 16px rgba(0,0,0,0.3);
        font-size: 13px;
        border: 1px solid #CCCCCC;
        max-width: 320px;
        margin-left: auto;
    }}
    .profile-info-line {{
        padding: 5px 0;
        color: #333333;
        border-bottom: 1px solid #E9ECEF;
        font-size: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* Cartes de planning et événements */
    .event-card {{
        background-color: rgba(28, 32, 38, 0.85);
        color: #FFFFFF;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-left: 4px solid #1B72E8;
        backdrop-filter: blur(5px);
    }}

    .online-badge {{
        display: inline-block;
        background-color: #10B981;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
    }}

    /* Sur petits écrans : cartes plus compactes */
    @media (max-width: 640px) {{
        .event-card {{ padding: 12px 14px; }}
        .compact-profile-box {{ max-width: 100%; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# INITIALISATION DES SESSIONS
# ---------------------------------------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_profile_menu" not in st.session_state:
    st.session_state.show_profile_menu = False
if "page_active" not in st.session_state:
    st.session_state.page_active = "Accueil"
if "tirage_temp_l1" not in st.session_state:
    st.session_state.tirage_temp_l1 = []
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

# Si la base persistante est configurée mais injoignable, on s'arrête plutôt que d'écraser des données
verifier_stockage()

# Données partagées : rechargées à chaque exécution pour que tous les utilisateurs voient les mêmes infos
recharger_donnees_partagees()

# ---------------------------------------------------------
# SPLASH SCREEN / ÉCRAN DE DÉMARRAGE ANIMÉ
# ---------------------------------------------------------
if not st.session_state.splash_done:
    splash_placeholder = st.empty()
    logo_data = Obtenir_logo_splash_base64()

    img_tag = f'<img src="{logo_data}" class="splash-image"/>' if logo_data else '<div style="font-size:60px;">🎓</div>'

    with splash_placeholder.container():
        st.markdown(
            f"""
            <div class="splash-container">
                {img_tag}
                <div class="splash-title">UCAC-ICAM</div>
                <div class="splash-subtitle">Chargement de la plateforme de recrutement...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(2.5)

    splash_placeholder.empty()
    st.session_state.splash_done = True
    st.rerun()

# ---------------------------------------------------------
# PAGE DE CONNEXION INITIALE
# ---------------------------------------------------------
if not st.session_state.user_email:
    st.title("Recrutement UCAC-ICAM")
    st.markdown("##### 👋 Bienvenue sur le Portail de Recrutement UCAC-ICAM")

    c_m1, col_box, c_m2 = st.columns([1, 2, 1])
    with col_box:
        with st.form("login_form"):
            st.markdown("#### 🔑 Connexion")
            email_input = st.text_input(
                "Adresse e-mail institutionnelle :", placeholder="exemple@ucac-icam.com"
            ).strip().lower()
            mdp_input = st.text_input(
                "Mot de passe administrateur (réservé aux administrateurs) :",
                type="password",
            )
            if st.form_submit_button("Se connecter"):
                if not email_input or not REGEX_EMAIL.match(email_input):
                    st.error(
                        "⚠️ Veuillez entrer une adresse e-mail institutionnelle valide "
                        "(@ucac-icam.com ou @2030.ucac-icam.com)."
                    )
                else:
                    est_admin = email_input in [e.lower() for e in ADMIN_EMAILS]
                    mdp_admin = obtenir_mot_de_passe_admin()
                    if est_admin and mdp_admin and not hmac.compare_digest(mdp_input, mdp_admin):
                        st.error("🔒 Mot de passe administrateur incorrect.")
                    else:
                        st.session_state.user_email = email_input
                        st.session_state.is_admin = est_admin
                        mettre_a_jour_presence(email_input)
                        st.rerun()
    st.stop()

# Suivi de la présence en direct
mettre_a_jour_presence(st.session_state.user_email)

# ---------------------------------------------------------
# EN-TÊTE PRINCIPAL ET BOUTON PROFIL
# ---------------------------------------------------------
premiere_lettre = st.session_state.user_email[0].upper() if st.session_state.user_email else "U"
user_prefix = st.session_state.user_email.split("@")[0].replace(".", " ").title()

col_title, col_space, col_user_corner = st.columns([6, 1, 3])

with col_title:
    st.title("Recrutement UCAC-ICAM")

with col_user_corner:
    c_btn_prof, c_btn_gear = st.columns([3, 1]) if st.session_state.is_admin else (col_user_corner, None)

    if c_btn_prof.button(f"⚪ {premiere_lettre} ▾", key="top_profile_btn", help="Mon Compte"):
        st.session_state.show_profile_menu = not st.session_state.show_profile_menu
        st.rerun()

    if st.session_state.is_admin and c_btn_gear:
        if c_btn_gear.button("⚙️", key="btn_admin_gear", help="Administration"):
            st.session_state.page_active = "Admin"
            st.rerun()

# Menu déroulant Profil
if st.session_state.show_profile_menu:
    col_l, col_pop = st.columns([7, 3])
    with col_pop:
        st.markdown(
            f"""
            <div class="compact-profile-box">
                <div class="profile-info-line">👤 <b>{esc(user_prefix)}</b></div>
                <div class="profile-info-line">📧 {esc(st.session_state.user_email)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔴 Déconnexion", key="btn_logout"):
            st.session_state.user_email = None
            st.session_state.is_admin = False
            st.session_state.show_profile_menu = False
            st.session_state.page_active = "Accueil"
            st.session_state.tirage_temp_l1 = []
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# EMPLACEMENT DES BOUTONS DE NAVIGATION
# ---------------------------------------------------------
nav_cols = st.columns(4)

with nav_cols[0]:
    if st.button("📝 Inscription / Profil", key="nav_inscrire"):
        st.session_state.page_active = "Inscription"
        st.rerun()

with nav_cols[1]:
    if st.button("📅 Planning des descentes", key="nav_planning"):
        st.session_state.page_active = "Accueil"
        st.rerun()

with nav_cols[2]:
    if st.button("🏫 Écoles de descentes", key="nav_ecoles"):
        st.session_state.page_active = "Ecoles"
        st.rerun()

with nav_cols[3]:
    if st.button("⛺ Stands de sensibilisation", key="nav_stands"):
        st.session_state.page_active = "Stands"
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# PAGES DE L'APPLICATION
# ---------------------------------------------------------

# --- ACCUEIL / PLANNING ---
if st.session_state.page_active == "Accueil":
    st.subheader("📅 Planning Officiel des Descentes")

    planning_trie = trier_planning(st.session_state.planning)

    if not planning_trie:
        st.info("Aucune descente planifiée pour le moment.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Descentes planifiées", len(planning_trie))
        m2.metric("Écoles", sum(1 for p in planning_trie if p.get("type_mission") == "École"))
        m3.metric("Stands", sum(1 for p in planning_trie if p.get("type_mission") == "Stand"))

        filtre_type = st.radio(
            "Afficher :", ["Tout", "École", "Stand"], horizontal=True, key="filtre_type_planning"
        )
        if filtre_type != "Tout":
            planning_trie = [p for p in planning_trie if p.get("type_mission") == filtre_type]

        df_plan = pd.DataFrame(planning_trie)

        if df_plan.empty:
            st.info("Aucune descente ne correspond à ce filtre.")
        else:
            col_date = "date_mission" if "date_mission" in df_plan.columns else "jour"
            dates_uniques = list(dict.fromkeys(df_plan[col_date]))  # ordre chronologique conservé
            for d in dates_uniques:
                st.markdown(
                    f'<div style="font-size:18px; font-weight:bold; margin-top:15px; color:#60A5FA;">📅 {esc(d)}</div>',
                    unsafe_allow_html=True,
                )
                items_d = df_plan[df_plan[col_date] == d]
                for _, row in items_d.iterrows():
                    icon = "🏫" if row.get("type_mission") == "École" else "⛺"
                    h_deb = row.get("heure_debut", row.get("heure", ""))
                    h_fin = row.get("heure_fin", "")
                    horaire = f"{h_deb} - {h_fin}" if h_fin else h_deb
                    quartier_info = (
                        f" | 📍 {row.get('quartier', '')} ({row.get('arrondissement', '')})"
                        if row.get("quartier")
                        else ""
                    )

                    st.markdown(
                        f"""
                        <div class="event-card">
                            <div style="font-weight:bold; font-size:16px;">{icon} {esc(row.get('lieu', ''))}</div>
                            <div style="color:#A0A5B1; font-size:13px; margin-top:4px;">⏱️ {esc(horaire)}{esc(quartier_info)}</div>
                            <div style="color:#93C5FD; font-size:13px; margin-top:6px;">👥 <b>Équipe constituée :</b> {esc(row.get('groupe', ''))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            csv_planning = pd.DataFrame(st.session_state.planning).to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Télécharger le planning (CSV)",
                data=csv_planning,
                file_name="planning_descentes.csv",
                mime="text/csv",
            )

# --- INSCRIPTION & RETRAIT ---
elif st.session_state.page_active == "Inscription":
    st.subheader("📝 Inscription & Gestion de ma participation")
    tab_inscr, tab_desist = st.tabs(["Formulaire d'inscription", "🏥 Demande de Retrait / Feu Vert"])

    with tab_inscr:
        with st.form("form_candidat", clear_on_submit=True):
            nom = st.text_input("Nom et Prénom complet :").strip().title()
            statut_filiere = st.selectbox("Filière / Niveau / Statut :", STATUTS_POSSIBLES)
            ecole = st.text_input("Ancien lycée / Établissement d'origine :").strip().title()
            quartier = st.text_input("Quartier de résidence :").strip().title()
            role_souhaite = st.selectbox(
                "Préférence d'affectation :",
                ["Écoles et Stands", "Descentes Écoles uniquement", "Animation Stands uniquement"],
            )
            jours_selectionnes = st.multiselect("Disponibilités :", JOURS_SEMAINE, default=JOURS_SEMAINE[:5])

            if st.form_submit_button("Valider mon inscription"):
                if not nom or not ecole or not quartier or not jours_selectionnes:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires.")
                elif nom_deja_inscrit(nom):
                    st.warning(f"ℹ️ {nom} est déjà inscrit(e). Aucun doublon n'a été créé.")
                else:
                    nouveau = {
                        "nom": nom,
                        "statut_filiere": statut_filiere,
                        "ecole": ecole,
                        "quartier": quartier,
                        "role_souhaite": role_souhaite,
                        "jours_dispo": ", ".join(jours_selectionnes),
                    }
                    st.session_state.candidats.append(nouveau)
                    sauvegarder_candidats(st.session_state.candidats)
                    st.success(f"✅ Inscription enregistrée avec succès pour {nom} ({statut_filiere}) !")

    with tab_desist:
        st.markdown("### 🏥 Signaler un empêchement ou une maladie")
        with st.form("form_desistement"):
            nom_volontaire = st.text_input("Nom et Prénom :", placeholder="Entrez votre nom et prénom").strip().title()
            raison = st.text_area("Raison du désistement :")
            if st.form_submit_button("Envoyer la demande de feu vert à l'Admin"):
                if not nom_volontaire or not raison.strip():
                    st.error("⚠️ Veuillez renseigner votre nom ainsi que le motif de votre absence.")
                else:
                    st.session_state.desistements.append(
                        {
                            "email": st.session_state.user_email,
                            "nom": nom_volontaire,
                            "raison": raison.strip(),
                            "date_demande": datetime.date.today().strftime("%d/%m/%Y"),
                        }
                    )
                    sauvegarder_desistements(st.session_state.desistements)
                    st.success("✅ Votre demande a été envoyée aux administrateurs.")

# --- ECOLES ---
elif st.session_state.page_active == "Ecoles":
    st.subheader("🏫 Écoles de descentes (Triées par ordre alphabétique)")
    if not st.session_state.ecoles_cibles:
        st.info("Aucune école enregistrée.")
    else:
        st.caption(f"{len(st.session_state.ecoles_cibles)} école(s) enregistrée(s)")
        recherche_e = st.text_input("🔎 Rechercher une école :", key="recherche_ecole").strip().lower()
        for i, e in enumerate(sorted(st.session_state.ecoles_cibles, key=lambda x: x.lower()), 1):
            if recherche_e in e.lower():
                st.markdown(f'<div class="event-card"><b>{i}. {esc(e)}</b></div>', unsafe_allow_html=True)

# --- STANDS ---
elif st.session_state.page_active == "Stands":
    st.subheader("⛺ Stands de sensibilisation (Triés par ordre alphabétique)")
    if not st.session_state.stands_cibles:
        st.info("Aucun stand enregistré.")
    else:
        st.caption(f"{len(st.session_state.stands_cibles)} stand(s) enregistré(s)")
        recherche_s = st.text_input("🔎 Rechercher un stand :", key="recherche_stand").strip().lower()
        for i, s in enumerate(sorted(st.session_state.stands_cibles, key=lambda x: x.lower()), 1):
            if recherche_s in s.lower():
                st.markdown(f'<div class="event-card"><b>{i}. {esc(s)}</b></div>', unsafe_allow_html=True)

# --- ADMIN ---
elif st.session_state.page_active == "Admin" and st.session_state.is_admin:
    st.subheader("⚙️ Zone d'Administration")

    if not obtenir_mot_de_passe_admin():
        st.warning(
            "🔓 Aucun mot de passe administrateur n'est configuré : n'importe qui connaissant une adresse admin "
            "peut accéder à cette zone. Définissez `ADMIN_PASSWORD` (dans `.streamlit/secrets.toml` ou en variable "
            "d'environnement) pour la protéger."
        )

    if not stockage_persistant_actif():
        st.warning(
            "💾 Stockage local temporaire : sur un hébergement comme Streamlit Community Cloud, les fichiers "
            "CSV sont effacés à chaque redémarrage. Configurez `DATABASE_URL` (voir l'onglet "
            "« Stockage & Sauvegarde »)."
        )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📅 Planification (3 Auto + 2 Manuel)",
            "🟢 Connexions en direct",
            "👥 Volontaires & Suppression",
            "🚦 Demandes Feu Vert",
            "🏫/⛺ Lieux",
            "💾 Stockage & Sauvegarde",
        ]
    )

    # 1. PLANIFICATION
    with tab1:
        st.markdown("### Créer un créneau de descente")
        st.info(
            "💡 **Règle de groupe :** Le programme choisit aléatoirement **3 personnes** parmi les BP, CP, L1. "
            "Vous sélectionnez ensuite manuellement **2 personnes** (Prof, Admin, B1, L2, L3)."
        )

        p_type = st.radio("Type de mission :", ["École", "Stand"], horizontal=True)
        lieux = sorted(
            st.session_state.ecoles_cibles if p_type == "École" else st.session_state.stands_cibles,
            key=lambda x: x.lower(),
        )

        candidats_auto = [
            c for c in st.session_state.candidats if c.get("statut_filiere") in STATUTS_AUTO
        ]
        candidats_manuels = [
            c for c in st.session_state.candidats if c.get("statut_filiere") in STATUTS_MANUELS
        ]

        col_tirage, col_res = st.columns([1, 2])
        with col_tirage:
            if st.button("🎲 Tirer au sort 3 L1/CP/BP"):
                if len(candidats_auto) < 3:
                    st.error(f"❌ Pas assez d'étudiants L1/CP/BP inscrits ({len(candidats_auto)}/3 requis).")
                else:
                    st.session_state.tirage_temp_l1 = random.sample(candidats_auto, 3)
                    st.success("Tirage effectué !")
            if st.session_state.tirage_temp_l1 and st.button("↩️ Réinitialiser le tirage", key="btn_reset_tirage"):
                st.session_state.tirage_temp_l1 = []
                st.rerun()

        with col_res:
            if st.session_state.tirage_temp_l1:
                st.markdown("**3 membres tirés au sort (L1 / CP / BP) :**")
                for item in st.session_state.tirage_temp_l1:
                    st.markdown(f"- **{item['nom']}** ({item.get('statut_filiere')})")
            else:
                st.warning("Aucun tirage en cours. Cliquez sur le bouton pour générer 3 candidats.")

        with st.form("form_p_hybrid"):
            date_choisie = st.date_input("Date exacte de la descente :", datetime.date.today())
            date_formatee = formater_date_fr(date_choisie)

            c_h1, c_h2 = st.columns(2)
            with c_h1:
                p_h_debut = st.selectbox("Heure de début :", HEURES_DISPONIBLES, index=1)
            with c_h2:
                p_h_fin = st.selectbox("Heure de fin :", HEURES_DISPONIBLES, index=5)

            p_lieu = st.selectbox("Lieu :", lieux if lieux else ["Aucun lieu disponible"])
            c_q, c_a = st.columns(2)
            with c_q:
                p_quartier = st.text_input("Quartier :").strip()
            with c_a:
                p_arrondissement = st.text_input("Arrondissement :").strip()

            noms_manuels = [
                f"{c['nom']} ({c.get('statut_filiere')})"
                for c in sorted(candidats_manuels, key=lambda x: x["nom"].lower())
            ]
            p_groupe_manuel = st.multiselect(
                "Sélectionner 2 encadrants / aînés (Prof, Admin, B1, L2, L3) :",
                noms_manuels,
                max_selections=2,
            )

            if st.form_submit_button("Valider et enregistrer la descente"):
                if not st.session_state.tirage_temp_l1:
                    st.error("⚠️ Veuillez effectuer d'abord le tirage au sort des 3 L1/CP/BP.")
                elif len(p_groupe_manuel) != 2:
                    st.error("⚠️ Vous devez sélectionner exactement 2 encadrants / aînés.")
                elif heure_en_entier(p_h_fin) <= heure_en_entier(p_h_debut):
                    st.error("⚠️ L'heure de fin doit être postérieure à l'heure de début.")
                elif p_lieu and p_lieu != "Aucun lieu disponible":
                    membres_auto_str = [
                        f"{c['nom']} ({c.get('statut_filiere')})" for c in st.session_state.tirage_temp_l1
                    ]
                    membres_tous = membres_auto_str + p_groupe_manuel

                    conflits = trouver_conflits(date_choisie.isoformat(), p_h_debut, p_h_fin, membres_tous)
                    if conflits:
                        st.warning(
                            "⚠️ Attention : déjà planifié(s) sur un créneau qui chevauche : " + ", ".join(conflits)
                        )

                    st.session_state.planning.append(
                        {
                            "date_mission": date_formatee,
                            "heure_debut": p_h_debut,
                            "heure_fin": p_h_fin,
                            "type_mission": p_type,
                            "lieu": p_lieu,
                            "quartier": p_quartier,
                            "arrondissement": p_arrondissement,
                            "groupe": ", ".join(membres_tous),
                            "date_iso": date_choisie.isoformat(),
                        }
                    )
                    sauvegarder_planning(st.session_state.planning)
                    st.session_state.tirage_temp_l1 = []
                    st.success("✅ Créneau ajouté au planning avec le groupe au complet (5 personnes) !")
                    st.rerun()
                else:
                    st.error("⚠️ Aucun lieu disponible : ajoutez d'abord un lieu dans l'onglet « Lieux ».")

        st.markdown("---")
        st.markdown("### Supprimer une descente planifiée")
        if st.session_state.planning:
            opts = [
                f"{i+1}. {p.get('date_mission', p.get('jour', 'Date inconnue'))} | {p.get('type_mission')} : {p.get('lieu')}"
                for i, p in enumerate(st.session_state.planning)
            ]
            idx_del = st.selectbox("Sélectionner le créneau à annuler :", range(len(opts)), format_func=lambda x: opts[x])
            if st.button("🗑️ Annuler ce créneau"):
                st.session_state.planning.pop(idx_del)
                sauvegarder_planning(st.session_state.planning)
                st.success("Créneau supprimé du planning.")
                st.rerun()

    # 2. CONNEXIONS EN DIRECT
    with tab2:
        st.markdown("### 🟢 Utilisateurs actuellement connectés au programme")
        st.caption("Mise à jour en temps réel (utilisateurs actifs au cours des 5 dernières minutes)")

        if st.button("🔄 Rafraîchir la liste des connexions"):
            st.rerun()

        connectes = obtenir_utilisateurs_en_ligne()
        if not connectes:
            st.info("Aucun utilisateur détecté en ligne actuellement.")
        else:
            st.markdown(f"**Nombre d'utilisateurs en ligne :** `{len(connectes)}`")
            for user in connectes:
                st.markdown(
                    f"""
                    <div style="background-color: rgba(16, 185, 129, 0.15); border: 1px solid #10B981;
                         border-radius: 8px; padding: 10px 15px; margin-bottom: 8px; display: flex; align-items: center;">
                        <span class="online-badge">EN LIGNE</span> &nbsp;&nbsp; <b>{esc(user)}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 3. VOLONTAIRES ET SUPPRESSION
    with tab3:
        st.markdown("### Liste des Volontaires inscrits")
        st.session_state.candidats = sorted(
            st.session_state.candidats, key=lambda x: (x.get("nom") or "").lower()
        )

        if st.session_state.candidats:
            df_cand = pd.DataFrame(st.session_state.candidats)

            # Statistiques rapides
            k1, k2, k3 = st.columns(3)
            k1.metric("Total volontaires", len(df_cand))
            k2.metric("L1 / CP / BP", int(df_cand["statut_filiere"].isin(STATUTS_AUTO).sum()))
            k3.metric("Encadrants (B1, L2, L3, Admin, Prof)", int(df_cand["statut_filiere"].isin(STATUTS_MANUELS).sum()))

            # Recherche et filtre
            f1, f2 = st.columns([2, 2])
            with f1:
                recherche_v = st.text_input("🔎 Rechercher un volontaire :", key="recherche_vol").strip().lower()
            with f2:
                filtre_statut = st.multiselect("Filtrer par statut :", STATUTS_POSSIBLES, key="filtre_statut_vol")

            df_aff = df_cand
            if recherche_v:
                df_aff = df_aff[df_aff["nom"].str.lower().str.contains(recherche_v, na=False, regex=False)]
            if filtre_statut:
                df_aff = df_aff[df_aff["statut_filiere"].isin(filtre_statut)]

            st.dataframe(df_aff, use_container_width=True)

            # Export des candidatures en CSV
            csv_data = df_cand.to_csv(index=False, encoding="utf-8").encode("utf-8")
            st.download_button(
                label="📥 Télécharger la liste des volontaires (CSV)",
                data=csv_data,
                file_name="volontaires_recrutement.csv",
                mime="text/csv",
            )

            st.markdown("---")
            st.markdown("### 🚫 Retirer un volontaire du recrutement")
            noms_volontaires = [c["nom"] for c in st.session_state.candidats]
            vol_a_retirer = st.selectbox("Sélectionner le volontaire à exclure/retirer :", noms_volontaires)

            if st.button("🚨 Confirmer le retrait du volontaire", key="btn_suppr_volontaire"):
                st.session_state.candidats = [c for c in st.session_state.candidats if c["nom"] != vol_a_retirer]
                sauvegarder_candidats(st.session_state.candidats)

                # Nettoyage sécurisé du volontaire dans les plannings
                retirer_volontaire_du_planning(vol_a_retirer)

                st.success(f"Le volontaire **{vol_a_retirer}** a été retiré.")
                st.rerun()
        else:
            st.info("Aucun volontaire inscrit pour le moment.")

    # 4. DEMANDES DE FEU VERT
    with tab4:
        st.markdown("### 🚦 Validation des Demandes de Feu Vert")
        if not st.session_state.desistements:
            st.info("Aucune demande de retrait en attente.")
        else:
            st.caption(f"{len(st.session_state.desistements)} demande(s) en attente")
            for idx, d in enumerate(st.session_state.desistements):
                with st.expander(f"Demande : {d.get('nom')} ({d.get('date_demande')})"):
                    st.write(f"**Email :** {d.get('email')}")
                    st.write(f"**Motif :** {d.get('raison')}")

                    c_acc, c_ref = st.columns(2)
                    if c_acc.button("🟢 Accorder Feu Vert", key=f"acc_fv_{idx}"):
                        nom_des = d.get("nom", "").strip().lower()
                        st.session_state.candidats = [
                            c for c in st.session_state.candidats if c["nom"].strip().lower() != nom_des
                        ]
                        sauvegarder_candidats(st.session_state.candidats)
                        # Le volontaire est aussi retiré des équipes déjà constituées
                        retirer_volontaire_du_planning(d.get("nom", ""))
                        st.session_state.desistements.pop(idx)
                        sauvegarder_desistements(st.session_state.desistements)
                        st.success("Feu vert accordé.")
                        st.rerun()

                    if c_ref.button("🔴 Refuser la demande", key=f"ref_fv_{idx}"):
                        st.session_state.desistements.pop(idx)
                        sauvegarder_desistements(st.session_state.desistements)
                        st.warning("Demande rejetée.")
                        st.rerun()

    # 5. GESTION DES LIEUX
    with tab5:
        c_e, c_s = st.columns(2)
        with c_e:
            st.markdown("#### 🏫 Ajouter / Retirer des Écoles")
            with st.form("form_add_ecole", clear_on_submit=True):
                ne = st.text_input("Nouvelle école :").strip()
                if st.form_submit_button("Ajouter École") and ne:
                    if ne.lower() in [x.lower() for x in st.session_state.ecoles_cibles]:
                        st.warning(f"L'école '{ne}' existe déjà.")
                    else:
                        st.session_state.ecoles_cibles.append(ne)
                        sauvegarder_csv_liste(FICHIER_ECOLES, st.session_state.ecoles_cibles)
                        st.success(f"École '{ne}' ajoutée !")
                        st.rerun()

            if st.session_state.ecoles_cibles:
                es = st.selectbox("Supprimer une école :", st.session_state.ecoles_cibles, key="select_del_ecole")
                if st.button("Supprimer École", key="btn_del_ecole"):
                    st.session_state.ecoles_cibles.remove(es)
                    sauvegarder_csv_liste(FICHIER_ECOLES, st.session_state.ecoles_cibles)
                    st.success("École supprimée.")
                    st.rerun()

        with c_s:
            st.markdown("#### ⛺ Ajouter / Retirer des Stands")
            with st.form("form_add_stand", clear_on_submit=True):
                ns = st.text_input("Nouveau stand :").strip()
                if st.form_submit_button("Ajouter Stand") and ns:
                    if ns.lower() in [x.lower() for x in st.session_state.stands_cibles]:
                        st.warning(f"Le stand '{ns}' existe déjà.")
                    else:
                        st.session_state.stands_cibles.append(ns)
                        sauvegarder_csv_liste(FICHIER_STANDS, st.session_state.stands_cibles)
                        st.success(f"Stand '{ns}' ajouté !")
                        st.rerun()

            if st.session_state.stands_cibles:
                ss = st.selectbox("Supprimer un stand :", st.session_state.stands_cibles, key="select_del_stand")
                if st.button("Supprimer Stand", key="btn_del_stand"):
                    st.session_state.stands_cibles.remove(ss)
                    sauvegarder_csv_liste(FICHIER_STANDS, st.session_state.stands_cibles)
                    st.success("Stand supprimé.")
                    st.rerun()

    # 6. STOCKAGE & SAUVEGARDE
    with tab6:
        st.markdown("### 💾 Stockage des données")
        if stockage_persistant_actif():
            st.success(
                "✅ Stockage persistant actif (base PostgreSQL) : les données survivent aux redémarrages "
                "et aux redéploiements."
            )
            if st.button("🔌 Tester la connexion à la base", key="btn_test_db"):
                try:
                    debut = time.time()
                    _executer_db("SELECT 1", lecture=True)
                    st.success(f"Connexion OK ({(time.time() - debut) * 1000:.0f} ms).")
                except Exception as e:
                    st.error(f"Échec de la connexion : {type(e).__name__}")
        else:
            st.warning(
                "⚠️ Stockage local (fichiers CSV) : les données peuvent disparaître au redémarrage de "
                "l'hébergement. Pour les rendre permanentes, ajoutez l'adresse de votre base PostgreSQL "
                "dans les secrets de l'application :"
            )
            st.code('DATABASE_URL = "postgresql://utilisateur:motdepasse@hote/base?sslmode=require"', language="toml")
            st.caption(
                "Les CSV déjà présents sont copiés automatiquement dans la base au premier lancement. "
                "Pensez aussi à ajouter `psycopg2-binary` à `requirements.txt`."
            )

        st.markdown("---")
        st.markdown("### 📦 Sauvegarde complète")
        st.caption("Volontaires, planning, écoles, stands et demandes de feu vert dans une seule archive ZIP.")
        st.download_button(
            "📥 Télécharger une sauvegarde complète (ZIP)",
            data=construire_sauvegarde_zip(),
            file_name=f"sauvegarde_recrutement_{datetime.date.today().isoformat()}.zip",
            mime="application/zip",
        )

        st.markdown("#### ♻️ Restaurer une sauvegarde")
        fichier_zip = st.file_uploader("Archive de sauvegarde (.zip) :", type=["zip"], key="upload_restore")
        confirmer_restore = st.checkbox(
            "Je comprends que la restauration remplace les données actuelles.", key="chk_restore"
        )
        if st.button("♻️ Restaurer cette sauvegarde", key="btn_restore"):
            if not fichier_zip:
                st.error("⚠️ Veuillez d'abord choisir une archive ZIP.")
            elif not confirmer_restore:
                st.error("⚠️ Cochez la case de confirmation pour continuer.")
            else:
                try:
                    restaures = restaurer_sauvegarde_zip(fichier_zip.getvalue())
                    if restaures:
                        st.success(f"✅ {len(restaures)} fichier(s) restauré(s).")
                        st.rerun()
                    else:
                        st.error("⚠️ Cette archive ne contient aucun fichier de données reconnu.")
                except zipfile.BadZipFile:
                    st.error("⚠️ Archive invalide.")

# --- ACCÈS ADMIN REFUSÉ ---
elif st.session_state.page_active == "Admin":
    st.error("🚫 Accès réservé aux administrateurs.")
    st.session_state.page_active = "Accueil"

# Pied de page
st.markdown("---")
st.caption("© UCAC-ICAM — Plateforme de Recrutement")
