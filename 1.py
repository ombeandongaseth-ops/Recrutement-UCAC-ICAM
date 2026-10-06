import csv
import os
import random
import pandas as pd
import streamlit as st

FICHIER_SAUVEGARDE = "candidats_recrutement_ucac_icam.csv"
FICHIER_ECOLES = "ecoles_recrutement.csv"
MOT_DE_PASSE_ADMIN = "ucac2026"


# ---------------------------------------------------------
# Fonctions de persistance des données
# ---------------------------------------------------------
def charger_candidats():
    if not os.path.exists(FICHIER_SAUVEGARDE):
        return []
    try:
        with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            candidats = []
            for row in reader:
                if "affectation" not in row:
                    row["affectation"] = "Non affecté(e)"
                candidats.append(row)
            return candidats
    except Exception:
        return []


def sauvegarder_candidats(candidats):
    with open(FICHIER_SAUVEGARDE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["nom", "ecole", "quartier", "affectation"]
        )
        writer.writeheader()
        writer.writerows(candidats)


def charger_ecoles_cible():
    if not os.path.exists(FICHIER_ECOLES):
        return []
    try:
        with open(FICHIER_ECOLES, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            return [line.strip() for line in lines if line.strip()]
    except Exception:
        return []


def sauvegarder_ecoles_cible(ecoles):
    with open(FICHIER_ECOLES, "w", encoding="utf-8") as f:
        for ecole in ecoles:
            f.write(f"{ecole}\n")


# ---------------------------------------------------------
# Configuration de la page Streamlit
# ---------------------------------------------------------
st.set_page_config(
    page_title="Recrutement UCAC-ICAM",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Plateforme de Recrutement — UCAC-ICAM")
st.caption("Gestion et répartition des étudiants volontaires")

if "candidats" not in st.session_state:
    st.session_state.candidats = charger_candidats()

if "ecoles_cibles" not in st.session_state:
    st.session_state.ecoles_cibles = charger_ecoles_cible()

# Navigation
menu = st.sidebar.radio(
    "Navigation",
    [
        "📝 Inscription Volontaire",
        "📋 Liste & Affectations",
        "🏫 Écoles à visiter",
        "🔍 Filtrer (Quartier / École)",
        "🔒 Espace Administration",
    ],
)

# ---------------------------------------------------------
# 1. Inscription Volontaire (Public)
# ---------------------------------------------------------
if menu == "📝 Inscription Volontaire":
    st.subheader("Inscription d'un étudiant volontaire")

    with st.form("form_candidat", clear_on_submit=True):
        nom = st.text_input("Nom et Prénom complet :").strip().title()
        ecole = st.text_input("Ancien lycée / École d'origine :").strip().title()
        quartier = st.text_input("Quartier de résidence actuel :").strip().title()

        soumis = st.form_submit_button("Enregistrer ma participation")

        if soumis:
            if not nom or not ecole or not quartier:
                st.error("⚠️ Tous les champs sont obligatoires.")
            else:
                nouveau = {
                    "nom": nom,
                    "ecole": ecole,
                    "quartier": quartier,
                    "affectation": "Non affecté(e)",
                }
                st.session_state.candidats.append(nouveau)
                sauvegarder_candidats(st.session_state.candidats)
                st.success(f"✅ Inscription réussie pour **{nom}** !")

# ---------------------------------------------------------
# 2. Liste Globale & Affectations (Public)
# ---------------------------------------------------------
elif menu == "📋 Liste & Affectations":
    st.subheader("👥 Volontaires et affectations actuelles")

    if not st.session_state.candidats:
        st.info("Aucun volontaire n'est encore inscrit.")
    else:
        df = pd.DataFrame(st.session_state.candidats)
        df = df.sort_values(by="nom").reset_index(drop=True)
        df.index += 1
        st.dataframe(
            df[["nom", "ecole", "quartier", "affectation"]],
            use_container_width=True,
        )

# ---------------------------------------------------------
# 3. Écoles à Visiter (Public - Lecture seule)
# ---------------------------------------------------------
elif menu == "🏫 Écoles à visiter":
    st.subheader("📍 Écoles cibles pour la campagne")

    if not st.session_state.ecoles_cibles:
        st.info("La liste des écoles cibles est en cours de préparation par l'administration.")
    else:
        for i, ecole in enumerate(st.session_state.ecoles_cibles, 1):
            st.markdown(f"**{i}. {ecole}**")

# ---------------------------------------------------------
# 4. Filtrage (Public)
# ---------------------------------------------------------
elif menu == "🔍 Filtrer (Quartier / École)":
    st.subheader("🔍 Recherche dans le registre")

    if not st.session_state.candidats:
        st.info("La base de données est vide.")
    else:
        df = pd.DataFrame(st.session_state.candidats)
        critere = st.radio(
            "Filtrer par :",
            ["Quartier de résidence", "École d'origine", "École d'affectation"],
            horizontal=True,
        )

        if critere == "Quartier de résidence":
            opts = sorted(list(df["quartier"].unique()))
            c = st.selectbox("Sélectionnez le quartier :", opts)
            res = df[df["quartier"] == c]
        elif critere == "École d'origine":
            opts = sorted(list(df["ecole"].unique()))
            c = st.selectbox("Sélectionnez l'école d'origine :", opts)
            res = df[df["ecole"] == c]
        else:
            opts = sorted(list(df["affectation"].unique()))
            c = st.selectbox("Sélectionnez l'affectation :", opts)
            res = df[df["affectation"] == c]

        st.dataframe(res, use_container_width=True)

# ---------------------------------------------------------
# 5. Espace Administration (Sécurisé)
# ---------------------------------------------------------
elif menu == "🔒 Espace Administration":
    st.subheader("🔒 Zone d'Administration Réservée")

    pwd = st.text_input("Entrez le mot de passe administrateur :", type="password")

    if pwd == MOT_DE_PASSE_ADMIN:
        st.success("Accès administrateur autorisé.")

        tab1, tab2, tab3 = st.tabs(
            [
                "🎲 Répartition Aléatoire / Manuel",
                "🏫 Gestion des Écoles Cibles",
                "🗑️ Supprimer / Exporter",
            ]
        )

        # TAB 1 : Répartition des volontaires
        with tab1:
            st.write("### 🎲 Répartition automatique des volontaires")
            st.caption("Attribue de manière aléatoire et équitable les volontaires aux écoles cibles enregistrées.")

            if not st.session_state.ecoles_cibles:
                st.warning("⚠️ Veuillez ajouter au moins une école cible dans l'onglet 'Gestion des Écoles Cibles'.")
            elif not st.session_state.candidats:
                st.warning("⚠️ Aucun volontaire inscrit pour le moment.")
            else:
                if st.button("⚡ Lancer la répartition aléatoire", type="primary"):
                    nb_ecoles = len(st.session_state.ecoles_cibles)
                    # Copie et mélange aléatoire
                    candidats_shuffled = st.session_state.candidats.copy()
                    random.shuffle(candidats_shuffled)

                    # Distribution équitable entre les écoles
                    for idx, c in enumerate(candidats_shuffled):
                        ecole_attribuee = st.session_state.ecoles_cibles[idx % nb_ecoles]
                        c["affectation"] = ecole_attribuee

                    st.session_state.candidats = candidats_shuffled
                    sauvegarder_candidats(st.session_state.candidats)
                    st.success("🎉 La répartition aléatoire a été effectuée avec succès !")
                    st.rerun()

            st.markdown("---")
            st.write("### ✏️ Affectation manuelle")
            if st.session_state.candidats and st.session_state.ecoles_cibles:
                noms = [c["nom"] for c in st.session_state.candidats]
                nom_sel = st.selectbox("Sélectionnez le volontaire :", noms)
                ecole_sel = st.selectbox("Attribuer l'école :", ["Non affecté(e)"] + st.session_state.ecoles_cibles)

                if st.button("Valider la modification manuelle"):
                    for c in st.session_state.candidats:
                        if c["nom"] == nom_sel:
                            c["affectation"] = ecole_sel
                            break
                    sauvegarder_candidats(st.session_state.candidats)
                    st.success(f"Affectation mise à jour pour {nom_sel}.")
                    st.rerun()

        # TAB 2 : Gestion des écoles
        with tab2:
            st.write("### 🏫 Ajouter / Supprimer des écoles à visiter")
            nouvelle = st.text_input("Nom de l'école cible :").strip().title()
            if st.button("Ajouter l'école"):
                if nouvelle and nouvelle not in st.session_state.ecoles_cibles:
                    st.session_state.ecoles_cibles.append(nouvelle)
                    sauvegarder_ecoles_cible(st.session_state.ecoles_cibles)
                    st.success(f"École '{nouvelle}' ajoutée.")
                    st.rerun()

            st.markdown("---")
            if st.session_state.ecoles_cibles:
                a_retirer = st.selectbox("Retirer une école :", st.session_state.ecoles_cibles)
                if st.button("Supprimer l'école"):
                    st.session_state.ecoles_cibles.remove(a_retirer)
                    sauvegarder_ecoles_cible(st.session_state.ecoles_cibles)
                    st.warning(f"École '{a_retirer}' retirée.")
                    st.rerun()

        # TAB 3 : Suppression & Exportation
        with tab3:
            st.write("### 🗑️ Supprimer un membre")
            if st.session_state.candidats:
                del_nom = st.selectbox("Sélectionnez le profil à supprimer :", [c["nom"] for c in st.session_state.candidats])
                if st.button("Supprimer définitivement", type="primary"):
                    st.session_state.candidats = [c for c in st.session_state.candidats if c["nom"] != del_nom]
                    sauvegarder_candidats(st.session_state.candidats)
                    st.warning(f"Profil de {del_nom} supprimé.")
                    st.rerun()

            st.markdown("---")
            st.write("### 📥 Exporter la liste")
            if st.session_state.candidats:
                df_exp = pd.DataFrame(st.session_state.candidats)
                st.download_button(
                    label="Télécharger le fichier CSV complet",
                    data=df_exp.to_csv(index=False, encoding="utf-8"),
                    file_name="recrutement_ucac_icam.csv",
                    mime="text/csv",
                )

    elif pwd:
        st.error("Mot de passe incorrect.")