"""
@author : Philippe PETIT
@version : 1.0.0
@description : Base permanente des équipements (millésime 2026)
"""
import sys, os

# Fix PyInstaller : plusieurs stratégies pour trouver _internal/
_candidates = [
    getattr(sys, '_MEIPASS', None),
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), '_internal'),
]
for _p in _candidates:
    if _p and os.path.isdir(os.path.join(_p, 'ui')) and _p not in sys.path:
        sys.path.insert(0, _p)
        break

import streamlit as st
import pandas as pd
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

from ui.cards import badge, badgeBlue, badgeGreen, badgeRed
from Datas.Lire_BPE import lire_bpe
from Datas.Lire_Datas_csv import affiche_selecteur
from Datas.affiche_selecteur_bpe_2 import affiche_selecteur_bpe, DOM, SDOM, TYPEQU
from Datas.bpe_signalement import afficher_formulaire_bpe
from Datas.Lire_Zonages_INSEE import afficher_import_zonages

import streamlit.components.v1 as components
# Lecture du fichier documentation (une seule fois au démarrage)
DOC_HTML_PATH = ROOT_DIR / "assets" / "documentation_bpe.html"
DOC_HTML = DOC_HTML_PATH.read_text(encoding="utf-8") if DOC_HTML_PATH.exists() else None

# =====================================================
# CONFIG STREAMLIT
# =====================================================
st.set_page_config(
    layout="wide",
    page_title="Tableau de bord artificialisation communale (V5.1.2)",
    page_icon="📊",
    initial_sidebar_state="expanded"
)


# =====================================================
# HELPERS
# =====================================================

def style_table_html(df: pd.DataFrame, col_num: list = None, col_cent: list = None) -> str:
    """Génère une table HTML avec style CSS personnalisé."""
    col_num  = col_num  or []
    col_cent = col_cent or []
    css = """
    <style>
        table th {
            background-color: #0489B1; text-align: center;
            color: white; text-shadow: 1px 2px 3px black;
        }
        table tr:nth-child(odd)  { background-color: #E0ECF8; }
        table tr:nth-child(even) { background-color: #FFFFFF; }
        table td.num  { text-align: right; }
        table td.cent { text-align: center; }
        table { border-collapse: collapse; width: 100%; }
        table td, table th { padding: 6px 10px; border: 1px solid #ccc; }
    </style>
    """
    thead = "<thead><tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr></thead>"
    rows  = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            if col in col_num:
                cells.append(f'<td class="num">{row[col]}</td>')
            elif col in col_cent:
                cells.append(f'<td class="cent">{row[col]}</td>')
            else:
                cells.append(f"<td>{row[col]}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return css + f"<table>{thead}{tbody}</table>"


def get_nom_epci(code_epci: str) -> str:
    """
    Interroge l'API geo.api.gouv.fr pour obtenir le nom et le type d'un EPCI.
    Résultat mis en cache dans st.session_state pour éviter les appels répétés.
    Retourne le code brut en cas d'échec (pas de message d'erreur affiché).
    """
    cache_key = f"epci_nom_{code_epci}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    try:
        r = requests.get(
            f"https://geo.api.gouv.fr/epcis/{code_epci}",
            timeout=3
        )
        if r.status_code == 200:
            data = r.json()
            nom  = data.get("nom", code_epci)
            type_epci = data.get("type", "")
            result = f"{nom} ({type_epci})" if type_epci else nom
        else:
            result = code_epci
    except Exception:
        result = code_epci

    st.session_state[cache_key] = result
    return result


def fermer_page_web():
    st.session_state["quitting"] = True


def afficher_page_sortie():
    st.markdown("""
        <div style='text-align:center; padding-top: 80px;'>
            <h1>👋 Application fermée</h1>
            <h3 style='color:orange;'>
                Merci d'avoir utilisé le <strong>DashBoard</strong>.<br><br>
                Vous pouvez maintenant <strong>fermer cet onglet</strong>.
            </h3>
        </div>
    """, unsafe_allow_html=True)
    from threading import Timer
    Timer(2, lambda: os._exit(0)).start()
    st.stop()


# =====================================================
# HEADER
# =====================================================
def afficher_header():
    col_logo, col_texte = st.columns([1, 4])
    with col_logo:
        logo_path = ROOT_DIR / "assets" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=210)
    with col_texte:
        st.markdown(
            """
            <div style='margin-top:10px;'>
                <h1 style='margin-bottom:0px;'>📊 Base permanente des équipements</h1>
                <div style='font-size:1rem; font-weight:600; color:orange; margin-top:6px;'>
                    Version 1.0.0, millésime 2026<br>
                    Auteur : Philippe PETIT |
                    <a href='mailto:philippe.petit.lafiou@outlook.fr?subject=Plateforme Publique [BPE]'>Contact</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("🚪 Quitter l'application", key="btn_quitter"):
        st.session_state["confirm_quit"] = True
        st.rerun()

    if st.session_state.get("confirm_quit", False):
        st.warning("Voulez-vous vraiment quitter l'application ?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Oui, quitter maintenant", key="btn_oui_quitter"):
                st.session_state["quitting"] = True
                st.rerun()
        with col2:
            if st.button("❌ Non, annuler", key="btn_non_quitter"):
                st.session_state["confirm_quit"] = False

    st.divider()


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    url_maps = "https://www.data.gouv.fr/api/1/datasets/r/7f85d7e7-f60d-4e0e-99af-eef3529191f0"
    st.markdown("### 📥 Données de la base permanente des équipements.")
    st.markdown(f"[🗺️ Télécharger les données depuis data.gouv.fr]({url_maps})")
    st.divider()

    st.header("📂 Import des données")
    df = lire_bpe()
    if df is not None:
        st.session_state["df"] = df

    if "df" in st.session_state:
        df = st.session_state["df"]
        with st.expander("🔍 Sélectionnez votre territoire…", expanded=True):
            df_sel = affiche_selecteur_bpe(df)
            if df_sel is not None:
                st.session_state["bpe_sel"] = df_sel
            elif "bpe_sel" in st.session_state:
                del st.session_state["bpe_sel"]
    else:
        st.info("Veuillez importer un fichier CSV dans la barre latérale.")

    afficher_import_zonages()

    # BPE Signalement
    if st.button("📋 Signaler une anomalie BPE", key="bpe_signalement"):
        st.session_state["page"] = "bpe_signalement"

    # Documentation
    if st.button("📖 Documentation", key="btn_doc"):
        st.session_state["page"] = "documentation"


# =====================================================
# MAIN
# =====================================================
if st.session_state.get("quitting"):
    afficher_page_sortie()

afficher_header()

page = st.session_state.get("page", "accueil")

if page == "bpe_signalement":
    if st.button("← Retour à la consultation"):
        st.session_state["page"] = "accueil"
        st.rerun()
    afficher_formulaire_bpe()
    st.stop()

if page == "documentation":
    if st.button("← Retour à la consultation"):
        st.session_state["page"] = "accueil"
        st.rerun()
    if DOC_HTML:
        components.html(DOC_HTML, height=900, scrolling=True)
    else:
        st.error("Fichier documentation_bpe.html introuvable dans assets/")
    st.stop()


# --- Affichage du résultat de sélection ---
if "bpe_sel" in st.session_state:
    df_sel = st.session_state["bpe_sel"]

    mode  = st.session_state.get("bpe_mode", "Commune")
    annee = df_sel["AN"].iloc[0] if "AN" in df_sel else ""

    # --- Header territoire ---
    if mode == "EPCI":
        epci     = st.session_state.get("bpe_territoire", "")
        nom_epci = get_nom_epci(str(epci))
        nb_com   = df_sel["LIBCOM"].nunique() if "LIBCOM" in df_sel else ""
        st.header(f"🏗️ {nom_epci}")
        st.caption(f"Code EPCI : {epci}")
        st.subheader(f"{nb_com} commune{'s' if nb_com > 1 else ''} — Millésime {annee}")
    else:
        depcom = df_sel["DEPCOM"].iloc[0] if "DEPCOM" in df_sel else ""
        libcom = df_sel["LIBCOM"].iloc[0] if "LIBCOM" in df_sel else ""
        st.header(f"{depcom} — {libcom}")
        st.subheader(f"Millésime — {annee}")

    st.subheader(f"📋 Résultats — {len(df_sel)} équipement{'s' if len(df_sel) > 1 else ''}")

    # --- Zonages INSEE (si fichiers chargés) ---
    uu  = st.session_state.get("df_uu")
    bv  = st.session_state.get("df_bv")
    aav = st.session_state.get("df_aav")

    if uu is not None or bv is not None or aav is not None:
        z1, z2, z3 = st.columns(3)

        if uu is not None or bv is not None or aav is not None:
            z1, z2, z3 = st.columns(3)

        # Référentiel communes du territoire (jointure commune)
        ref_com = df_sel[["DEPCOM", "LIBCOM"]].drop_duplicates()
        ref_com = ref_com.copy()
        ref_com["CODGEO"] = ref_com["DEPCOM"].astype(str).str.zfill(5)

        with z1:
            if uu is not None and "DEPCOM" in df_sel.columns:
                depcom_norm = ref_com["CODGEO"].tolist()
                lignes = uu[uu["CODGEO"].isin(depcom_norm)]
                if not lignes.empty and "LIBUU2020" in lignes.columns:
                    lignes = lignes.merge(ref_com[["CODGEO", "LIBCOM"]], on="CODGEO", how="left")
                    groupes = lignes.groupby("LIBUU2020")
                    nb_uu = groupes.ngroups
                    st.info(f"🏙️ **Unités urbaines ({nb_uu})** "
                            f"[ℹ️](https://www.insee.fr/fr/information/4802589)")
                    for libuu, grp in groupes:
                        type_uu = grp["TYPE_COMMUNE_UU"].iloc[0] \
                                  if "TYPE_COMMUNE_UU" in grp.columns else ""
                        communes = grp["LIBCOM"].dropna().sort_values().unique()
                        with st.expander(f"🏙️ {libuu}" + (f" *({type_uu})*" if type_uu else "")):
                            for com in communes:
                                st.markdown(f"- {com}")

        with z2:
            if bv is not None and "BV2022" in df_sel.columns:
                bv_codes = df_sel["BV2022"].dropna().unique()
                lignes = bv[bv["BV2022"].isin([str(c) for c in bv_codes])]
                if not lignes.empty and "LIBBV2022" in lignes.columns:
                    # Jointure pour récupérer LIBCOM par bassin de vie
                    # On passe par df_sel qui contient BV2022 + DEPCOM + LIBCOM
                    ref_bv = df_sel[["DEPCOM", "LIBCOM", "BV2022"]].drop_duplicates()
                    ref_bv["BV2022"] = ref_bv["BV2022"].astype(str)
                    lignes["BV2022"] = lignes["BV2022"].astype(str)
                    lignes = lignes.merge(ref_bv[["BV2022", "LIBCOM"]], on="BV2022", how="left")
                    groupes = lignes.groupby("LIBBV2022")
                    nb_bv = groupes.ngroups
                    st.info(f"🌿 **Bassins de vie ({nb_bv})** "
                            f"[ℹ️](https://www.insee.fr/fr/information/6676988)")
                    for libbv, grp in groupes:
                        communes = grp["LIBCOM"].dropna().sort_values().unique()
                        with st.expander(f"🌿 {libbv}"):
                            for com in communes:
                                st.markdown(f"- {com}")

        with z3:
            if aav is not None and "AAV2020" in df_sel.columns:
                aav_codes = df_sel["AAV2020"].dropna().unique()
                lignes    = aav[aav["AAV2020"].isin([str(c) for c in aav_codes])]
                if not lignes.empty:
                    col_lib = next(
                        (c for c in ["LIBAAV2020", "AAV2020"] if c in lignes.columns), None
                    )
                    if col_lib:
                        vals    = lignes[[col_lib]].drop_duplicates()
                        contenu = "\n\n".join(f"• {row[col_lib]}" for _, row in vals.iterrows())
                        st.info(f"🔵 **Aires d'attraction des villes ({len(vals)})** "
                                f"[ℹ️](https://www.insee.fr/fr/information/4803954)\n\n{contenu}")
    st.divider()
    # --- Accordéons DOM / SDOM ---
    cols_affich = [
        "AN", "DOM", "SDOM", "TYPEQU", "NOMRS", "CNOMRS", "TYPVOIE", "LIBVOIE",
        "CADR", "CODPOS", "LIBCOM", "DEPCOM", "LONGITUDE", "LATITUDE"
    ]
    cols_ok = [c for c in cols_affich if c in df_sel.columns]

    for dom_code, df_dom in df_sel.groupby("DOM"):
        lib_dom = f"{dom_code} — {DOM.get(dom_code, '')}"
        with st.expander(f"📂 {lib_dom}", expanded=False):
            for sdom_code, df_sdom in df_dom.groupby("SDOM"):
                lib_sdom = f"{sdom_code} — {SDOM.get(sdom_code, '')}"
                with st.expander(f"📁 {lib_sdom}", expanded=False):
                    df_aff = df_sdom.copy()
                    df_aff["TYPEQU"] = df_aff["TYPEQU"].map(
                        lambda c: f"{c} — {TYPEQU.get(c, c)}"
                    )
                    st.dataframe(df_aff[cols_ok], use_container_width=True, hide_index=True)
                    


else:
    st.info("Utilisez le panneau latéral pour sélectionner un type d'équipement et une commune.")
