import streamlit as st
import pandas as pd
import json
import os

# Configuration de la page
st.set_page_config(
    page_title="Gestion Recrutement - UCAC-ICAM",
    page_icon="🎓",
    layout="wide"
)

# Noms des fichiers de données
FICHIER_CANDIDATS = "candidats.json"
FICHIER_PLANNING = "planning.json"
FICHIER_DESISTEMENTS = "desistements.json"
FICHIER_ECOLES = "ecoles.csv"
FICHIER_STANDS = "stands.csv"

# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
def charger_json(fichier, defaut):
    if os.path.exists(fichier):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return defaut
    return defaut

def sauvegarder_json(fichier, donnees):
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=4)

def charger_csv_liste(fichier, defaut):
    if os.path.exists(fichier):
        try:
            df = pd.read_csv(fichier)
            if not df.empty and df.columns[0]:
                return df.iloc[:, 0].dropna().tolist()
        except Exception:
            return defaut
    return defaut

def sauvegarder_csv_liste(fichier, liste):
    df = pd.DataFrame(liste, columns=["Nom"])
    df.to_csv(fichier, index=False, encoding="utf-8")

def sauvegarder_candidats(candidats):
    sauvegarder_json(FICHIER_CANDIDATS, candidats)

def sauvegarder_planning(planning):
    sauvegarder_json(FICHIER_PLANNING, planning)

def sauvegarder_desistements(desistements):
    sauvegarder_json(FICHIER_DESISTEMENTS, desistements)

# Initialisation du Session State
if "candidats" not in st.session_state:
    st.session_state.candidats = charger_json(FICHIER_CANDIDATS, [])

if "planning" not in st.session_state:
    st.session_state.planning = charger_json(FICHIER_PLANNING, [])

if "desistements" not in st.session_state:
    st.session_state.desistements = charger_json(FICHIER_DESISTEMENTS, [])

if "ecoles_cibles" not in st.session_state:
    ecoles_defaut = ["Lycée Savorgnan de Brazza", "Lycée Chaminade", "Complexe Scolaire Révolution", "Lycée Saint-Denis"]
    st.session_state.ecoles_cibles = charger_csv_liste(FICHIER_ECOLES, ecoles_defaut)

if "stands_cibles" not in st.session_state:
    stands_defaut = ["Stand Centre-Ville", "Stand Total / Bacongo", "Stand Ouenzé / Poto-Poto", "Stand Makelekele"]
    st.session_state.stands_cibles = charger_csv_liste(FICHIER_STANDS, stands_defaut)

# En-tête de l'application
st.title("🎓 Plateforme d'Administration du Recrutement — UCAC-ICAM")
st.markdown("Gestion des descentes terrain, plannings, volontaires et autorisations.")

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Planning & Descentes", 
    "👥 Liste des Volontaires", 
    "🚦 Demandes de Feu Vert", 
    "🏫 Écoles & Stands"
])

# 1. PLANNING ET DESCENTES
with tab1:
    st.markdown("### 📌 Organiser et Planifier une Descente Terrain")
    
    with st.form("form_planning", clear_on_submit=True):
        col_type, col_lieu, col_date = st.columns(3)
        
        with col_type:
            p_type = st.selectbox("Type de mission :", ["École", "Stand"])
        
        with col_lieu:
            if p_type == "École":
                p_lieu = st.selectbox("Sélectionner l'établissement :", st.session_state.ecoles_cibles if st.session_state.ecoles_cibles else ["Aucune école définie"])
            else:
                p_lieu = st.selectbox("Sélectionner le lieu du stand :", st.session_state.stands_cibles if st.session_state.stands_cibles else ["Aucun stand défini"])
        
        with col_date:
            p_date = st.date_input("Date prévue de la descente :")
        
        col_q, col_arr = st.columns(2)
        with col_q:
            p_quartier = st.text_input("Quartier :")
        with col_arr:
            p_arrondissement = st.text_input("Arrondissement :")
            
        st.markdown("#### Choisir l'équipe de volontaires (Max 5 personnes)")
        noms_dispos = [c.get("nom", "Inconnu") for c in st.session_state.candidats]
        p_groupe = st.multiselect("Sélectionner les volontaires :", noms_dispos, max_selections=5)
        
        btn_planifier = st.form_submit_button("➕ Valider et Sauvegarder la Descente")
        
        if btn_planifier:
            if p_lieu and p_groupe:
                nouvelle_descente = {
                    "date_mission": str(p_date),
                    "type_mission": p_type,
                    "lieu": p_lieu,
                    "quartier": p_quartier,
                    "arrondissement": p_arrondissement,
                    "groupe": ", ".join(p_groupe)
                }
                st.session_state.planning.append(nouvelle_descente)
                sauvegarder_planning(st.session_state.planning)
                st.success("🎯 Créneau ajouté au planning avec succès !")
                st.rerun()
            else:
                st.error("⚠️ Veuillez remplir tous les champs et sélectionner au moins 1 volontaire (Max 5).")

    st.markdown("---")
    st.markdown("### 🗓️ Plannings Enregistrés")
    
    if st.session_state.planning:
        df_plan = pd.DataFrame(st.session_state.planning)
        st.dataframe(df_plan, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🗑️ Supprimer une descente planifiée")
        
        opts = []
        for i, p in enumerate(st.session_state.planning):
            d_val = p.get("date_mission", p.get("jour", "Date inconnue"))
            t_val = p.get("type_mission", "Mission")
            l_val = p.get("lieu", "Lieu inconnu")
            opts.append(f"{i+1}. {d_val} | {t_val} : {l_val}")
            
        idx_del = st.selectbox(
            "Sélectionner le créneau à annuler :", 
            range(len(opts)), 
            format_func=lambda x: opts[x]
        )
        if st.button("🗑️ Annuler ce créneau"):
            st.session_state.planning.pop(idx_del)
            sauvegarder_planning(st.session_state.planning)
            st.success("Créneau supprimé du planning.")
            st.rerun()
    else:
        st.info("Aucune descente planifiée pour le moment.")

# 2. VOLONTAIRES ET SUPPRESSION
with tab2:
    st.markdown("### Liste des Volontaires (Ordre Alphabétique)")
    st.session_state.candidats = sorted(st.session_state.candidats, key=lambda x: x.get("nom", "").lower())

    if st.session_state.candidats:
        df_cand = pd.DataFrame(st.session_state.candidats)
        st.dataframe(df_cand, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🚫 Retirer un volontaire du recrutement")
        noms_volontaires = [c["nom"] for c in st.session_state.candidats if "nom" in c]
        vol_a_retirer = st.selectbox("Sélectionner le volontaire à exclure/retirer :", noms_volontaires)

        if st.button("🚨 Confirmer le retrait du volontaire", key="btn_suppr_volontaire"):
            st.session_state.candidats = [c for c in st.session_state.candidats if c.get("nom") != vol_a_retirer]
            sauvegarder_candidats(st.session_state.candidats)

            for p in st.session_state.planning:
                if "groupe" in p and p["groupe"]:
                    membres = [m.strip() for m in p["groupe"].split(",")]
                    membres_filtres = [m for m in membres if not m.startswith(vol_a_retirer)]
                    p["groupe"] = ", ".join(membres_filtres)
            sauvegarder_planning(st.session_state.planning)

            st.success(f"Le volontaire **{vol_a_retirer}** a été retiré de la base de données et des plannings.")
            st.rerun()
    else:
        st.info("Aucun volontaire inscrit pour le moment.")

# 3. DEMANDES DE FEU VERT
with tab3:
    st.markdown("### 🚦 Validation des Demandes de Feu Vert (Maladies / Problèmes)")
    st.session_state.desistements = sorted(st.session_state.desistements, key=lambda x: x.get("nom", "").lower())

    if not st.session_state.desistements:
        st.info("Aucune demande de retrait en attente.")
    else:
        for idx, d in enumerate(st.session_state.desistements):
            with st.expander(f"Demande : {d.get('nom', 'Inconnu')} ({d.get('date_demande', '')})"):
                st.write(f"**Email :** {d.get('email', '')}")
                st.write(f"**Motif :** {d.get('raison', '')}")

                c_acc, c_ref = st.columns(2)
                if c_acc.button(f"🟢 Accorder Feu Vert", key=f"acc_fv_{idx}"):
                    nom_des = d.get("nom", "").lower()
                    st.session_state.candidats = [
                        c for c in st.session_state.candidats if c.get("nom", "").lower() not in nom_des
                    ]
                    sauvegarder_candidats(st.session_state.candidats)

                    st.session_state.desistements.pop(idx)
                    sauvegarder_desistements(st.session_state.desistements)

                    st.success("Feu vert accordé. Le volontaire a été retiré.")
                    st.rerun()

                if c_ref.button(f"🔴 Refuser la demande", key=f"ref_fv_{idx}"):
                    st.session_state.desistements.pop(idx)
                    sauvegarder_desistements(st.session_state.desistements)
                    st.warning("Demande rejetée.")
                    st.rerun()

# 4. GESTION DES LIEUX
with tab4:
    st.session_state.ecoles_cibles = sorted(st.session_state.ecoles_cibles, key=lambda x: x.lower())
    st.session_state.stands_cibles = sorted(st.session_state.stands_cibles, key=lambda x: x.lower())

    c_e, c_s = st.columns(2)
    with c_e:
        st.markdown("#### 🏫 Ajouter / Retirer des Écoles")
        with st.form("form_add_ecole", clear_on_submit=True):
            ne = st.text_input("Nouvelle école :").strip()
            btn_add_e = st.form_submit_button("Ajouter École")
            if btn_add_e and ne:
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
            btn_add_s = st.form_submit_button("Ajouter Stand")
            if btn_add_s and ns:
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
