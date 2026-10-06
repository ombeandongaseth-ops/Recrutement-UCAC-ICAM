import csv
import os
import pandas as pd
import streamlit as st

FICHIER_CANDIDATS = "candidats_recrutement_ucac_icam.csv"
FICHIER_ECOLES = "ecoles_recrutement.csv"
FICHIER_STANDS = "stands_recrutement.csv"
FICHIER_PLANNING = "planning_recrutement.csv"

# ---------------------------------------------------------
# SÉCURITÉ ADMIN : Liste des e-mails autorisés
# ---------------------------------------------------------
ADMIN_EMAILS = [
    "ninon.ombeandonga@2030.ucac-icam.com",
    "gedidia.mabahou@2030.ucac-icam.com",
    "admin@ucac-icam.com",
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


# ---------------------------------------------------------
# Persistance des données
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
            f, fieldnames=["jour", "heure", "type_mission", "lieu", "groupe"]
        )
        writer.writeheader()
        writer.writerows(planning)


# ---------------------------------------------------------
# Configuration de la page Streamlit + Injection CSS (Style Zoom)
# ---------------------------------------------------------
st.set_page_config(
    page_title="UCAC-ICAM Recrutement",
    page_icon="🎓",
    layout="wide",
)

# Injection CSS Personnalisée
st.markdown(
    """
    <style>
    /* Fond principal sombre */
    .stApp {
        background-color: #121418;
        color: #E1E3E6;
    }
    
    /* Barre latérale sombre */
    [data-testid="stSidebar"] {
        background-color: #1A1D24;
        border-right: 1px solid #2B2F3A;
    }
    
    /* Cartes d'action & conteneurs */
    .zoom-card {
        background-color: #1E222D;
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 16px;
        border: 1px solid #2B3040;
    }
    
    .zoom-banner {
        background: linear-gradient(135deg, #0E4497 0%, #176BFF 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        margin-bottom: 20px;
    }
    
    .zoom-badge-school {
        background-color: #1E3A8A;
        color: #93C5FD;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
    }
    
    .zoom-badge-stand {
        background-color: #831843;
        color: #FBCFE8;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
    }
    
    /* Style des boutons principal */
    .stButton>button {
        border-radius: 12px;
        background-color: #0E62FE;
        color: white;
        border: none;
        font-weight: 600;
        padding: 8px 16px;
    }
    
    .stButton>button:hover {
        background-color: #0042C7;
        color: white;
    }
    
    /* Titres */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialisation des états
if "candidats" not in st.session_state:
    st.session_state.candidats = charger_candidats()

if "ecoles_cibles" not in st.session_state:
    st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES)

if "stands_cibles" not in st.session_state:
    st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS)

if "planning" not in st.session_state:
    st.session_state.planning = charger_planning()

if "admin_connecte" not in st.session_state:
    st.session_state.admin_connecte = False

if "admin_email" not in st.session_state:
    st.session_state.admin_email = ""

# Navigation
menu = st.sidebar.radio(
    "Navigation",
    [
        "📅 Programme de la Semaine",
        "📝 Inscription Volontaire",
        "🏫 Écoles & ⛺ Stands",
        "🔍 Registre des Étudiants",
        "🔒 Espace Administration",
    ],
)

# ---------------------------------------------------------
# En-tête de l'application
# ---------------------------------------------------------
st.markdown(
    """
    <div class="zoom-banner">
        <h2 style="margin:0; font-size: 26px;">🎓 Campagne de Recrutement UCAC-ICAM</h2>
        <p style="margin:5px 0 0 0; opacity: 0.9;">Planification des descentes dans les lycées et animation des stands stratégiques.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 1. Programme de la Semaine (Style Fil d'actualité / Agenda)
# ---------------------------------------------------------
if menu == "📅 Programme de la Semaine":
    st.subheader("📅 Planning Hebdomadaire des Missions")

    if not st.session_state.planning:
        st.markdown(
            """
            <div class="zoom-card">
                <p style="color: #9CA3AF; margin:0;">Aucun événement planifié pour le moment.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        df_plan = pd.DataFrame(st.session_state.planning)

        jour_filtre = st.selectbox("Filtrer par jour :", ["Tous les jours"] + JOURS_SEMAINE)
        if jour_filtre != "Tous les jours":
            df_plan = df_plan[df_plan["jour"] == jour_filtre]

        jours_a_afficher = (
            JOURS_SEMAINE if jour_filtre == "Tous les jours" else [jour_filtre]
        )

        for j in jours_a_afficher:
            items_j = df_plan[df_plan["jour"] == j]
            st.markdown(f"### {j}")

            if items_j.empty:
                st.markdown(
                    "<p style='color: #6B7280; font-size:14px; margin-left:10px;'>Aucun événement prévus</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in items_j.iterrows():
                    badge_class = (
                        "zoom-badge-school"
                        if row["type_mission"] == "École"
                        else "zoom-badge-stand"
                    )
                    st.markdown(
                        f"""
                        <div class="zoom-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span class="{badge_class}">{row['type_mission'].upper()}</span>
                                <span style="color:#9CA3AF; font-size:14px;">⏱️ {row['heure']}</span>
                            </div>
                            <h4 style="margin: 4px 0 8px 0; color:#FFFFFF;">📍 {row['lieu']}</h4>
                            <p style="margin:0; color:#D1D5DB; font-size:14px;">👥 <b>Groupe affecté :</b> {row['groupe']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ---------------------------------------------------------
# 2. Inscription Volontaire
# ---------------------------------------------------------
elif menu == "📝 Inscription Volontaire":
    st.subheader("📝 Rejoinnez l'équipe des volontaires")

    with st.form("form_candidat", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom et Prénom complet :").strip().title()
            ecole = st.text_input("Ancien lycée / École d'origine :").strip().title()
            quartier = st.text_input("Quartier de résidence actuel :").strip().title()

        with col2:
            role_souhaite = st.selectbox(
                "Préférence de mission :",
                ["Écoles et Stands", "Descentes Écoles uniquement", "Animation Stands uniquement"],
            )
            jours_selectionnes = st.multiselect(
                "Jours de disponibilité :",
                JOURS_SEMAINE,
                default=JOURS_SEMAINE,
            )

        soumis = st.form_submit_button("Enregistrer ma participation")

        if soumis:
            if not nom or not ecole or not quartier or not jours_selectionnes:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires.")
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
                st.success(f"✅ Inscription réussie pour **{nom}** !")

# ---------------------------------------------------------
# 3. Écoles & Stands Cibles
# ---------------------------------------------------------
elif menu == "🏫 Écoles & ⛺ Stands":
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏫 Écoles cibles")
        if not st.session_state.ecoles_cibles:
            st.info("Aucune école enregistrée.")
        else:
            for i, e in enumerate(st.session_state.ecoles_cibles, 1):
                st.markdown(
                    f"""
                    <div class="zoom-card" style="padding:12px 18px;">
                        <b>{i}. {e}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with col_b:
        st.subheader("⛺ Stands stratégiques")
        if not st.session_state.stands_cibles:
            st.info("Aucun stand enregistré.")
        else:
            for i, s in enumerate(st.session_state.stands_cibles, 1):
                st.markdown(
                    f"""
                    <div class="zoom-card" style="padding:12px 18px;">
                        <b>{i}. {s}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------
# 4. Registre des Étudiants
# ---------------------------------------------------------
elif menu == "🔍 Registre des Étudiants":
    st.subheader("🔍 Liste des volontaires inscrits")

    if not st.session_state.candidats:
        st.info("Aucun étudiant volontaire inscrit.")
    else:
        df_cand = pd.DataFrame(st.session_state.candidats)
        st.dataframe(df_cand, use_container_width=True)

# ---------------------------------------------------------
# 5. Espace Administration
# ---------------------------------------------------------
elif menu == "🔒 Espace Administration":
    st.subheader("🔒 Console d'Administration")

    if st.session_state.admin_connecte:
        st.success(f"Connecté en tant que : **{st.session_state.admin_email}**")
        if st.button("🚪 Se déconnecter"):
            st.session_state.admin_connecte = False
            st.session_state.admin_email = ""
            st.rerun()

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📅 Ajouter au Planning",
                "🏫 & ⛺ Écoles / Stands",
                "👥 Gestion Volontaires",
                "📥 Exporter Données",
            ]
        )

        with tab1:
            st.write("### ➕ Planifier un nouveau créneau")
            with st.form("form_planning", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    p_jour = st.selectbox("Jour :", JOURS_SEMAINE)
                    p_heure = st.text_input("Créneau (ex: 08h00 - 11h00) :").strip()

                with c2:
                    p_type = st.selectbox("Type :", ["École", "Stand"])
                    lieux_dispos = (
                        st.session_state.ecoles_cibles
                        if p_type == "École"
                        else st.session_state.stands_cibles
                    )
                    p_lieu = st.selectbox(
                        "Lieu :",
                        lieux_dispos if lieux_dispos else ["Aucun lieu disponible"],
                    )

                with c3:
                    noms_volontaires = [c["nom"] for c in st.session_state.candidats]
                    p_groupe = st.multiselect("Étudiants affectés :", noms_volontaires)

                if st.form_submit_button("Ajouter la mission"):
                    if not p_heure or not p_lieu or not p_groupe or p_lieu == "Aucun lieu disponible":
                        st.error("⚠️ Veuillez renseigner tous les champs.")
                    else:
                        nouvel_element = {
                            "jour": p_jour,
                            "heure": p_heure,
                            "type_mission": p_type,
                            "lieu": p_lieu,
                            "groupe": ", ".join(p_groupe),
                        }
                        st.session_state.planning.append(nouvel_element)
                        sauvegarder_planning(st.session_state.planning)
                        st.success("Mission ajoutée !")
                        st.rerun()

            st.markdown("---")
            if st.session_state.planning:
                st.write("### 📋 Missions configurées")
                st.dataframe(pd.DataFrame(st.session_state.planning), use_container_width=True)

        with tab2:
            col_ecole, col_stand = st.columns(2)
            with col_ecole:
                st.write("### 🏫 Écoles")
                nouv_ecole = st.text_input("Nom école :").strip().title()
                if st.button("Ajouter École"):
                    if nouv_ecole and nouv_ecole not in st.session_state.ecoles_cibles:
                        st.session_state.ecoles_cibles.append(nouv_ecole)
                        sauvegarder_csv_liste(FICHIER_ECOLES, st.session_state.ecoles_cibles)
                        st.rerun()

            with col_stand:
                st.write("### ⛺ Stands")
                nouv_stand = st.text_input("Nom stand :").strip().title()
                if st.button("Ajouter Stand"):
                    if nouv_stand and nouv_stand not in st.session_state.stands_cibles:
                        st.session_state.stands_cibles.append(nouv_stand)
                        sauvegarder_csv_liste(FICHIER_STANDS, st.session_state.stands_cibles)
                        st.rerun()

        with tab3:
            st.write("### 🗑️ Supprimer un volontaire")
            if st.session_state.candidats:
                del_nom = st.selectbox(
                    "Choisir un profil :", [c["nom"] for c in st.session_state.candidats]
                )
                if st.button("Supprimer"):
                    st.session_state.candidats = [
                        c for c in st.session_state.candidats if c["nom"] != del_nom
                    ]
                    sauvegarder_candidats(st.session_state.candidats)
                    st.rerun()

        with tab4:
            st.write("### 📥 Télécharger les fichiers CSV")
            if st.session_state.candidats:
                st.download_button(
                    "Télécharger le registre",
                    pd.DataFrame(st.session_state.candidats).to_csv(index=False, encoding="utf-8"),
                    "volontaires.csv",
                    "text/csv",
                )

    else:
        st.markdown(
            """
            <div class="zoom-card">
                <h3 style="margin-top:0;">Identification Administrateur</h3>
                <p style="color:#9CA3AF;">Entrez votre adresse e-mail autorisée pour accéder aux paramètres.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        email_saisi = st.text_input("Adresse e-mail :").strip().lower()

        if st.button("Se connecter"):
            if not email_saisi:
                st.warning("⚠️ Veuillez écrire une adresse e-mail.")
            elif email_saisi not in [e.lower() for e in ADMIN_EMAILS]:
                st.error("❌ Adresse e-mail non autorisée.")
            else:
                st.session_state.admin_connecte = True
                st.session_state.admin_email = email_saisi
                st.rerun()
