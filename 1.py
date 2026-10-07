import base64
import csv
import datetime
import os
import random
import time
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

# ---------------------------------------------------------
# FONCTIONS DE PERSISTANCE CSV & PRÉSENCE
# ---------------------------------------------------------
def charger_csv_liste(fichier):
    if not os.path.exists(fichier):
        return []
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f.read().splitlines() if line.strip()]
            return sorted(items, key=lambda x: x.lower())
    except Exception:
        return []

def sauvegarder_csv_liste(fichier, liste_items):
    liste_triee = sorted(liste_items, key=lambda x: x.lower())
    with open(fichier, "w", encoding="utf-8") as f:
        for item in liste_triee:
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
            return sorted(candidats, key=lambda x: x.get("nom", "").lower())
    except Exception:
        return []

def sauvegarder_candidats(candidats):
    candidats_tries = sorted(candidats, key=lambda x: x.get("nom", "").lower())
    with open(FICHIER_CANDIDATS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["nom", "statut_filiere", "ecole", "quartier", "role_souhaite", "jours_dispo"]
        )
        writer.writeheader()
        writer.writerows(candidats_tries)

def charger_planning():
    if not os.path.exists(FICHIER_PLANNING):
        return []
    try:
        with open(FICHIER_PLANNING, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            planning = []
            for row in reader:
                if "date_mission" not in row or not row["date_mission"]:
                    row["date_mission"] = row.get("jour", "Date non précisée")
                planning.append(row)
            return planning
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
            desistements = list(csv.DictReader(f))
            return sorted(desistements, key=lambda x: x.get("nom", "").lower())
    except Exception:
        return []

def sauvegarder_desistements(desistements):
    desistements_tries = sorted(desistements, key=lambda x: x.get("nom", "").lower())
    with open(FICHIER_DEMANDES_DESISTEMENT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "nom", "raison", "date_demande"])
        writer.writeheader()
        writer.writerows(desistements_tries)

def mettre_a_jour_presence(email):
    """Enregistre l'activité récente de l'utilisateur pour le suivi en temps réel."""
    maintenant = time.time()
    presences = {}
    if os.path.exists(FICHIER_PRESENCE):
        try:
            with open(FICHIER_PRESENCE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    presences[row["email"]] = float(row["last_ping"])
        except Exception:
            pass
    presences[email] = maintenant

    # Nettoyage des sessions inactives (> 5 minutes)
    presences = {e: t for e, t in presences.items() if maintenant - t < 300}

    with open(FICHIER_PRESENCE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "last_ping"])
        writer.writeheader()
        for e, t in presences.items():
            writer.writerow({"email": e, "last_ping": t})

def obtenir_utilisateurs_en_ligne():
    """Renvoie la liste des utilisateurs actifs ces 5 dernières minutes."""
    if not os.path.exists(FICHIER_PRESENCE):
        return []
    maintenant = time.time()
    en_ligne = []
    try:
        with open(FICHIER_PRESENCE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if maintenant - float(row["last_ping"]) < 300:
                    en_ligne.append(row["email"])
    except Exception:
        pass
    return sorted(en_ligne)

# ---------------------------------------------------------
# BACKGROUND & STYLE
# ---------------------------------------------------------
def Obtenir_bg_base64():
    image_path = None
    for ext in ["welcome.jpg", "welcome.jpeg", "welcome.png"]:
        if os.path.exists(ext):
            image_path = ext
            break
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
    .online-badge {{
        display: inline-block; background-color: #10B981; color: white;
        padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;
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
if "show_logout_menu" not in st.session_state:
    st.session_state.show_logout_menu = False
if "candidats" not in st.session_state:
    st.session_state.candidats = charger_candidats()
if "ecoles_cibles" not in st.session_state:
    st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES)
if "stands_cibles" not in st.session_state:
    st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS)
if "planning" not in st.session_state:
    st.session_state.planning = charger_planning()
if "desistements" not in st.session_state:
    st.session_state.desistements = charger_desistements()
if "page_active" not in st.session_state:
    st.session_state.page_active = "Accueil"
if "tirage_temp_l1" not in st.session_state:
    st.session_state.tirage_temp_l1 = []

# ---------------------------------------------------------
# CONNEXION INITIALE
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
                mettre_a_jour_presence(email_input)
                st.rerun()
    st.stop()

# Mettre à jour le statut de présence en temps réel
mettre_a_jour_presence(st.session_state.user_email)

# ---------------------------------------------------------
# EN-TÊTE ET NAVIGATION
# ---------------------------------------------------------
col_title, col_user_btn, col_gear = st.columns([5, 4, 1]) if st.session_state.is_admin else st.columns([6, 4, 1])
with col_title:
    st.title("Recrutement UCAC-ICAM")
with col_user_btn:
    if st.button(f"👤 {st.session_state.user_email}", key="btn_user_profile"):
        st.session_state.show_logout_menu = not st.session_state.show_logout_menu
        st.rerun()

if st.session_state.is_admin and col_gear.button("⚙️", key="btn_admin_gear", help="Zone d'administration"):
    st.session_state.page_active = "Admin"
    st.rerun()

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
# GESTION DES PAGES
# ---------------------------------------------------------

# --- ACCUEIL / PLANNING ---
if st.session_state.page_active == "Accueil":
    st.markdown(
        '<div class="banner-bronze"><h4>Planning Officiel des Descentes</h4><p>Retrouvez ici les équipes constituées (3 Étudiants L1/CP/BP + 2 Encadrants/Aînés) classées par date.</p></div>',
        unsafe_allow_html=True,
    )

    df_plan = pd.DataFrame(st.session_state.planning)
    if df_plan.empty:
        st.info("Aucune descente planifiée pour le moment.")
    else:
        col_date = "date_mission" if "date_mission" in df_plan.columns else "jour"
        dates_uniques = df_plan[col_date].unique()
        for d in dates_uniques:
            st.markdown(
                f'<div style="font-size:18px; font-weight:bold; margin-top:20px; color:#60A5FA;">📅 {d}</div>',
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
                        <div style="font-weight:bold; font-size:16px;">{icon} {row.get('lieu', '')}</div>
                        <div style="color:#A0A5B1; font-size:13px; margin-top:4px;">⏱️ {horaire}{quartier_info}</div>
                        <div style="color:#93C5FD; font-size:13px; margin-top:6px;">👥 <b>Équipe constituée :</b> {row.get('groupe', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --- INSCRIPTION ---
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
            nom_volontaire = st.text_input(
                "Nom et Prénom :",
                value=st.session_state.user_email.split("@")[0].replace(".", " ").title(),
            )
            raison = st.text_area("Raison du désistement :")
            if st.form_submit_button("Envoyer la demande de feu vert à l'Admin"):
                if not raison:
                    st.error("⚠️ Veuillez indiquer le motif de votre absence.")
                else:
                    st.session_state.desistements.append(
                        {
                            "email": st.session_state.user_email,
                            "nom": nom_volontaire,
                            "raison": raison,
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
        for i, e in enumerate(sorted(st.session_state.ecoles_cibles, key=lambda x: x.lower()), 1):
            st.markdown(f'<div class="event-card"><b>{i}. {e}</b></div>', unsafe_allow_html=True)

# --- STANDS ---
elif st.session_state.page_active == "Stands":
    st.subheader("⛺ Stands de sensibilisation (Triés par ordre alphabétique)")
    if not st.session_state.stands_cibles:
        st.info("Aucun stand enregistré.")
    else:
        for i, s in enumerate(sorted(st.session_state.stands_cibles, key=lambda x: x.lower()), 1):
            st.markdown(f'<div class="event-card"><b>{i}. {s}</b></div>', unsafe_allow_html=True)

# --- ADMIN ---
elif st.session_state.page_active == "Admin" and st.session_state.is_admin:
    st.subheader("⚙️ Zone d'Administration")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📅 Planification (3 Auto + 2 Manuel)",
            "🟢 Connexions en direct",
            "👥 Volontaires & Suppression",
            "🚦 Demandes Feu Vert",
            "🏫/⛺ Lieux",
        ]
    )

    # 1. PLANIFICATION (TIRAGE AUTO + SÉLECTION MANUELLE)
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

        # Filtrage des candidats selon les rôles
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

        with col_res:
            if st.session_state.tirage_temp_l1:
                st.markdown("**3 membres tirés au sort (L1 / CP / BP) :**")
                for item in st.session_state.tirage_temp_l1:
                    st.markdown(f"- **{item['nom']}** ({item.get('statut_filiere')})")
            else:
                st.warning("Aucun tirage en cours. Cliquez sur le bouton pour générer 3 candidats.")

        with st.form("form_p_hybrid"):
            date_choisie = st.date_input("Date exacte de la descente :", datetime.date.today())
            date_formatee = date_choisie.strftime("%A %d %B %Y").capitalize()

            c_h1, c_h2 = st.columns(2)
            with c_h1:
                p_h_debut = st.selectbox("Heure de début :", HEURES_DISPONIBLES, index=1)
            with c_h2:
                p_h_fin = st.selectbox("Heure de fin :", HEURES_DISPONIBLES, index=5)

            p_lieu = st.selectbox("Lieu :", lieux if lieux else ["Aucun lieu disponible"])
            c_q, c_a = st.columns(2)
            with c_q:
                p_quartier = st.text_input("Quartier :")
            with c_a:
                p_arrondissement = st.text_input("Arrondissement :")

            noms_manuels = [
                f"{c['nom']} ({c.get('statut_filiere')})" for c in sorted(candidats_manuels, key=lambda x: x["nom"].lower())
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
                elif p_lieu and p_lieu != "Aucun lieu disponible":
                    membres_auto_str = [f"{c['nom']} ({c.get('statut_filiere')})" for c in st.session_state.tirage_temp_l1]
                    groupe_final = ", ".join(membres_auto_str + p_groupe_manuel)

                    st.session_state.planning.append(
                        {
                            "date_mission": date_formatee,
                            "heure_debut": p_h_debut,
                            "heure_fin": p_h_fin,
                            "type_mission": p_type,
                            "lieu": p_lieu,
                            "quartier": p_quartier,
                            "arrondissement": p_arrondissement,
                            "groupe": groupe_final,
                        }
                    )
                    sauvegarder_planning(st.session_state.planning)
                    st.session_state.tirage_temp_l1 = []
                    st.success("✅ Créneau ajouté au planning avec le groupe au complet (5 personnes) !")
                    st.rerun()

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

    # 2. CONNEXIONS EN DIRECT / TEMPS RÉEL
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
                        <span class="online-badge">EN LIGNE</span> &nbsp;&nbsp; <b>{user}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 3. VOLONTAIRES ET SUPPRESSION
    with tab3:
        st.markdown("### Liste des Volontaires inscrits")
        st.session_state.candidats = sorted(st.session_state.candidats, key=lambda x: x.get("nom", "").lower())

        if st.session_state.candidats:
            df_cand = pd.DataFrame(st.session_state.candidats)
            st.dataframe(df_cand, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🚫 Retirer un volontaire du recrutement")
            noms_volontaires = [c["nom"] for c in st.session_state.candidats]
            vol_a_retirer = st.selectbox("Sélectionner le volontaire à exclure/retirer :", noms_volontaires)

            if st.button("🚨 Confirmer le retrait du volontaire", key="btn_suppr_volontaire"):
                st.session_state.candidats = [c for c in st.session_state.candidats if c["nom"] != vol_a_retirer]
                sauvegarder_candidats(st.session_state.candidats)

                for p in st.session_state.planning:
                    if "groupe" in p and p["groupe"]:
                        membres = [m.strip() for m in p["groupe"].split(",")]
                        membres_filtres = [m for m in membres if not m.startswith(vol_a_retirer)]
                        p["groupe"] = ", ".join(membres_filtres)
                sauvegarder_planning(st.session_state.planning)

                st.success(f"Le volontaire **{vol_a_retirer}** a été retiré.")
                st.rerun()

    # 4. DEMANDES DE FEU VERT
    with tab4:
        st.markdown("### GL Validation des Demandes de Feu Vert")
        if not st.session_state.desistements:
            st.info("Aucune demande de retrait en attente.")
        else:
            for idx, d in enumerate(st.session_state.desistements):
                with st.expander(f"Demande : {d.get('nom')} ({d.get('date_demande')})"):
                    st.write(f"**Email :** {d.get('email')}")
                    st.write(f"**Motif :** {d.get('raison')}")

                    c_acc, c_ref = st.columns(2)
                    if c_acc.button(f"🟢 Accorder Feu Vert", key=f"acc_fv_{idx}"):
                        nom_des = d.get("nom", "").lower()
                        st.session_state.candidats = [
                            c for c in st.session_state.candidats if c["nom"].lower() not in nom_des
                        ]
                        sauvegarder_candidats(st.session_state.candidats)
                        st.session_state.desistements.pop(idx)
                        sauvegarder_desistements(st.session_state.desistements)
                        st.success("Feu vert accordé.")
                        st.rerun()

                    if c_ref.button(f"🔴 Refuser la demande", key=f"ref_fv_{idx}"):
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
                    if ne not in st.session_state.ecoles_cibles:
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
                    if ns not in st.session_state.stands_cibles:
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

# Pied de page
st.markdown("---")
st.caption("© UCAC-ICAM — Plateforme de Recrutement")
