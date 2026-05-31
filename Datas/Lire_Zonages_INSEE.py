"""
Lire_Zonages_INSEE.py
---------------------
Chargement optionnel des trois fichiers de zonage INSEE complémentaires :
  - Unités urbaines (UU2020)  → table commune→zonage  (clé : CODGEO)
  - Bassins de vie (BV2022)   → table de référence     (clé : BV2022)
  - Aires d'attraction (AA2020) → table de référence   (clé : AA2020)

Correspondance des champs (source : documentation INSEE) :
  BPE (DEPCOM) ↔ UU2020 (CODGEO)   jointure commune
  BPE (BV2022) ↔ BV2022 (BV2022)   jointure bassin de vie
  BPE (AA2020) ↔ AA2020 (AA2020)   jointure aire d'attraction

Ces fichiers sont facultatifs. L'application fonctionne sans eux.

Utilisation dans app.py (sidebar) :
    from Datas.Lire_Zonages_INSEE import afficher_import_zonages

Accès aux données :
    df_uu  = st.session_state.get("df_uu")
    df_bv  = st.session_state.get("df_bv")
    df_aav = st.session_state.get("df_aav")
"""

import streamlit as st
import pandas as pd
from io import StringIO

# ---------------------------------------------------------------------------
# Configuration des trois zonages
# ---------------------------------------------------------------------------
# "type" : "commune"  → une ligne par commune, contient CODGEO
#           "referentiel" → une ligne par zonage, pas de CODGEO

ZONAGES = {
    "uu": {
        "label":       "Unités urbaines",
        "emoji":       "🏙️",
        "session_key": "df_uu",
        "type":        "commune",      # table commune → zonage
        "col_code":    "CODGEO",       # code commune INSEE
        "col_zonage":  "UU2020",       # code unité urbaine
        "col_libelle": "LIBUU2020",        # libellé unité urbaine
        "encoding":    "utf-8",
        "sep":         ";",
        "help": (
            "Fichier INSEE des unités urbaines 2020 (une ligne par commune).\n"
            "Téléchargeable sur : https://www.insee.fr/fr/information/4803954"
        ),
    },
    "bv": {
        "label":       "Bassins de vie",
        "emoji":       "🌿",
        "session_key": "df_bv",
        "type":        "referentiel",  # table de référence des bassins
        "col_code":    "BV2022",       # code bassin de vie (clé)
        "col_zonage":  "BV2022",
        "col_libelle": "LIBBV2022",    # libellé bassin de vie
        "encoding":    "utf-8",
        "sep":         ";",
        "help": (
            "Fichier INSEE des bassins de vie 2022 (une ligne par bassin).\n"
            "Colonnes attendues : BV2022, LIBBV2022, TYPE_BV2022, NB_COM\n"
            "Téléchargeable sur : https://www.insee.fr/fr/information/6676988"
        ),
    },
    "aav": {
        "label":       "Aires d'attraction des villes",
        "emoji":       "🔵",
        "session_key": "df_aav",
        "type":        "referentiel",  # table de référence des aires
        "col_code":    "AAV2020",      # code aire d'attraction (clé)
        "col_zonage":  "AAV2020",
        "col_libelle": "AAV2020",      # pas de libellé séparé connu — à affiner
        "encoding":    "utf-8",
        "sep":         ";",
        "help": (
            "Fichier INSEE des aires d'attraction des villes 2020 (une ligne par aire).\n"
            "Colonne attendue : AA2020\n"
            "Téléchargeable sur : https://www.insee.fr/fr/information/4803954"
        ),
    },
}

# ---------------------------------------------------------------------------
# Chargement d'un fichier zonage
# ---------------------------------------------------------------------------

def _charger_zonage(uploaded_file, cfg: dict) -> pd.DataFrame | None:
    """
    Charge et valide un fichier CSV de zonage INSEE.
    Pour les tables "commune" : vérifie la présence de col_code (CODGEO).
    Pour les tables "referentiel" : vérifie la présence de col_zonage.
    Retourne le DataFrame ou None en cas d'erreur.
    """
    try:
        contenu = uploaded_file.read().decode(cfg["encoding"], errors="replace")
        df = pd.read_csv(StringIO(contenu), sep=cfg["sep"], dtype=str)
        df.columns = df.columns.str.strip().str.upper()

        # Colonne à vérifier selon le type de fichier
        col_cible = cfg["col_code"] if cfg["type"] == "commune" else cfg["col_zonage"]

        if col_cible not in df.columns:
            st.error(
                f"❌ Colonne '{col_cible}' introuvable dans le fichier.\n"
                f"Colonnes détectées : {', '.join(df.columns.tolist())}"
            )
            return None

        # Pour les tables commune : normaliser CODGEO sur 5 caractères
        if cfg["type"] == "commune":
            df[cfg["col_code"]] = df[cfg["col_code"]].str.strip().str.zfill(5)

        return df

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {e}")
        return None


# ---------------------------------------------------------------------------
# Widget de chargement — à appeler dans la sidebar
# ---------------------------------------------------------------------------

def afficher_import_zonages() -> None:
    """
    Affiche un expander dans la sidebar pour charger les trois fichiers
    de zonage INSEE. Stocke les DataFrames dans st.session_state.
    """
    with st.expander("🗂️ Zonages INSEE optionnels", expanded=False):

        st.caption(
            "Ces fichiers enrichissent l'analyse BPE (unité urbaine, bassin de vie, "
            "aire d'attraction des villes). Facultatifs — disponibles en open data sur "
            "[insee.fr](https://www.insee.fr)."
        )

        for key, cfg in ZONAGES.items():
            st.markdown(f"**{cfg['emoji']} {cfg['label']}**")

            if cfg["session_key"] in st.session_state:
                df_ex = st.session_state[cfg["session_key"]]
                nb = len(df_ex)
                cols = ", ".join(df_ex.columns.tolist())
                st.success(f"✅ Chargé — {nb:,} lignes".replace(",", "\u202f"))
                st.caption(f"Colonnes : {cols}")
                if st.button("🗑️ Supprimer", key=f"del_{key}"):
                    del st.session_state[cfg["session_key"]]
                    st.rerun()
            else:
                uploaded = st.file_uploader(
                    f"Fichier CSV {cfg['label']}",
                    type=["csv", "txt"],
                    key=f"upload_{key}",
                    help=cfg["help"],
                    label_visibility="collapsed",
                )
                if uploaded is not None:
                    with st.spinner(f"Chargement {cfg['label']}…"):
                        df = _charger_zonage(uploaded, cfg)
                    if df is not None:
                        st.session_state[cfg["session_key"]] = df
                        st.success(f"✅ {len(df):,} lignes chargées".replace(",", "\u202f"))
                        st.rerun()

            st.divider()


# ---------------------------------------------------------------------------
# Helpers pour les modules consommateurs
# ---------------------------------------------------------------------------

def get_zonage_commune(depcom: str) -> dict:
    """
    Retourne les informations de zonage d'une commune (DEPCOM 5 car.)
    uniquement pour les fichiers de type "commune" (ex: UU2020).
    Les fichiers référentiels (BV, AAV) nécessitent que la BPE
    contienne directement les colonnes BV2022 / AA2020.

    Retour exemple :
        {"uu": {"code": "00002", "libelle": "Unité urbaine de Paris", "label": "Unités urbaines"}}
    """
    result = {}
    depcom = str(depcom).zfill(5)
    for key, cfg in ZONAGES.items():
        if cfg["type"] != "commune":
            continue
        df = st.session_state.get(cfg["session_key"])
        if df is None:
            continue
        ligne = df[df[cfg["col_code"]] == depcom]
        if ligne.empty:
            continue
        code_zon = ligne[cfg["col_zonage"]].iloc[0] if cfg["col_zonage"] in ligne.columns else "—"
        lib_zon  = ligne[cfg["col_libelle"]].iloc[0] if cfg["col_libelle"] in ligne.columns else "—"
        result[key] = {"code": code_zon, "libelle": lib_zon, "label": cfg["label"]}
    return result


def get_infos_bassin(code_bv: str) -> dict | None:
    """
    Retourne les infos d'un bassin de vie à partir de son code BV2022.
    Retourne None si le fichier n'est pas chargé ou le code inconnu.
    """
    df = st.session_state.get("df_bv")
    if df is None:
        return None
    ligne = df[df["BV2022"] == str(code_bv)]
    if ligne.empty:
        return None
    return ligne.iloc[0].to_dict()


def get_infos_aire(code_aa: str) -> dict | None:
    """
    Retourne les infos d'une aire d'attraction à partir de son code AA2020.
    Retourne None si le fichier n'est pas chargé ou le code inconnu.
    """
    df = st.session_state.get("df_aav")
    if df is None:
        return None
    ligne = df[df["AAV2020"] == str(code_aa)]
    if ligne.empty:
        return None
    return ligne.iloc[0].to_dict()


def zonages_charges() -> list[str]:
    """Retourne la liste des clés de zonages actuellement chargés en session."""
    return [key for key, cfg in ZONAGES.items() if cfg["session_key"] in st.session_state]