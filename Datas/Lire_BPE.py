"""
Lire_BPE.py
-----------
Chargement filtré par département du fichier BPE (INSEE, ~1 Go).
Usage local uniquement.

Nouveautés v1.1 :
  - Bouton 📂 ouvre un dialogue fichier système (tkinter, thread séparé)
  - Cache disque CSV : un département déjà lu est rechargé instantanément
    sans relire le CSV source (fichier : <dossier_BPE>/cache_bpe_<DEP>.csv)
"""

import streamlit as st
import pandas as pd
import chardet
import threading
import queue
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
CHUNK_SIZE   = 50_000
SAMPLE_BYTES = 20_000
COL_DEP      = "DEP"
DEFAULT_PATH = str(ROOT_DIR / "BPE24.csv")
CACHE_PREFIX = "cache_bpe_"          # préfixe des fichiers cache CSV


# ---------------------------------------------------------------------------
# Helpers : encodage / séparateur
# ---------------------------------------------------------------------------
def _detect_encoding(sample: bytes) -> str:
    return chardet.detect(sample).get("encoding") or "utf-8"


def _detect_separator(sample: bytes, encoding: str) -> str:
    first_line = sample.decode(encoding, errors="ignore").split("\n")[0]
    if first_line.count(";") > first_line.count(","):
        return ";"
    return "," if first_line.count(",") > 0 else ";"


# ---------------------------------------------------------------------------
# Dialogue fichier système via tkinter (thread séparé pour ne pas bloquer)
# ---------------------------------------------------------------------------
def _ouvrir_dialogue_fichier() -> str | None:
    """
    Ouvre un vrai dialogue 'Ouvrir fichier' Windows/Linux/macOS.
    Exécuté dans un thread secondaire pour ne pas bloquer Streamlit.
    Retourne le chemin sélectionné ou None si annulé.
    """
    result_queue = queue.Queue()

    def _run():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()          # fenêtre principale invisible
            root.wm_attributes("-topmost", True)
            path = filedialog.askopenfilename(
                title="Sélectionner le fichier BPE",
                filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            )
            root.destroy()
            result_queue.put(path or None)
        except Exception as exc:
            result_queue.put(None)
            st.warning(f"Dialogue fichier indisponible : {exc}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=60)   # attend max 60 s (l'utilisateur peut prendre son temps)
    return result_queue.get_nowait() if not result_queue.empty() else None


# ---------------------------------------------------------------------------
# Cache disque parquet
# ---------------------------------------------------------------------------
def _cache_path(csv_path: str, code_dep: str) -> Path:
    """Retourne le chemin du fichier parquet cache pour ce CSV + département."""
    return Path(csv_path).parent / f"{CACHE_PREFIX}{code_dep}.csv"


def _lire_cache(csv_path: str, code_dep: str) -> pd.DataFrame | None:
    """Retourne le DataFrame depuis le cache parquet, ou None s'il n'existe pas."""
    p = _cache_path(csv_path, code_dep)
    if p.is_file():
        try:
            df = pd.read_csv(p, dtype={COL_DEP: str}, low_memory=False)
            print(f"[BPE] Cache CSV chargé : {p.name} ({len(df):,} lignes)")
            return df
        except Exception as exc:
            st.warning(f"Cache corrompu, relecture du CSV… ({exc})")
            p.unlink(missing_ok=True)
    return None


def _ecrire_cache(csv_path: str, code_dep: str, df: pd.DataFrame) -> None:
    """Sérialise le DataFrame en parquet à côté du CSV."""
    p = _cache_path(csv_path, code_dep)
    try:
        df.to_csv(p, index=False)
        print(f"[BPE] Cache CSV écrit : {p.name}")
    except Exception as exc:
        st.warning(f"Impossible d'écrire le cache parquet : {exc}")


# ---------------------------------------------------------------------------
# Lecture chunked filtrée (appelée seulement si pas de cache)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _charger_bpe(file_path: str, sep: str, encoding: str, code_dep: str) -> pd.DataFrame:
    """Lecture CSV par chunks, filtrée sur COL_DEP == code_dep."""
    fragments  = []
    progress   = st.progress(0, text="Filtrage en cours…")
    status     = st.empty()

    total_size       = Path(file_path).stat().st_size
    estimated_chunks = max(1, total_size // (CHUNK_SIZE * 120))
    chunk_idx = rows_kept = 0

    try:
        reader = pd.read_csv(
            file_path,
            sep=sep,
            encoding=encoding,
            chunksize=CHUNK_SIZE,
            dtype={COL_DEP: str},
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
            status.text(f"Packet {chunk_idx} — {rows_kept:,} lignes retenues…")
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
def lire_bpe() -> pd.DataFrame | None:
    """
    Widget Streamlit : saisie + bouton parcourir + cache parquet + lecture chunked.
    Retourne un DataFrame filtré ou None.
    """
    st.subheader("📂 Chargement BPE — par département")

    # --- Chemin fichier : saisie + bouton parcourir ---
    col_path, col_btn = st.columns([5, 1])
    with col_path:
        file_path = st.text_input(
            "Chemin du fichier BPE (.csv)",
            value=st.session_state.get("bpe_file_path", DEFAULT_PATH),
            key="bpe_path_input",
            help="Saisir le chemin ou cliquer sur 📂 pour parcourir.",
            label_visibility="collapsed",
        ).strip()
    with col_btn:
        if st.button("📂", help="Parcourir…", use_container_width=True):
            chosen = _ouvrir_dialogue_fichier()
            if chosen:
                st.session_state["bpe_file_path"] = chosen
                st.rerun()

    # Synchronise la valeur saisie manuellement
    if file_path:
        st.session_state["bpe_file_path"] = file_path

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

    # --- Indicateur cache disponible ---
    cache_dispo = _cache_path(file_path, code_dep).is_file()
    if cache_dispo:
        st.caption(f"⚡ Cache CSV disponible pour le département {code_dep} — chargement instantané.")

    # --- Bouton chargement ---
    label_btn = f"Charger le département {code_dep}" + (" (depuis cache)" if cache_dispo else "")
    if st.button(label_btn, type="primary"):

        # 1. Essai cache parquet
        df = _lire_cache(file_path, code_dep)

        # 2. Sinon lecture CSV chunked
        if df is None:
            df = _charger_bpe(file_path, sep, encoding, code_dep)
            if df.empty:
                st.warning(f"Aucune ligne trouvée pour le département « {code_dep} ».")
                return None
            # Écriture du cache pour les prochaines fois
            _ecrire_cache(file_path, code_dep, df)

        st.success(f"✅ {len(df):,} équipements — département {code_dep}")
        st.session_state["bpe_df"]  = df
        st.session_state["bpe_dep"] = code_dep
        return df

    # Données déjà en session
    if st.session_state.get("bpe_dep") == code_dep and "bpe_df" in st.session_state:
        st.info(f"Département {code_dep} déjà chargé ({len(st.session_state['bpe_df']):,} lignes).")
        return st.session_state["bpe_df"]

    return None
