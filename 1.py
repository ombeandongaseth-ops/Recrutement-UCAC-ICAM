import csv
import os
import pandas as pd
import streamlit as st

FICHIER_CANDIDATS = "candidats_recrutement_ucac_icam.csv"
FICHIER_ECOLES = "ecoles_recrutement.csv"
FICHIER_STANDS = "stands_recrutement.csv"
FICHIER_PLANNING = "planning_recrutement.csv"

# ---------------------------------------------------------
# SÉCURITÉ ADMIN : Liste des adresses e-mail autorisées
# ---------------------------------------------------------
ADMIN_EMAILS = [
    "ninon.ombeandonga@2030.ucac-icam.com",
    "gedidia.mabahou@2030.ucac-icam.com",
    "admin@ucac-icam.com",
    # Ajoutez d'autres e-mails autorisés ici si besoin
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


# ---------------------------------------------------------
# Fonctions de persistance des données (CSV)
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
# Configuration de la page Streamlit
# ---------------------------------------------------------
st.set_page_config(
    page_title="Recrutement UCAC-ICAM",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Campagne de Recrutement — UCAC-ICAM")
st.caption("Gestion des Descentes dans les Écoles & Animation des Stands")

# Initialisation des états de session
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
        "📝 Inscription Volontaire",
        "📅 Planning Général de la Semaine",
        "🏫 Écoles & ⛺ Stands Cibles",
        "🔍 Filtrer Volontaires & Lieux",
        "🔒 Espace Administration",
    ],
)

# ---------------------------------------------------------
# 1. Inscription Volontaire (Public)
# ---------------------------------------------------------
if menu == "📝 Inscription Volontaire":
    st.subheader("📝 Formulaire d'inscription d'un étudiant volontaire")

    with st.form("form_candidat", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom et Prénom complet :").strip().title()
            ecole = st.text_input("Ancien lycée / École d'origine :").strip().title()
            quartier = st.text_input("Quartier de résidence actuel :").strip().title()

        with col2:
            role_souhaite = st.selectbox(
                "Préférence de mission :",
                ["Écoles et Stands", "Descentes dans les Écoles uniquement", "Animation des Stands uniquement"],
            )
            jours_selectionnes = st.multiselect(
                "Vos jours de disponibilité pour la semaine :",
                JOURS_SEMAINE,
                default=JOURS_SEMAINE,
            )

        soumis = st.form_submit_button("Enregistrer ma participation")

        if soumis:
            if not nom or not ecole or not quartier or not jours_selectionnes:
                st.error("⚠️ Veuillez remplir tous les champs et sélectionner au moins un jour de disponibilité.")
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
# 2. Planning Général de la Semaine (Public)
# ---------------------------------------------------------
elif menu == "📅 Planning Général de la Semaine":
    st.subheader("📅 Programme des Descentes et des Stands pour la Semaine")

    if not st.session_state.planning:
        st.info("Le planning de la semaine n'a pas encore été généré par l'administration.")
    else:
        df_plan = pd.DataFrame(st.session_state.planning)
        
        jour_filtre = st.selectbox("Filtrer le programme par jour :", ["Tous les jours"] + JOURS_SEMAINE)
        if jour_filtre != "Tous les jours":
            df_plan = df_plan[df_plan["jour"] == jour_filtre]

        type_filtre = st.radio("Filtrer par type de mission :", ["Tous", "École", "Stand"], horizontal=True)
        if type_filtre != "Tous":
            df_plan = df_plan[df_plan["type_mission"] == type_filtre]

        if df_plan.empty:
            st.warning("Aucun passage prévu pour les filtres sélectionnés.")
        else:
            st.dataframe(df_plan, use_container_width=True)

# ---------------------------------------------------------
# 3. Écoles & Stands Cibles (Public)
# ---------------------------------------------------------
elif menu == "🏫 Écoles & ⛺ Stands Cibles":
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏫 Écoles à visiter")
        if not st.session_state.ecoles_cibles:
            st.info("Aucune école n'a encore été enregistrée.")
        else:
            for i, e in enumerate(st.session_state.ecoles_cibles, 1):
                st.markdown(f"**{i}. {e}**")

    with col_b:
        st.subheader("⛺ Stands stratégiques")
        if not st.session_state.stands_cibles:
            st.info("Aucun stand n'a encore été enregistré.")
        else:
            for i, s in enumerate(st.session_state.stands_cibles, 1):
                st.markdown(f"**{i}. {s}**")

# ---------------------------------------------------------
# 4. Filtrage Volontaires & Registre (Public)
# ---------------------------------------------------------
elif menu == "🔍 Filtrer Volontaires & Lieux":
    st.subheader("🔍 Consultation du registre des volontaires")

    if not st.session_state.candidats:
        st.info("Aucun étudiant volontaire inscrit pour le moment.")
    else:
        df_cand = pd.DataFrame(st.session_state.candidats)
        st.dataframe(df_cand, use_container_width=True)

# ---------------------------------------------------------
# 5. Espace Administration (Sécurisé par Adresse E-mail uniquement)
# ---------------------------------------------------------
elif menu == "🔒 Espace Administration":
    st.subheader("🔒 Zone d'Administration — Gestion du Recrutement")

    if st.session_state.admin_connecte:
        st.success(f"Connecté en tant que **{st.session_state.admin_email}**")
        if st.button("🚪 Se déconnecter"):
            st.session_state.admin_connecte = False
            st.session_state.admin_email = ""
            st.rerun()

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📅 Organiser le Planning Horaires/Groupes",
                "🏫 & ⛺ Gestion des Écoles & Stands",
                "👥 Gestion des Volontaires",
                "📥 Exporter les Données",
            ]
        )

        # TAB 1 : Création du Planning
        with tab1:
            st.write("### ➕ Planifier un créneau d'intervention")
            st.caption("Affectez des groupes de volontaires sur des écoles ou des stands à des heures précises.")

            with st.form("form_planning", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    p_jour = st.selectbox("Jour de la semaine :", JOURS_SEMAINE)
                    p_heure = st.text_input("Créneau Horaire (ex: 08h00 - 11h00) :").strip()

                with c2:
                    p_type = st.selectbox("Type d'intervention :", ["École", "Stand"])
                    lieux_dispos = (
                        st.session_state.ecoles_cibles
                        if p_type == "École"
                        else st.session_state.stands_cibles
                    )
                    p_lieu = st.selectbox("Lieu exact :", lieux_dispos if lieux_dispos else ["Aucun lieu disponible"])

                with c3:
                    noms_volontaires = [c["nom"] for c in st.session_state.candidats]
                    p_groupe = st.multiselect("Étudiants affectés à ce créneau :", noms_volontaires)

                bouton_plan = st.form_submit_button("Ajouter ce créneau au planning")

                if bouton_plan:
                    if not p_heure or not p_lieu or not p_groupe or p_lieu == "Aucun lieu disponible":
                        st.error("⚠️ Veuillez spécifier l'heure, le lieu et au moins un volontaire.")
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
                        st.success(f"✅ Passage à **{p_lieu}** planifié pour le {p_jour} ({p_heure}).")
                        st.rerun()

            st.markdown("---")
            st.write("### 📋 Planning actuel enregistré")
            if st.session_state.planning:
                df_p = pd.DataFrame(st.session_state.planning)
                st.dataframe(df_p, use_container_width=True)

                st.write("#### 🗑️ Supprimer un créneau du planning")
                index_a_supprimer = st.number_input(
                    "Indice de la ligne à supprimer (début à 0) :",
                    min_value=0,
                    max_value=len(st.session_state.planning) - 1,
                    step=1,
                )
                if st.button("Supprimer ce créneau"):
                    st.session_state.planning.pop(index_a_supprimer)
                    sauvegarder_planning(st.session_state.planning)
                    st.success("Créneau supprimé du planning.")
                    st.rerun()

        # TAB 2 : Gestion des Écoles et Stands
        with tab2:
            col_ecole, col_stand = st.columns(2)

            with col_ecole:
                st.write("### 🏫 Écoles cibles")
                nouv_ecole = st.text_input("Nouvelle école :").strip().title()
                if st.button("Ajouter l'école"):
                    if nouv_ecole and nouv_ecole not in st.session_state.ecoles_cibles:
                        st.session_state.ecoles_cibles.append(nouv_ecole)
                        sauvegarder_csv_liste(FICHIER_ECOLES, st.session_state.ecoles_cibles)
                        st.success(f"École '{nouv_ecole}' ajoutée.")
                        st.rerun()

                if st.session_state.ecoles_cibles:
                    sup_ecole = st.selectbox("Retirer une école :", st.session_state.ecoles_cibles)
                    if st.button("Supprimer l'école"):
                        st.session_state.ecoles_cibles.remove(sup_ecole)
                        sauvegarder_csv_liste(FICHIER_ECOLES, st.session_state.ecoles_cibles)
                        st.warning(f"École '{sup_ecole}' retirée.")
                        st.rerun()

            with col_stand:
                st.write("### ⛺ Stands stratégiques")
                nouv_stand = st.text_input("Nouveau stand (ex: Rond-Point Thollon) :").strip().title()
                if st.button("Ajouter le stand"):
                    if nouv_stand and nouv_stand not in st.session_state.stands_cibles:
                        st.session_state.stands_cibles.append(nouv_stand)
                        sauvegarder_csv_liste(FICHIER_STANDS, st.session_state.stands_cibles)
                        st.success(f"Stand '{nouv_stand}' ajouté.")
                        st.rerun()

                if st.session_state.stands_cibles:
                    sup_stand = st.selectbox("Retirer un stand :", st.session_state.stands_cibles)
                    if st.button("Supprimer le stand"):
                        st.session_state.stands_cibles.remove(sup_stand)
                        sauvegarder_csv_liste(FICHIER_STANDS, st.session_state.stands_cibles)
                        st.warning(f"Stand '{sup_stand}' retiré.")
                        st.rerun()

        # TAB 3 : Gestion des Volontaires
        with tab3:
            st.write("### 🗑️ Supprimer un profil d'étudiant")
            if st.session_state.candidats:
                del_nom = st.selectbox(
                    "Sélectionnez l'étudiant à retirer :",
                    [c["nom"] for c in st.session_state.candidats],
                )
                if st.button("Supprimer l'étudiant", type="primary"):
                    st.session_state.candidats = [
                        c for c in st.session_state.candidats if c["nom"] != del_nom
                    ]
                    sauvegarder_candidats(st.session_state.candidats)
                    st.warning(f"Profil de {del_nom} supprimé.")
                    st.rerun()

        # TAB 4 : Exporter
        with tab4:
            st.write("### 📥 Télécharger les données de la campagne")
            if st.session_state.candidats:
                st.download_button(
                    label="Télécharger le registre des volontaires (CSV)",
                    data=pd.DataFrame(st.session_state.candidats).to_csv(index=False, encoding="utf-8"),
                    file_name="volontaires_recrutement.csv",
                    mime="text/csv",
                )
            if st.session_state.planning:
                st.download_button(
                    label="Télécharger le planning complet de la semaine (CSV)",
                    data=pd.DataFrame(st.session_state.planning).to_csv(index=False, encoding="utf-8"),
                    file_name="planning_semaine_recrutement.csv",
                    mime="text/csv",
                )

    # Identification par e-mail uniquement
    else:
        st.info("Veuillez saisir votre adresse e-mail autorisée pour déverrouiller l'espace administrateur.")
        email_saisi = st.text_input("Adresse e-mail administrateur :").strip().lower()

        if st.button("Se connecter"):
            if not email_saisi:
                st.warning("⚠️ Veuillez entrer une adresse e-mail.")
            elif email_saisi not in [e.lower() for e in ADMIN_EMAILS]:
                st.error("❌ Cette adresse e-mail n'est pas autorisée à accéder à l'espace administration.")
            else:
                st.session_state.admin_connecte = True
                st.session_state.admin_email = email_saisi
                st.success(f"Bienvenue {email_saisi} ! Connexion réussie.")
                st.rerun()
