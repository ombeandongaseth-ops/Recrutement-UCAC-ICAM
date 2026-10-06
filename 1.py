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
# Persistance des données (CSV)
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
# Configuration & CSS personnalisé (Reproduction de l'interface)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Accueil — UCAC-ICAM Recrutement",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Fond principal très sombre */
    .stApp {
        background-color: #121417;
        color: #FFFFFF;
    }
    
    /* Masquer le menu Streamlit par défaut pour faire application mobile */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Carte d'action rapide */
    .quick-action-btn {
        background-color: #1B72E8;
        border-radius: 18px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: white;
        margin-bottom: 8px;
    }
    .quick-action-orange { background-color: #F06A6A; }
    .quick-action-blue { background-color: #2D68C4; }
    .quick-action-indigo { background-color: #3F51B5; }
    
    /* Notification Bronze / Marron */
    .banner-bronze {
        background-color: #4A2B0F;
        border-radius: 14px;
        padding: 14px 18px;
        color: #FCE7D0;
        margin-top: 15px;
        margin-bottom: 15px;
        border: 1px solid #6E3F15;
    }
    .banner-bronze h4 {
        margin: 0 0 4px 0;
        font-size: 15px;
        color: #FFF;
    }
    .banner-bronze p {
        margin: 0;
        font-size: 13px;
        color: #D3C2B3;
    }

    /* Bannière Bleue Royale (Style AI Companion) */
    .banner-blue {
        background: linear-gradient(135deg, #1C54CE 0%, #1771EB 100%);
        border-radius: 16px;
        padding: 18px;
        color: white;
        margin-bottom: 25px;
        position: relative;
    }
    .banner-blue p {
        font-size: 14px;
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

    /* Cartes pour le programme jour par jour */
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
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-left: 4px solid #1B72E8;
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

if "page_active" not in st.session_state:
    st.session_state.page_active = "Accueil"


# ---------------------------------------------------------
# En-tête supérieur
# ---------------------------------------------------------
col_title, col_icon = st.columns([4, 1])
with col_title:
    st.title("Accueil")
with col_icon:
    st.markdown("### 🎓 UCAC")

# ---------------------------------------------------------
# Boutons d'accès rapide (Ligne d'icônes comme sur la photo)
# ---------------------------------------------------------
btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)

with btn_col1:
    if st.button("📝\nS'inscrire"):
        st.session_state.page_active = "Inscription"
        st.rerun()

with btn_col2:
    if st.button("📅\nPlanning"):
        st.session_state.page_active = "Accueil"
        st.rerun()

with btn_col3:
    if st.button("🏫\nÉcoles"):
        st.session_state.page_active = "Ecoles"
        st.rerun()

with btn_col4:
    if st.button("⛺\nStands"):
        st.session_state.page_active = "Stands"
        st.rerun()

with btn_col5:
    if st.button("🔒\nAdmin"):
        st.session_state.page_active = "Admin"
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# AFFICHAGE DE LA PAGE SÉLECTIONNÉE
# ---------------------------------------------------------

# --- PAGE ACCUEIL / PLANNING (Style exact de la photo) ---
if st.session_state.page_active == "Accueil":

    # Banner 1 : Style Bronze
    st.markdown(
        """
        <div class="banner-bronze">
            <h4>Connecter la campagne de recrutement</h4>
            <p>Consultez la répartition des équipes pour les descentes dans les lycées et les installations des stands.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Banner 2 : Style Bleu Royal
    st.markdown(
        """
        <div class="banner-blue">
            <p><b>Campagne Officielle 2026</b><br>
            Mobilisez-vous pour représenter l'UCAC-ICAM auprès des futurs bacheliers !</p>
            <div class="btn-pill">Volontaires actifs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Agenda chronologique jour par jour
    df_plan = pd.DataFrame(st.session_state.planning)

    labels_jours = {
        "Lundi": "Lundi · Phase 1",
        "Mardi": "Mardi · Phase 1",
        "Mercredi": "Mercredi · Phase 2",
        "Jeudi": "Jeudi · Phase 2",
        "Vendredi": "Vendredi · Phase 3",
        "Samedi": "Samedi · Clôture",
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
                icon = "🏫" if row["type_mission"] == "École" else "⛺"
                st.markdown(
                    f"""
                    <div class="event-card">
                        <div style="font-weight:bold; font-size:16px;">{icon} {row['lieu']}</div>
                        <div style="color:#A0A5B1; font-size:13px; margin-top:4px;">⏱️ {row['heure']} | 👥 {row['groupe']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --- PAGE INSCRIPTION VOLONTAIRE ---
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

# --- PAGE ÉCOLES ---
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

# --- PAGE STANDS ---
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

# --- PAGE ADMIN ---
elif st.session_state.page_active == "Admin":
    st.subheader("🔒 Zone d'Administration")

    if st.session_state.admin_connecte:
        st.success(f"Connecté : {st.session_state.admin_email}")
        if st.button("Se déconnecter"):
            st.session_state.admin_connecte = False
            st.rerun()

        tab1, tab2, tab3 = st.tabs(
            ["📅 Planifier Créneau", "🏫/⛺ Écoles & Stands", "👥 Volontaires"]
        )

        with tab1:
            with st.form("form_p"):
                p_jour = st.selectbox("Jour :", JOURS_SEMAINE)
                p_heure = st.text_input("Heure (ex: 08h00 - 11h00) :")
                p_type = st.selectbox("Type :", ["École", "Stand"])
                lieux = (
                    st.session_state.ecoles_cibles
                    if p_type == "École"
                    else st.session_state.stands_cibles
                )
                p_lieu = st.selectbox(
                    "Lieu :", lieux if lieux else ["Aucun lieu"]
                )
                noms = [c["nom"] for c in st.session_state.candidats]
                p_groupe = st.multiselect("Volontaires :", noms)

                if st.form_submit_button("Ajouter au planning"):
                    if p_heure and p_lieu and p_groupe:
                        st.session_state.planning.append(
                            {
                                "jour": p_jour,
                                "heure": p_heure,
                                "type_mission": p_type,
                                "lieu": p_lieu,
                                "groupe": ", ".join(p_groupe),
                            }
                        )
                        sauvegarder_planning(st.session_state.planning)
                        st.success("Créneau ajouté !")
                        st.rerun()

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
        email = st.text_input("Adresse e-mail autorisée :").strip().lower()
        if st.button("Se connecter"):
            if email in [e.lower() for e in ADMIN_EMAILS]:
                st.session_state.admin_connecte = True
                st.session_state.admin_email = email
                st.rerun()
            else:
                st.error("❌ Adresse e-mail non autorisée.")
