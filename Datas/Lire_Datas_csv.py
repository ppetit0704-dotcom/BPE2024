"""
Lire_BPE.py
-----------
Chargement filtré par département du fichier BPE (INSEE, ~1 Go).
Usage local uniquement : le fichier est lu directement depuis son chemin disque.
Stratégie : lecture par chunks pandas — aucune dépendance supplémentaire.

Utilisation :
    from Lire_BPE import lire_bpe
    df_dep = lire_bpe()   # retourne DataFrame ou None
"""

import streamlit as st
import pandas as pd
import chardet
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Constantes — à ajuster si besoin
# ---------------------------------------------------------------------------
CHUNK_SIZE   = 50_000    # lignes par chunk
SAMPLE_BYTES = 20_000    # octets pour détecter encodage + séparateur
COL_DEP      = "DEP"     # colonne département dans la BPE INSEE
DEFAULT_PATH = str(ROOT_DIR / "Datas" / "BPE24.csv")
print("Module (Lire_BPE) : défault path : ",DEFAULT_PATH)

# ---------------------------------------------------------------------------
# Détection encodage + séparateur (sur un échantillon, pas le fichier entier)
# ---------------------------------------------------------------------------
def _detect_encoding(sample: bytes) -> str:
    return chardet.detect(sample).get("encoding") or "utf-8"


def _detect_separator(sample: bytes, encoding: str) -> str:
    first_line = sample.decode(encoding, errors="ignore").split("\n")[0]
    if first_line.count(";") > first_line.count(","):
        return ";"
    return "," if first_line.count(",") > 0 else ";"


# ---------------------------------------------------------------------------
# Lecture chunked filtrée
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _charger_bpe(file_path: str, sep: str, encoding: str, code_dep: str) -> pd.DataFrame:
    """
    Lit le CSV par blocs de CHUNK_SIZE lignes.
    Seules les lignes dont COL_DEP == code_dep sont conservées.
    Résultat mis en cache par (chemin, sep, encoding, code_dep).
    """
    fragments  = []
    progress   = st.progress(0, text="Filtrage en cours…")
    status     = st.empty()

    total_size       = Path(file_path).stat().st_size
    estimated_chunks = max(1, total_size // (CHUNK_SIZE * 120))
    chunk_idx, rows_kept = 0, 0

    try:
        reader = pd.read_csv(
            file_path,
            sep=sep,
            encoding=encoding,
            chunksize=CHUNK_SIZE,
            dtype={COL_DEP: str},   # conserve "01", "2A"…
            low_memory=False,
        )
        for chunk in reader:
            chunk_idx += 1
            if COL_DEP in chunk.columns:
                filtered = chunk[chunk[COL_DEP] == code_dep]
            else:
                if chunk_idx == 1:
                    st.warning(
                        f"Colonne '{COL_DEP}' introuvable. "
                        f"Colonnes disponibles : {list(chunk.columns)}"
                    )
                filtered = chunk
            if not filtered.empty:
                fragments.append(filtered)
                rows_kept += len(filtered)
            pct = min(int(chunk_idx / estimated_chunks * 100), 99)
            status.text(f"Chunk {chunk_idx} — {rows_kept:,} lignes retenues…")
            progress.progress(pct)

    except Exception as exc:
        progress.empty()
        status.empty()
        st.error(f"Erreur lecture : {exc}")
        return pd.DataFrame()

    progress.progress(100)
    progress.empty()
    status.empty()

    return pd.concat(fragments, ignore_index=True) if fragments else pd.DataFrame()


# ---------------------------------------------------------------------------
# Interface publique
# ---------------------------------------------------------------------------
def affiche_selecteur(df) -> pd.DataFrame | None:
    """
    Widget Streamlit : saisie du chemin fichier + code département.
    Retourne un DataFrame filtré ou None.
    """
    st.subheader("📂 Chargement BPE — par département")

    # --- Chemin fichier ---
    file_path = st.text_input(
        "Chemin du fichier BPE (.csv)",
        value=DEFAULT_PATH,
        help="Chemin absolu ou relatif au dossier du script.",
    ).strip()
    print("Lire_Datas_csv(117) : ",file_path)
    if not file_path:
        return None
    if not Path(file_path).is_file():
        st.warning(f"Fichier introuvable : `{file_path}`")
        return None

    # --- Détection encodage + séparateur ---
    with open(file_path, "rb") as f:
        sample = f.read(SAMPLE_BYTES)

    encoding = _detect_encoding(sample)
    sep      = _detect_separator(sample, encoding)
    col1, col2 = st.columns(2)
    col1.caption(f"Encodage : **{encoding}**")
    col2.caption(f"Séparateur : **{sep!r}**")

    # --- Saisie département ---
    code_dep = st.text_input("Code département (ex : 34, 75, 2A…)", max_chars=3).strip()
    if not code_dep:
        return None
    if code_dep.isdigit() and len(code_dep) == 1:
        code_dep = "0" + code_dep

    # --- Chargement ---
    if st.button(f"Charger le département {code_dep}", type="primary"):
        df = _charger_bpe(file_path, sep, encoding, code_dep)
        if df.empty:
            st.warning(f"Aucune ligne trouvée pour le département « {code_dep} ».")
            return None
        st.success(f"✅ {len(df):,} équipements — département {code_dep}")
        st.session_state["bpe_df"]  = df
        st.session_state["bpe_dep"] = code_dep
        return df

    # Données déjà en session pour ce département
    if st.session_state.get("bpe_dep") == code_dep and "bpe_df" in st.session_state:
        st.info(f"Département {code_dep} déjà chargé ({len(st.session_state['bpe_df']):,} lignes).")
        return st.session_state["bpe_df"]

    return None