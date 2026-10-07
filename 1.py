import os
import csv
import base64
import streamlit as st

# ==========================================
# 1. CONFIGURATION ET CONSTANTES
# ==========================================
st.set_page_config(
    page_title="Portail Recrutement UCAC-ICAM",
    page_icon="🎓",
    layout="wide"
)

ADMIN_EMAILS = [
    "admin@ucac-icam.com",
    "responsable.recrutement@ucac-icam.com"
]

FICHIER_ECOLES = "ecoles.csv"
FICHIER_STANDS = "stands.csv"
FICHIER_CANDIDATS = "candidats.csv"
FICHIER_PLANNING = "planning.csv"
FICHIER_DESISTEMENTS = "desistements.csv"

# ==========================================
# 2. FONCTIONS UTILITAIRES ET PERSISTANCE
# ==========================================
def charger_csv_liste(fichier):
    items = []
    if os.path.exists(fichier):
        with open(fichier, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    items.append(row[0])
    return sorted(list(set(items)))

def sauvegarder_csv_liste(fichier, liste_items):
    with open(fichier, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for item in sorted(liste_items):
            writer.writerow([item])

def charger_candidats():
    candidats = []
    if os.path.exists(FICHIER_CANDIDATS):
        with open(FICHIER_CANDIDATS, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidats.append(row)
    return candidats

def sauvegarder_candidats(candidats):
    champ_noms = ["nom", "prenom", "email", "statut", "lycee", "quartier", "role", "disponibilites"]
    with open(FICHIER_CANDIDATS, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=champ_noms)
        writer.writeheader()
        writer.writerows(candidats)

def charger_planning():
    planning = []
    if os.path.exists(FICHIER_PLANNING):
        with open(FICHIER_PLANNING, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                planning.append(row)
    return planning

def sauvegarder_planning(planning):
    champ_noms = ["id", "date", "heure_debut", "heure_fin", "type", "lieu", "quartier", "arrondissement", "groupe"]
    with open(FICHIER_PLANNING, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=champ_noms)
        writer.writeheader()
        writer.writerows(planning)

def charger_desistements():
    desistements = []
    if os.path.exists(FICHIER_DESISTEMENTS):
        with open(FICHIER_DESISTEMENTS, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                desistements.append(row)
    return desistements

def sauvegarder_desistements(desistements):
    champ_noms = ["email", "motif", "statut"]
    with open(FICHIER_DESISTEMENTS, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=champ_noms)
        writer.writeheader()
        writer.writerows(desistements)

def obtenir_bg_base64():
    for ext in ["jpg", "jpeg", "png"]:
        nom_fichier = f"welcome.{ext}"
        if os.path.exists(nom_fichier):
            with open(nom_fichier, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            return f"data:image/{ext};base64,{encoded}"
    return None

# ==========================================
# 3. INITIALISATION ET APPARENCE
# ==========================================
bg_image = obtenir_bg_base64()
if bg_image:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{bg_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

# ==========================================
# 4. EN-TÊTE ET CONNEXION
# ==========================================
st.title("🎓 Portail Recrutement UCAC-ICAM")

with st.sidebar:
    st.header("Connexion")
    email_input = st.text_input("Adresse E-mail", value=st.session_state["user_email"])
    if st.button("Se connecter / Valider"):
        st.session_state["user_email"] = email_input.strip()
        st.session_state["is_admin"] = email_input.strip().lower() in [e.lower() for e in ADMIN_EMAILS]
        st.success(f"Connecté : {st.session_state['user_email']}")

    if st.session_state["is_admin"]:
        st.info("⚡ Mode Administrateur Activé")

# ==========================================
# 5. NAVIGATION PRINCIPALE
# ==========================================
onglets = ["Planning Descentes", "Inscription Volontaire", "Écoles", "Stands"]
if st.session_state["is_admin"]:
    onglets.append("Administration ⚙️")

choix_onglet = st.tabs(onglets)

# ------------------------------------------
# ONGLET 1 : PLANNING
# ------------------------------------------
with choix_onglet[0]:
    st.subheader("📅 Planning des Descentes")
    planning = charger_planning()
    if planning:
        st.dataframe(planning, use_container_width=True)
    else:
        st.info("Aucun créneau planifié pour le moment.")

# ------------------------------------------
# ONGLET 2 : INSCRIPTION VOLONTAIRE
# ------------------------------------------
with choix_onglet[1]:
    st.subheader("📝 Formulaire d'Inscription Volontaire")
    
    with st.form("form_inscription"):
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("E-mail", value=st.session_state["user_email"])
        statut = st.selectbox("Statut / Filière", ["Étudiant L1", "Étudiant L2", "Étudiant L3", "Master", "Alumni", "Staff"])
        lycee = st.text_input("Ancien Lycée")
        quartier = st.text_input("Quartier de résidence")
        role = st.selectbox("Rôle souhaité", ["Animateur Stand", "Accompagnateur", "Logistique", "Autre"])
        dispos = st.text_area("Disponibilités (jours/heures)")
        
        soumis = st.form_submit_button("S'inscrire")
        if soumis:
            if not nom or not email:
                st.error("Veuillez remplir au moins le nom et l'e-mail.")
            else:
                candidats = charger_candidats()
                candidats.append({
                    "nom": nom, "prenom": prenom, "email": email,
                    "statut": statut, "lycee": lycee, "quartier": quartier,
                    "role": role, "disponibilites": dispos
                })
                sauvegarder_candidats(candidats)
                st.success("Inscription enregistrée avec succès !")

    st.hr()
    st.subheader("🚨 Demande de Feu Vert / Absence")
    with st.form("form_desistement"):
        motif = st.text_area("Motif de la demande d'absence")
        soumis_desistement = st.form_submit_button("Envoyer la demande")
        if soumis_desistement:
            if not st.session_state["user_email"]:
                st.error("Veuillez renseigner votre e-mail dans la barre latérale.")
            else:
                desistements = charger_desistements()
                desistements.append({
                    "email": st.session_state["user_email"],
                    "motif": motif,
                    "statut": "En attente"
                })
                sauvegarder_desistements(desistements)
                st.success("Demande transmise à l'administration.")

# ------------------------------------------
# ONGLET 3 : ÉCOLES
# ------------------------------------------
with choix_onglet[2]:
    st.subheader("🏫 Liste des Écoles Cibles")
    ecoles = charger_csv_liste(FICHIER_ECOLES)
    if ecoles:
        for e in ecoles:
            st.write(f"- {e}")
    else:
        st.write("Aucune école répertoriée.")

# ------------------------------------------
# ONGLET 4 : STANDS
# ------------------------------------------
with choix_onglet[3]:
    st.subheader("🎪 Liste des Stands")
    stands = charger_csv_liste(FICHIER_STANDS)
    if stands:
        for s in stands:
            st.write(f"- {s}")
    else:
        st.write("Aucun stand répertorié.")

# ------------------------------------------
# ONGLET 5 : ADMINISTRATION (ADMIN ONLY)
# ------------------------------------------
if st.session_state["is_admin"]:
    with choix_onglet[4]:
        st.subheader("⚙️ Panneau d'Administration")
        
        tab_admin1, tab_admin2, tab_admin3, tab_admin4 = st.tabs([
            "Planification", "Volontaires", "Demandes Feu Vert", "Lieux (Écoles/Stands)"
        ])
        
        # --- Gestion des créneaux ---
        with tab_admin1:
            st.write("### Ajouter un nouveau créneau (Max 5 pers.)")
            with st.form("form_creneau"):
                c_date = st.date_input("Date")
                c_h_debut = st.time_input("Heure Début")
                c_h_fin = st.time_input("Heure Fin")
                c_type = st.selectbox("Type", ["Descente École", "Stand Forum", "Autre"])
                c_lieu = st.text_input("Lieu")
                c_quartier = st.text_input("Quartier")
                c_arrondissement = st.text_input("Arrondissement")
                c_groupe = st.text_area("Membres du groupe (séparés par des virgules)")
                
                if st.form_submit_button("Créer le créneau"):
                    membres = [m.strip() for m in c_groupe.split(",") if m.strip()]
                    if len(membres) > 5:
                        st.error("Erreur : Le groupe ne peut pas dépasser 5 personnes maximum.")
                    else:
                        planning = charger_planning()
                        nouvel_id = str(len(planning) + 1)
                        planning.append({
                            "id": nouvel_id, "date": str(c_date),
                            "heure_debut": str(c_h_debut), "heure_fin": str(c_h_fin),
                            "type": c_type, "lieu": c_lieu, "quartier": c_quartier,
                            "arrondissement": c_arrondissement, "groupe": ", ".join(membres)
                        })
                        sauvegarder_planning(planning)
                        st.success("Créneau ajouté avec succès !")

        # --- Gestion des volontaires ---
        with tab_admin2:
            st.write("### Candidats Inscrits")
            candidats = charger_candidats()
            if candidats:
                st.dataframe(candidats)
                email_suppr = st.selectbox("Retirer un candidat (par e-mail)", [c["email"] for c in candidats])
                if st.button("Retirer Candidat"):
                    candidats = [c for c in candidats if c["email"] != email_suppr]
                    sauvegarder_candidats(candidats)
                    st.success(f"Candidat {email_suppr} retiré.")
                    st.rerun()

        # --- Gestion des feu vert / absences ---
        with tab_admin3:
            st.write("### Traitement des demandes d'absence")
            desistements = charger_desistements()
            if desistements:
                st.dataframe(desistements)
            else:
                st.info("Aucune demande en attente.")

        # --- Gestion des Écoles & Stands ---
        with tab_admin4:
            st.write("### Ajouter / Supprimer Écoles et Stands")
            col_e, col_s = st.columns(2)
            
            with col_e:
                nouvelle_ecole = st.text_input("Nom de l'école à ajouter")
                if st.button("Ajouter École"):
                    if nouvelle_ecole:
                        ecoles = charger_csv_liste(FICHIER_ECOLES)
                        ecoles.append(nouvelle_ecole)
                        sauvegarder_csv_liste(FICHIER_ECOLES, ecoles)
                        st.success("École ajoutée !")
                        st.rerun()
            
            with col_s:
                nouveau_stand = st.text_input("Nom du stand à ajouter")
                if st.button("Ajouter Stand"):
                    if nouveau_stand:
                        stands = charger_csv_liste(FICHIER_STANDS)
                        stands.append(nouveau_stand)
                        sauvegarder_csv_liste(FICHIER_STANDS, stands)
                        st.success("Stand ajouté !")
                        st.rerun()
