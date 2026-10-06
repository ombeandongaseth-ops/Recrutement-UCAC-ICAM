import csv
import os
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONSTANTES ET FICHIERS
# ---------------------------------------------------------
FICHIER_CANDIDATS = "candidats_recrutement_ucac_icam.csv"
FICHIER_ECOLES = "ecoles_recrutement.csv"
FICHIER_STANDS = "stands_recrutement.csv"
FICHIER_PLANNING = "planning_recrutement.csv"

ADMIN_EMAILS = [
    "ninon.ombeandonga@2030.ucac-icam.com",
    "gedidia.mabahou@2030.ucac-icam.com",
    "admin@ucac-icam.com",
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
HEURES_DISPONIBLES = [f"{h:02d}h00" for h in range(8, 18)]

# ---------------------------------------------------------
# FONCTIONS DE PERSISTANCE CSV
# ---------------------------------------------------------
def charger_csv_liste(fichier):
    if not os.path.exists(fichier):
        return []
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.read().splitlines() if line.strip()]
    except Exception:
        return []

def sauvegarder_csv_liste(fichier, liste_items):
    with open(fichier, "w", encoding="utf-8") as f:
        for item in liste_items:
            f.write(f"{item}\n")

def charger_candidats():
    if not os.path.exists(FICHIER_CANDIDATS):
        return []
    try:
        with open(FICHIER_CANDIDATS, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            candidats = []
            for row in reader:
                if "role_souhaite" not in row:
                    row["role_souhaite"] = "Écoles et Stands"
                if "jours_dispo" not in row:
                    row["jours_dispo"] = "Tous les jours"
                candidats.append(row)
            return candidats
    except Exception:
        return []

def sauvegarder_candidats(candidats):
    with open(FICHIER_CANDIDATS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["nom", "ecole", "quartier", "role_souhaite", "jours_dispo"]
        )
        writer.writeheader()
        writer.writerows(candidats)

def charger_planning():
    if not os.path.exists(FICHIER_PLANNING):
        return []
    try:
        with open(FICHIER_PLANNING, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def sauvegarder_planning(planning):
    with open(FICHIER_PLANNING, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["jour", "heure_debut", "heure_fin", "type_mission", "lieu", "quartier", "arrondissement", "groupe"]
        )
        writer.writeheader()
        writer.writerows(planning)

# ---------------------------------------------------------
# CONFIGURATION & STYLE CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Recrutement UCAC-ICAM",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #121417;
        color: #FFFFFF;
    }
    
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Boutons de navigation agrandis */
    div.stButton > button {
        width: 100% !important;
        min-height: 65px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        background-color: #1C2026 !important;
        color: #FFFFFF !important;
        border: 2px solid #2D323B !important;
        margin-bottom: 10px !important;
        padding: 10px 16px !important;
    }
    div.stButton > button:hover {
        background-color: #1B72E8 !important;
        color: white !important;
        border-color: #1B72E8 !important;
    }

    /* Profil utilisateur dans le coin supérieur droit */
    .user-profile-box {
        text-align: right;
        background-color: #1C2026;
        padding: 8px 14px;
        border-radius: 8px;
        border: 1px solid #2D323B;
        font-size: 13px;
        color: #A0A5B1;
        margin-bottom: 8px;
    }

    .banner-bronze {
        background-color: #4A2B0F;
        border-radius: 12px;
        padding: 16px 20px;
        color: #FCE7D0;
        margin-top: 15px;
        margin-bottom: 15px;
        border: 1px solid #6E3F15;
    }
    .banner-bronze h4 {
        margin: 0 0 4px 0;
        font-size: 16px;
        color: #FFF;
    }
    .banner-bronze p {
        margin: 0;
        font-size: 14px;
        color: #D3C2B3;
    }

    .banner-blue {
        background: linear-gradient(135deg, #1C54CE 0%, #1771EB 100%);
        border-radius: 14px;
        padding: 20px;
        color: white;
        margin-bottom: 25px;
    }
    .banner-blue p {
        font-size: 15px;
        margin-bottom: 15px;
        line-height: 1.4;
    }
    .btn-pill {
        background-color: #0A1128;
        color: white;
        border-radius: 20px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }

    .day-header {
        font-size: 18px;
        font-weight: bold;
        color: #FFFFFF;
        margin-top: 20px;
        margin-bottom: 8px;
    }
    .empty-event {
        color: #717680;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .event-card {
        background-color: #1C2026;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-left: 4px solid #1B72E8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# INITIALISATION DES ÉTATS DE SESSION
# ---------------------------------------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "candidats" not in st.session_state:
    st.session_state.candidats = charger_candidats()

if "ecoles_cibles" not in st.session_state:
    st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES)

if "stands_cibles" not in st.session_state:
    st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS)

if "planning" not in st.session_state:
    st.session_state.planning = charger_planning()

if "page_active" not in st.session_state:
    st.session_state.page_active = "Accueil"

# ---------------------------------------------------------
# ÉCRAN DE CONNEXION INITIALE
# ---------------------------------------------------------
if not st.session_state.user_email:
    st.title("Recrutement UCAC-ICAM")

    # Détection de l'image (welcome.jpg, welcome.png, welcome.jpeg)
    image_path = None
    for ext in ["welcome.jpg", "welcome.jpeg", "welcome.png"]:
        if os.path.exists(ext):
            image_path = ext
            break

    if image_path:
        st.image(image_path, use_container_width=True)
    else:
        st.markdown(
            """
            <div class="banner-blue" style="text-align: center; padding: 30px;">
                <h2 style="margin:0; color:white;">🎓 Bienvenue sur le Portail de Recrutement</h2>
                <p style="margin-top:10px; font-size:16px;">Connectez-vous pour accéder au planning des descentes et des stands.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("🔑 Connexion")
    st.write("Veuillez saisir votre adresse e-mail pour accéder à la plateforme :")
    
    with st.form("login_form"):
        email_input = st.text_input("Adresse e-mail :").strip().lower()
        submit_login = st.form_submit_button("Se connecter")
        
        if submit_login:
            if not email_input or "@" not in email_input:
                st.error("⚠️ Veuillez entrer une adresse e-mail valide.")
            else:
                st.session_state.user_email = email_input
                if email_input in [e.lower() for e in ADMIN_EMAILS]:
                    st.session_state.is_admin = True
                else:
                    st.session_state.is_admin = False
                st.rerun()
    st.stop()

# ---------------------------------------------------------
# EN-TÊTE ET PROFIL UTILISATEUR
# ---------------------------------------------------------
col_title, col_logout = st.columns([3, 1])

with col_title:
    st.title("Recrutement UCAC-ICAM")

with col_logout:
    st.markdown(
        f"""
        <div class="user-profile-box">
            👤 <b>{st.session_state.user_email}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Déconnexion", key="btn_logout"):
        st.session_state.user_email = None
        st.session_state.is_admin = False
        st.rerun()

# ---------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------
if st.session_state.is_admin:
    nav_cols = st.columns(5)
else:
    nav_cols = st.columns(4)

with nav_cols[0]:
    if st.button("📝 S'inscrire"):
        st.session_state.page_active = "Inscription"
        st.rerun()

with nav_cols[1]:
    if st.button("📅 Planning"):
        st.session_state.page_active = "Accueil"
        st.rerun()

with nav_cols[2]:
    if st.button("🏫 Écoles"):
        st.session_state.page_active = "Ecoles"
        st.rerun()

with nav_cols[3]:
    if st.button("⛺ Stands"):
        st.session_state.page_active = "Stands"
        st.rerun()

if st.session_state.is_admin:
    with nav_cols[4]:
        if st.button("⚙️ Admin"):
            st.session_state.page_active = "Admin"
            st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# PAGES
# ---------------------------------------------------------

# --- ACCUEIL / PLANNING ---
if st.session_state.page_active == "Accueil":

    st.markdown(
        """
        <div class="banner-bronze">
            <h4>Commencer la campagne de recrutement</h4>
            <p>Consultez la répartition des équipes pour les descentes dans les lycées et les installations des stands.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="banner-blue">
            <p><b>Campagne Officielle 2027</b><br>
            Mobilisez-vous pour représenter l'UCAC-ICAM auprès des futurs bacheliers !</p>
            <div class="btn-pill">Volontaires actifs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_plan = pd.DataFrame(st.session_state.planning)

    labels_jours = {
        "Lundi": "Lundi · Phase 1",
        "Mardi": "Mardi · Phase 1",
        "Mercredi": "Mercredi · Phase 2",
        "Jeudi": "Jeudi · Phase 2",
        "Vendredi": "Vendredi · Phase 3",
    }

    for j in JOURS_SEMAINE:
        st.markdown(
            f'<div class="day-header">{labels_jours.get(j, j)}</div>',
            unsafe_allow_html=True,
        )

        if not df_plan.empty:
            items_j = df_plan[df_plan["jour"] == j]
        else:
            items_j = pd.DataFrame()

        if items_j.empty:
            st.markdown(
                '<div class="empty-event">Aucun événement</div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in items_j.iterrows():
                icon = "🏫" if row.get("type_mission") == "École" else "⛺"
                h_deb = row.get("heure_debut", row.get("heure", ""))
                h_fin = row.get("heure_fin", "")
                horaire = f"{h_deb} - {h_fin}" if h_fin else h_deb
                quartier_info = f" | 📍 {row.get('quartier', '')} ({row.get('arrondissement', '')})" if row.get('quartier') else ""

                st.markdown(
                    f"""
                    <div class="event-card">
                        <div style="font-weight:bold; font-size:16px;">{icon} {row['lieu']}</div>
                        <div style="color:#A0A5B1; font-size:13px; margin-top:4px;">⏱️ {horaire}{quartier_info} | 👥 {row['groupe']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --- INSCRIPTION ---
elif st.session_state.page_active == "Inscription":
    st.subheader("📝 Inscription d'un Volontaire")

    with st.form("form_candidat", clear_on_submit=True):
        nom = st.text_input("Nom et Prénom complet :").strip().title()
        ecole = st.text_input("Ancien lycée / École d'origine :").strip().title()
        quartier = st.text_input("Quartier de résidence :").strip().title()
        role_souhaite = st.selectbox(
            "Préférence :",
            [
                "Écoles et Stands",
                "Descentes Écoles uniquement",
                "Animation Stands uniquement",
            ],
        )
        jours_selectionnes = st.multiselect(
            "Disponibilités :", JOURS_SEMAINE, default=JOURS_SEMAINE
        )

        if st.form_submit_button("Valider mon inscription"):
            if not nom or not ecole or not quartier or not jours_selectionnes:
                st.error("⚠️ Veuillez remplir tous les champs.")
            else:
                nouveau = {
                    "nom": nom,
                    "ecole": ecole,
                    "quartier": quartier,
                    "role_souhaite": role_souhaite,
                    "jours_dispo": ", ".join(jours_selectionnes),
                }
                st.session_state.candidats.append(nouveau)
                sauvegarder_candidats(st.session_state.candidats)
                st.success(f"✅ Inscription enregistrée pour {nom} !")

# --- ÉCOLES ---
elif st.session_state.page_active == "Ecoles":
    st.subheader("🏫 Écoles cibles à visiter")
    if not st.session_state.ecoles_cibles:
        st.info("Aucune école enregistrée.")
    else:
        for i, e in enumerate(st.session_state.ecoles_cibles, 1):
            st.markdown(
                f'<div class="event-card"><b>{i}. {e}</b></div>',
                unsafe_allow_html=True,
            )

# --- STANDS ---
elif st.session_state.page_active == "Stands":
    st.subheader("⛺ Stands stratégiques")
    if not st.session_state.stands_cibles:
        st.info("Aucun stand enregistré.")
    else:
        for i, s in enumerate(st.session_state.stands_cibles, 1):
            st.markdown(
                f'<div class="event-card"><b>{i}. {s}</b></div>',
                unsafe_allow_html=True,
            )

# --- ADMIN ---
elif st.session_state.page_active == "Admin" and st.session_state.is_admin:
    st.subheader("⚙️ Zone d'Administration")

    tab1, tab2, tab3 = st.tabs(
        ["📅 Planifier Créneau", "🏫/⛺ Écoles & Stands", "👥 Volontaires"]
    )

    with tab1:
        with st.form("form_p"):
            p_jour = st.selectbox("Jour :", JOURS_SEMAINE)
            
            c_h1, c_h2 = st.columns(2)
            with c_h1:
                p_h_debut = st.selectbox("Heure de début :", HEURES_DISPONIBLES, index=0)
            with c_h2:
                p_h_fin = st.selectbox("Heure de fin :", HEURES_DISPONIBLES, index=4)

            p_type = st.selectbox("Type :", ["École", "Stand"])
            lieux = (
                st.session_state.ecoles_cibles
                if p_type == "École"
                else st.session_state.stands_cibles
            )
            p_lieu = st.selectbox(
                "Lieu :", lieux if lieux else ["Aucun lieu"]
            )
            
            c_q, c_a = st.columns(2)
            with c_q:
                p_quartier = st.text_input("Quartier :")
            with c_a:
                p_arrondissement = st.text_input("Arrondissement :")

            noms = [c["nom"] for c in st.session_state.candidats]
            p_groupe = st.multiselect("Volontaires affectés :", noms)

            if st.form_submit_button("Ajouter au planning"):
                if p_lieu and p_groupe:
                    st.session_state.planning.append(
                        {
                            "jour": p_jour,
                            "heure_debut": p_h_debut,
                            "heure_fin": p_h_fin,
                            "type_mission": p_type,
                            "lieu": p_lieu,
                            "quartier": p_quartier,
                            "arrondissement": p_arrondissement,
                            "groupe": ", ".join(p_groupe),
                        }
                    )
                    sauvegarder_planning(st.session_state.planning)
                    st.success("Créneau ajouté au planning !")
                    st.rerun()
                else:
                    st.error("⚠️ Veillez choisir un lieu et attribuer au moins un volontaire.")

    with tab2:
        ne = st.text_input("Nouvelle école :")
        if st.button("Ajouter école"):
            if ne:
                st.session_state.ecoles_cibles.append(ne)
                sauvegarder_csv_liste(
                    FICHIER_ECOLES, st.session_state.ecoles_cibles
                )
                st.rerun()

        ns = st.text_input("Nouveau stand :")
        if st.button("Ajouter stand"):
            if ns:
                st.session_state.stands_cibles.append(ns)
                sauvegarder_csv_liste(
                    FICHIER_STANDS, st.session_state.stands_cibles
                )
                st.rerun()

    with tab3:
        if st.session_state.candidats:
            st.dataframe(pd.DataFrame(st.session_state.candidats))
        else:
            st.info("Aucun volontaire inscrit pour le moment.")

# Pied de page
st.markdown("---")
st.caption("© 2027 UCAC-ICAM — Plateforme de Recrutement")
