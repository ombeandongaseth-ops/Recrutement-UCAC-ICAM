import base64
import csv
import os
import datetime
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

ADMIN_EMAILS = [
    "ninon.ombeandonga@2030.ucac-icam.com",
    "gedidia.mabahou@2030.ucac-icam.com",
    "admin@ucac-icam.com",
]

STATUTS_POSSIBLES = [
    "L1",
    "L2",
    "L3",
    "Membre de l'administration",
    "Enseignant / Professeur",
    "CP (Chef de Projet / Chargé de Programme)",
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
HEURES_DISPONIBLES = [f"{h:02d}h00" for h in range(7, 19)]

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
                if "statut_filiere" not in row:
                    row["statut_filiere"] = "L1"
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
            f, fieldnames=["nom", "statut_filiere", "ecole", "quartier", "role_souhaite", "jours_dispo"]
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
            f, fieldnames=["date_mission", "heure_debut", "heure_fin", "type_mission", "lieu", "quartier", "arrondissement", "groupe"]
        )
        writer.writeheader()
        writer.writerows(planning)

def charger_desistements():
    if not os.path.exists(FICHIER_DEMANDES_DESISTEMENT):
        return []
    try:
        with open(FICHIER_DEMANDES_DESISTEMENT, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def sauvegarder_desistements(desistements):
    with open(FICHIER_DEMANDES_DESISTEMENT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "nom", "raison", "date_demande"])
        writer.writeheader()
        writer.writerows(desistements)

# ---------------------------------------------------------
# BACKGROUND & STYLE
# ---------------------------------------------------------
def Obtenir_bg_base64():
    image_path = None
    for ext in ["welcome.jpg", "welcome.jpeg", "welcome.png"]:
        if os.path.exists(ext):
            image_path = ext; break
    if image_path:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            mime = "image/jpeg" if image_path.endswith((".jpg", ".jpeg")) else "image/png"
            return f"data:{mime};base64,{encoded}"
    return None

st.set_page_config(page_title="Recrutement UCAC-ICAM", page_icon="🎓", layout="wide")

bg_data = Obtenir_bg_base64()
bg_css = f"""
.stApp {{
    background: linear-gradient(rgba(18, 20, 23, 0.70), rgba(18, 20, 23, 0.85)), url("{bg_data}");
    background-size: cover; background-position: center; background-attachment: fixed; color: #FFFFFF;
}}
""" if bg_data else ".stApp { background-color: #121417; color: #FFFFFF; }"

st.markdown(
    f"""
    <style>
    {bg_css}
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    div.stButton > button {{
        width: 100% !important; height: 52px !important; font-size: 14px !important;
        font-weight: 700 !important; border-radius: 12px !important;
        background-color: rgba(28, 32, 38, 0.85) !important; color: #FFFFFF !important;
        border: 2px solid #3A3F4D !important; backdrop-filter: blur(8px);
        transition: all 0.2s ease-in-out !important;
    }}
    div.stButton > button:hover {{
        background-color: #1B72E8 !important; color: #FFFFFF !important; border-color: #1B72E8 !important;
    }}
    .banner-bronze {{
        background-color: rgba(74, 43, 15, 0.85); border-radius: 12px; padding: 16px 20px;
        color: #FCE7D0; margin: 15px 0; border: 1px solid #6E3F15; backdrop-filter: blur(5px);
    }}
    .banner-blue {{
        background: linear-gradient(135deg, rgba(28, 84, 206, 0.85) 0%, rgba(23, 113, 235, 0.85) 100%);
        border-radius: 14px; padding: 20px; color: white; margin-bottom: 25px; backdrop-filter: blur(5px);
    }}
    .event-card {{
        background-color: rgba(28, 32, 38, 0.85); border-radius: 12px; padding: 14px 18px;
        margin-bottom: 12px; border-left: 4px solid #1B72E8; backdrop-filter: blur(5px);
    }}
    .badge-filiere {{
        background-color: #1E3A8A; color: #93C5FD; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: bold;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# INITIALISATION DES SESSIONS
# ---------------------------------------------------------
if "user_email" not in st.session_state: st.session_state.user_email = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "show_logout_menu" not in st.session_state: st.session_state.show_logout_menu = False
if "candidats" not in st.session_state: st.session_state.candidats = charger_candidats()
if "ecoles_cibles" not in st.session_state: st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES)
if "stands_cibles" not in st.session_state: st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS)
if "planning" not in st.session_state: st.session_state.planning = charger_planning()
if "desistements" not in st.session_state: st.session_state.desistements = charger_desistements()
if "page_active" not in st.session_state: st.session_state.page_active = "Accueil"

# ---------------------------------------------------------
# ÉCRAN DE CONNEXION INITIALE
# ---------------------------------------------------------
if not st.session_state.user_email:
    st.title("Recrutement UCAC-ICAM")
    st.markdown(
        """
        <div class="banner-blue" style="text-align: center; padding: 30px;">
            <h2 style="margin:0; color:white;">🎓 Portail de Recrutement UCAC-ICAM</h2>
            <p style="margin-top:10px; font-size:16px;">Connectez-vous pour vous inscrire ou consulter le planning des descentes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        email_input = st.text_input("Adresse e-mail :").strip().lower()
        if st.form_submit_button("Se connecter"):
            if not email_input or "@" not in email_input:
                st.error("⚠️ Veuillez entrer une adresse e-mail valide.")
            else:
                st.session_state.user_email = email_input
                st.session_state.is_admin = email_input in [e.lower() for e in ADMIN_EMAILS]
                st.rerun()
    st.stop()

# ---------------------------------------------------------
# EN-TÊTE ET NAVIGATION
# ---------------------------------------------------------
col_title, col_user_btn, col_gear = st.columns([5, 4, 1]) if st.session_state.is_admin else st.columns([6, 4, 1])
with col_title: st.title("Recrutement UCAC-ICAM")
with col_user_btn:
    if st.button(f"👤 {st.session_state.user_email}", key="btn_user_profile"):
        st.session_state.show_logout_menu = not st.session_state.show_logout_menu
        st.rerun()

if st.session_state.is_admin and col_gear.button("⚙️", key="btn_admin_gear", help="Zone d'administration"):
    st.session_state.page_active = "Admin"; st.rerun()

if st.session_state.show_logout_menu:
    col_empty, col_logout_sub = st.columns([6, 4])
    with col_logout_sub:
        if st.button("🚪 Déconnexion", key="btn_confirm_logout"):
            st.session_state.user_email = None
            st.session_state.is_admin = False
            st.session_state.show_logout_menu = False
            st.rerun()

nav_cols = st.columns(4)
with nav_cols[0]:
    if st.button("📝 Inscription / Profil", key="nav_inscrire"): st.session_state.page_active = "Inscription"; st.rerun()
with nav_cols[1]:
    if st.button("📅 Planning des descentes", key="nav_planning"): st.session_state.page_active = "Accueil"; st.rerun()
with nav_cols[2]:
    if st.button("🏫 Écoles de descentes", key="nav_ecoles"): st.session_state.page_active = "Ecoles"; st.rerun()
with nav_cols[3]:
    if st.button("⛺ Stands de sensibilisation", key="nav_stands"): st.session_state.page_active = "Stands"; st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# GESTION DES PAGES
# ---------------------------------------------------------

# --- PAGE ACCUEIL / PLANNING ---
if st.session_state.page_active == "Accueil":
    st.markdown('<div class="banner-bronze"><h4>Planning Officiel des Descentes</h4><p>Retrouvez ici les équipes constituées (5 personnes max) par date et heure.</p></div>', unsafe_allow_html=True)

    df_plan = pd.DataFrame(st.session_state.planning)
    if df_plan.empty:
        st.info("Aucune descente planifiée pour le moment.")
    else:
        dates_uniques = df_plan["date_mission"].unique() if "date_mission" in df_plan.columns else []
        for d in dates_uniques:
            st.markdown(f'<div style="font-size:18px; font-weight:bold; margin-top:20px; color:#60A5FA;">📅 {d}</div>', unsafe_allow_html=True)
            items_d = df_plan[df_plan["date_mission"] == d]
            for _, row in items_d.iterrows():
                icon = "🏫" if row.get("type_mission") == "École" else "⛺"
                h_deb = row.get("heure_debut", "")
                h_fin = row.get("heure_fin", "")
                horaire = f"{h_deb} - {h_fin}" if h_fin else h_deb
                quartier_info = f" | 📍 {row.get('quartier', '')} ({row.get('arrondissement', '')})" if row.get('quartier') else ""

                st.markdown(
                    f"""
                    <div class="event-card">
                        <div style="font-weight:bold; font-size:16px;">{icon} {row['lieu']}</div>
                        <div style="color:#A0A5B1; font-size:13px; margin-top:4px;">⏱️ {horaire}{quartier_info}</div>
                        <div style="color:#93C5FD; font-size:13px; margin-top:6px;">👥 <b>Équipe (5 max) :</b> {row['groupe']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --- PAGE INSCRIPTION ET GESTION INDIVIDUELLE ---
elif st.session_state.page_active == "Inscription":
    st.subheader("📝 Inscription & Gestion de ma participation")

    tab_inscr, tab_desist = st.tabs(["Formulaire d'inscription", "🏥 Demande de Retrait / Maladie"])

    with tab_inscr:
        with st.form("form_candidat", clear_on_submit=True):
            nom = st.text_input("Nom et Prénom complet :").strip().title()
            statut_filiere = st.selectbox("Filière / Niveau / Statut :", STATUTS_POSSIBLES)
            ecole = st.text_input("Ancien lycée / Établissement d'origine :").strip().title()
            quartier = st.text_input("Quartier de résidence :").strip().title()
            role_souhaite = st.selectbox("Préférence d'affectation :", ["Écoles et Stands", "Descentes Écoles uniquement", "Animation Stands uniquement"])
            jours_selectionnes = st.multiselect("Disponibilités :", JOURS_SEMAINE, default=JOURS_SEMAINE[:5])

            if st.form_submit_button("Valider mon inscription"):
                if not nom or not ecole or not quartier or not jours_selectionnes:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires.")
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
        st.write("En cas d'empêchement majeur (maladie, urgence académique/personnelle), vous pouvez demander votre retrait de la campagne. La demande sera soumise à la confirmation de l'administration.")
        
        with st.form("form_desistement"):
            nom_volontaire = st.text_input("Nom et Prénom :", value=st.session_state.user_email.split('@')[0].replace('.', ' ').title())
            raison = st.text_area("Raison du désistement / certificat :")
            if st.form_submit_button("Envoyer la demande de feu vert à l'Admin"):
                if not raison:
                    st.error("⚠️ Veuillez indiquer le motif de votre absence.")
                else:
                    st.session_state.desistements.append({
                        "email": st.session_state.user_email,
                        "nom": nom_volontaire,
                        "raison": raison,
                        "date_demande": datetime.date.today().strftime("%d/%m/%Y")
                    })
                    sauvegarder_desistements(st.session_state.desistements)
                    st.success("✅ Votre demande a été envoyée aux administrateurs. Vous serez retiré après validation.")

# --- PAGE ECOLES ---
elif st.session_state.page_active == "Ecoles":
    st.subheader("🏫 Écoles de descentes")
    if not st.session_state.ecoles_cibles:
        st.info("Aucune école enregistrée.")
    else:
        for i, e in enumerate(st.session_state.ecoles_cibles, 1):
            st.markdown(f'<div class="event-card"><b>{i}. {e}</b></div>', unsafe_allow_html=True)

# --- PAGE STANDS ---
elif st.session_state.page_active == "Stands":
    st.subheader("⛺ Stands de sensibilisation")
    if not st.session_state.stands_cibles:
        st.info("Aucun stand enregistré.")
    else:
        for i, s in enumerate(st.session_state.stands_cibles, 1):
            st.markdown(f'<div class="event-card"><b>{i}. {s}</b></div>', unsafe_allow_html=True)

# --- PAGE ADMIN ---
elif st.session_state.page_active == "Admin" and st.session_state.is_admin:
    st.subheader("⚙️ Zone d'Administration")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Planifier (Grps de 5)", "👥 Volontaires & Suppression", "🚑 Demandes Feu Vert", "🏫/⛺ Lieux"])

    # 1. PLANIFICATION PAR DATES ET GROUPS DE 5
    with tab1:
        st.markdown("### Créer un créneau de descente")
        p_type = st.radio("Type de mission :", ["École", "Stand"], horizontal=True)
        lieux = st.session_state.ecoles_cibles if p_type == "École" else st.session_state.stands_cibles

        with st.form("form_p"):
            date_choisie = st.date_input("Date exacte de la descente :", datetime.date.today())
            date_formatee = date_choisie.strftime("%A %d %B %Y").capitalize()
            
            st.info(f"📆 Date sélectionnée : **{date_formatee}**")

            c_h1, c_h2 = st.columns(2)
            with c_h1: p_h_debut = st.selectbox("Heure de début :", HEURES_DISPONIBLES, index=1)
            with c_h2: p_h_fin = st.selectbox("Heure de fin :", HEURES_DISPONIBLES, index=5)

            p_lieu = st.selectbox("Lieu :", lieux if lieux else ["Aucun lieu disponible"])
            c_q, c_a = st.columns(2)
            with c_q: p_quartier = st.text_input("Quartier :")
            with c_a: p_arrondissement = st.text_input("Arrondissement :")

            noms = [f"{c['nom']} ({c.get('statut_filiere', 'L1')})" for c in st.session_state.candidats]
            p_groupe = st.multiselect("Volontaires affectés (MAXIMUM 5) :", noms, max_selections=5)

            if st.form_submit_button("Ajouter au planning"):
                if p_lieu and p_lieu != "Aucun lieu disponible" and p_groupe:
                    st.session_state.planning.append({
                        "date_mission": date_formatee,
                        "heure_debut": p_h_debut,
                        "heure_fin": p_h_fin,
                        "type_mission": p_type,
                        "lieu": p_lieu,
                        "quartier": p_quartier,
                        "arrondissement": p_arrondissement,
                        "groupe": ", ".join(p_groupe),
                    })
                    sauvegarder_planning(st.session_state.planning)
                    st.success("✅ Créneau ajouté au planning avec succès !")
                    st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir tous les champs et sélectionner au moins 1 volontaire (Max 5).")

        st.markdown("---")
        st.markdown("### Supprimer une descente planifiée")
        if st.session_state.planning:
            opts = [f"{i+1}. {p['date_mission']} | {p['type_mission']} : {p['lieu']}" for i, p in enumerate(st.session_state.planning)]
            idx_del = st.selectbox("Sélectionner le créneau à annuler :", range(len(opts)), format_func=lambda x: opts[x])
            if st.button("🗑️ Annuler ce créneau"):
                st.session_state.planning.pop(idx_del)
                sauvegarder_planning(st.session_state.planning)
                st.success("Créneau supprimé du planning.")
                st.rerun()

    # 2. GESTION DES VOLONTAIRES & RETRAIT PAR L'ADMIN
    with tab2:
        st.markdown("### Liste Générale des Volontaires")
        if st.session_state.candidats:
            df_cand = pd.DataFrame(st.session_state.candidats)
            st.dataframe(df_cand, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🚫 Retirer un volontaire du recrutement")
            noms_volontaires = [c["nom"] for c in st.session_state.candidats]
            vol_a_retirer = st.selectbox("Sélectionner le volontaire à exclure/retirer :", noms_volontaires)
            
            if st.button("🚨 Confirmer le retrait du volontaire"):
                # Retrait de la liste candidats
                st.session_state.candidats = [c for c in st.session_state.candidats if c["nom"] != vol_a_retirer]
                sauvegarder_candidats(st.session_state.candidats)
                
                # Retrait des plannings
                for p in st.session_state.planning:
                    membres = [m.strip() for m in p["groupe"].split(",")]
