"""
affiche_selecteur_bpe.py
------------------------
Sélecteur BPE orienté territoire : COMMUNE ou EPCI en premier.
Le tableau résultant est trié et enrichi DOM → SDOM → TYPEQU.
Référentiel INSEE intégré (BPE 2024).

Utilisation :
    from affiche_selecteur_bpe import affiche_selecteur_bpe
    affiche_selecteur_bpe(df)
"""

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Référentiel INSEE — BPE 2024
# ---------------------------------------------------------------------------
DOM = {
    "A": "SERVICES POUR LES PARTICULIERS", "B": "COMMERCES",
    "C": "ENSEIGNEMENT", "D": "SANTÉ ET ACTION SOCIALE",
    "E": "TRANSPORTS ET DÉPLACEMENTS", "F": "SPORTS, LOISIRS ET CULTURE",
    "G": "TOURISME",
}
SDOM = {
    "A1": "SERVICES PUBLICS", "A2": "SERVICES GÉNÉRAUX",
    "A3": "SERVICES AUTOMOBILES", "A4": "ARTISANAT DU BÂTIMENT",
    "A5": "AUTRES SERVICES", "B1": "GRANDES SURFACES",
    "B2": "COMMERCES ALIMENTAIRES", "B3": "COMMERCES SPÉCIALISÉS NON-ALIMENTAIRES",
    "C1": "ENSEIGNEMENT DU PREMIER DEGRÉ",
    "C2": "ENSEIGNEMENT DU SECOND DEGRÉ - PREMIER CYCLE",
    "C3": "ENSEIGNEMENT DU SECOND DEGRÉ - SECOND CYCLE",
    "C4": "ENSEIGNEMENT SUPÉRIEUR NON-UNIVERSITAIRE",
    "C5": "ENSEIGNEMENT SUPÉRIEUR UNIVERSITAIRE",
    "C6": "FORMATION CONTINUE", "C7": "AUTRES SERVICES DE L'ÉDUCATION",
    "D1": "ETABLISSEMENTS ET SERVICES DE SANTÉ",
    "D2": "FONCTIONS MÉDICALES ET PARAMÉDICALES (À TITRE LIBÉRAL)",
    "D3": "AUTRES ÉTABLISSEMENTS ET SERVICES À CARACTÈRE SANITAIRE",
    "D4": "ACTION SOCIALE POUR PERSONNES ÂGÉES",
    "D5": "ACTION SOCIALE POUR ENFANTS EN BAS-ÂGE",
    "D6": "ACTION SOCIALE POUR HANDICAPÉS",
    "D7": "AUTRES SERVICES D'ACTION SOCIALE",
    "E1": "INFRASTRUCTURES DE TRANSPORTS",
    "F1": "EQUIPEMENTS SPORTIFS", "F2": "EQUIPEMENTS DE LOISIRS",
    "F3": "EQUIPEMENTS CULTURELS ET SOCIOCULTURELS", "G1": "TOURISME",
}
TYPEQU = {
    "A101": "POLICE", "A104": "GENDARMERIE", "A105": "COUR D'APPEL",
    "A108": "CONSEIL DE PRUD'HOMMES", "A109": "TRIBUNAL DE COMMERCE",
    "A120": "DIRECTION RÉGIONALE DES FINANCES PUBLIQUES",
    "A121": "DIRECTION DÉPARTEMENTALE DES FINANCES PUBLIQUES",
    "A122": "RÉSEAU DE PROXIMITÉ FRANCE TRAVAIL",
    "A124": "MAISON DE JUSTICE ET DU DROIT", "A125": "ANTENNE DE JUSTICE",
    "A126": "CONSEIL DÉPARTEMENTAL D'ACCÈS AU DROIT",
    "A128": "FRANCE SERVICES", "A129": "MAIRIE",
    "A130": "BUREAU D'AIDE JURIDICTIONNELLE", "A131": "TRIBUNAL JUDICIAIRE",
    "A132": "TRIBUNAL DE PROXIMITÉ", "A133": "DÉCHÈTERIE",
    "A134": "COUR CRIMINELLE DEPARTEMENTALE", "A135": "COUR D'ASSISES",
    "A136": "JURIDICTION ADMINISTRATIVE", "A137": "TRIBUNAL CORRECTIONNEL",
    "A138": "TRIBUNAL DE POLICE", "A139": "TRIBUNAL POUR ENFANTS",
    "A203": "BANQUE, CAISSE D'ÉPARGNE", "A205": "SERVICES FUNÉRAIRES",
    "A206": "BUREAU DE POSTE", "A207": "RELAIS POSTE", "A208": "AGENCE POSTALE",
    "A301": "RÉPARATION AUTOMOBILE ET DE MATÉRIEL AGRICOLE",
    "A302": "CONTRÔLE TECHNIQUE AUTOMOBILE",
    "A303": "LOCATION AUTO-UTILITAIRES LÉGERS", "A304": "ÉCOLE DE CONDUITE",
    "A401": "MAÇON", "A402": "PLÂTRIER PEINTRE",
    "A403": "MENUISIER CHARPENTIER SERRURIER",
    "A404": "PLOMBIER COUVREUR CHAUFFAGISTE", "A405": "ÉLECTRICIEN",
    "A406": "ENTREPRISE GÉNÉRALE DU BÂTIMENT",
    "A501": "COIFFURE", "A502": "VÉTÉRINAIRE",
    "A503": "AGENCE DE TRAVAIL TEMPORAIRE",
    "A504": "RESTAURANT - RESTAURATION RAPIDE",
    "A505": "AGENCE IMMOBILIÈRE", "A506": "PRESSING-LAVERIE AUTOMATIQUE",
    "A507": "INSTITUT DE BEAUTÉ-ONGLERIE",
    "B103": "GRANDE SURFACE DE BRICOLAGE",
    "B104": "HYPERMARCHÉ ET GRAND MAGASIN",
    "B105": "SUPERMARCHÉ ET MAGASIN MULTI-COMMERCE",
    "B201": "SUPÉRETTE", "B202": "ÉPICERIE",
    "B204": "BOUCHERIE CHARCUTERIE", "B205": "PRODUITS SURGELÉS",
    "B206": "POISSONNERIE", "B207": "BOULANGERIE-PÂTISSERIE",
    "B208": "COMMERCE SPÉCIALISÉ EN FRUITS ET LÉGUMES",
    "B209": "COMMERCE DE BOISSONS", "B210": "AUTRES COMMERCES ALIMENTAIRES",
    "B302": "MAGASIN DE VÊTEMENTS", "B303": "MAGASIN D'ÉQUIPEMENTS DU FOYER",
    "B304": "MAGASIN DE CHAUSSURES", "B306": "MAGASIN DE MEUBLES",
    "B307": "MAGASIN D'ARTICLES DE SPORTS ET DE LOISIRS",
    "B308": "MAGASIN DE REVÊTEMENTS MURS ET SOLS",
    "B309": "DROGUERIE QUINCAILLERIE BRICOLAGE",
    "B310": "PARFUMERIE-COSMÉTIQUE", "B311": "HORLOGERIE-BIJOUTERIE",
    "B312": "FLEURISTE-JARDINERIE-ANIMALERIE", "B313": "MAGASIN D'OPTIQUE",
    "B315": "MAGASIN DE MATÉRIEL MÉDICAL ET ORTHOPÉDIQUE",
    "B316": "STATION-SERVICE", "B317": "COMMERCE DE TISSUS ET MERCERIE",
    "B318": "COMMERCE DE JEUX ET JOUETS",
    "B319": "MAROQUINERIE ET ARTICLES DE VOYAGE",
    "B320": "COMMERCE DE COMBUSTIBLES DOMESTIQUES",
    "B321": "MAGASIN ÉLECTROMÉNAGER, MATÉRIEL AUDIO VIDÉO INFORMATIQUE",
    "B322": "MAGASIN DE MATÉRIELS DE TÉLÉCOMMUNICATION",
    "B323": "COMMERCE DE BIENS D'OCCASION", "B324": "LIBRAIRIE",
    "B325": "PAPETERIE ET PRESSE",
    "B326": "STATION DE RECHARGE DE VÉHICULES ÉLECTRIQUES",
    "C107": "ÉCOLE MATERNELLE", "C108": "ÉCOLE PRIMAIRE",
    "C109": "ÉCOLE ÉLÉMENTAIRE", "C201": "COLLÈGE",
    "C301": "LYCÉE D'ENSEIGNEMENT GÉNÉRAL ET/OU TECHNOLOGIQUE",
    "C302": "LYCÉE D'ENSEIGNEMENT PROFESSIONNEL",
    "C303": "LYCÉE D'ENSEIGNEMENT TECHNIQUE ET/OU PROFESSIONNEL AGRICOLE",
    "C304": "SGT SECTION D'ENSEIGNEMENT GÉNÉRAL ET TECHNOLOGIQUE",
    "C305": "SEP SECTION D'ENSEIGNEMENT PROFESSIONNEL",
    "C401": "STS / CPGE", "C403": "FORMATION COMMERCE",
    "C409": "AUTRE FORMATION POST BAC NON UNIVERSITAIRE",
    "C410": "ÉCOLE DE FORMATION AUX PROFESSIONS SANITAIRES ET SOCIALES",
    "C501": "UFR", "C502": "INSTITUT UNIVERSITAIRE",
    "C503": "ÉCOLE D'INGÉNIEURS",
    "C504": "ENSEIGNEMENT GÉNÉRAL SUPÉRIEUR PRIVÉ",
    "C505": "ÉCOLE D'ENSEIGNEMENT SUPÉRIEUR AGRICOLE",
    "C509": "AUTRE ENSEIGNEMENT SUPÉRIEUR", "C602": "GRETA",
    "C603": "CENTRE DISPENSANT DE LA FORMATION CONTINUE AGRICOLE",
    "C604": "FORMATION AUX MÉTIERS DU SPORT",
    "C610": "ORGANISME DE FORMATION EN APPRENTISSAGE",
    "C701": "RÉSIDENCE UNIVERSITAIRE", "C702": "RESTAURANT UNIVERSITAIRE",
    "D101": "ÉTABLISSEMENT DE SOINS DE COURTE DURÉE",
    "D102": "ÉTABLISSEMENT DE SOINS DE SUITE ET DE RÉADAPTATION",
    "D103": "ÉTABLISSEMENT DE SOINS DE LONGUE DURÉE",
    "D104": "ÉTABLISSEMENT PSYCHIATRIQUE",
    "D105": "CENTRE DE LUTTE CONTRE LE CANCER",
    "D106": "URGENCES", "D107": "MATERNITÉ", "D108": "CENTRE DE SANTÉ",
    "D109": "STRUCTURE PSYCHIATRIQUE EN AMBULATOIRE",
    "D110": "CENTRE DE MÉDECINE PRÉVENTIVE", "D111": "DIALYSE",
    "D112": "HOSPITALISATION À DOMICILE",
    "D113": "MAISON DE SANTÉ PLURIDISCIPLINAIRE",
    "D114": "SERVICE DE PRISE EN CHARGE DES ADDICTIONS",
    "D115": "SERVICES DE SANTÉ MATERNELLE ET INFANTILE",
    "D245": "PROFESSIONNELS DE L'APPAREILLAGE",
    "D247": "ERGOTHÉRAPEUTE", "D248": "PSYCHOMOTRICIEN",
    "D249": "DIÉTÉTICIEN", "D250": "PSYCHOLOGUE",
    "D251": "ALLERGOLOGUE", "D252": "ANESTHÉSISTE-RÉANIMATEUR",
    "D253": "SPÉCIALISTE EN CHIRURGIE GÉNÉRALE",
    "D254": "SPÉCIALISTE EN CHIRURGIE ORTHOPÉDIQUE, PLASTIQUE ET TRAUMATOLOGIQUE",
    "D255": "ENDOCRINOLOGUE", "D256": "GÉRIATRE", "D257": "HÉMATOLOGUE",
    "D258": "SPÉCIALISTE EN MÉDECINE PHYSIQUE ET DE RÉADAPTATION",
    "D259": "NEUROLOGUE",
    "D260": "SPÉCIALISTE EN ONCOLOGIE, ANATOMIE ET CYTOLOGIE PATHOLOGIQUES",
    "D261": "RHUMATOLOGUE", "D262": "UROLOGUE, NÉPHROLOGUE",
    "D265": "MÉDECIN GÉNÉRALISTE", "D266": "SPÉCIALISTE EN CARDIOLOGIE",
    "D267": "SPÉCIALISTE EN DERMATOLOGIE VÉNÉRÉOLOGIE",
    "D268": "SPÉCIALISTE EN GASTRO-ENTÉROLOGIE HÉPATOLOGIE",
    "D269": "SPÉCIALISTE EN PSYCHIATRIE",
    "D270": "SPÉCIALISTE EN OPHTALMOLOGIE",
    "D271": "SPÉCIALISTE EN OTO-RHINO-LARYNGOLOGIE",
    "D272": "SPÉCIALISTE EN PÉDIATRIE", "D273": "SPÉCIALISTE EN PNEUMOLOGIE",
    "D274": "SPÉCIALISTE EN RADIODIAGNOSTIC ET IMAGERIE MÉDICALE",
    "D275": "SPÉCIALISTE EN STOMATOLOGIE",
    "D276": "SPÉCIALISTE EN GYNÉCOLOGIE MÉDICALE ET/OU OBSTÉTRIQUE",
    "D277": "CHIRURGIEN DENTISTE", "D278": "SAGE-FEMME",
    "D279": "MASSEUR KINÉSITHÉRAPEUTE", "D280": "PÉDICURE-PODOLOGUE",
    "D281": "INFIRMIER",
    "D302": "LABORATOIRE D'ANALYSES ET DE BIOLOGIE MÉDICALE",
    "D303": "AMBULANCE", "D304": "TRANSFUSION SANGUINE",
    "D305": "ÉTABLISSEMENT THERMAL", "D307": "PHARMACIE",
    "D401": "PERSONNES ÂGÉES : HÉBERGEMENT",
    "D402": "PERSONNES ÂGÉES : SOINS À DOMICILE",
    "D403": "PERSONNES ÂGÉES : SERVICES D'AIDE",
    "D502": "ÉTABLISSEMENT D'ACCUEIL DU JEUNE ENFANT",
    "D503": "LIEUX D'ACCUEIL ENFANT-PARENT",
    "D504": "RELAIS PETITE ENFANCE",
    "D505": "ACCUEIL DE LOISIR SANS HÉBERGEMENT",
    "D506": "CENTRES SOCIAUX", "D507": "MÉDIATION FAMILIALE",
    "D601": "ENFANTS HANDICAPÉS : HÉBERGEMENT",
    "D602": "ENFANTS HANDICAPÉS : SERVICES À DOMICILE OU AMBULATOIRES",
    "D603": "ADULTES HANDICAPÉS : ACCUEIL/HÉBERGEMENT",
    "D604": "ADULTES HANDICAPÉS : SERVICES D'AIDE", "D605": "TRAVAIL PROTÉGÉ",
    "D606": "ADULTES HANDICAPÉS : SERVICES DE SOINS À DOMICILE",
    "D607": "SERVICE D'AIDE AUX DÉFICIENTS VISUELS OU AUDITIFS",
    "D701": "PROTECTION DE L'ENFANCE : HÉBERGEMENT",
    "D702": "PROTECTION DE L'ENFANCE : ACTION ÉDUCATIVE",
    "D703": "CENTRE D'HÉBERGEMENT ET DE RÉINSERTION SOCIALE",
    "D704": "CENTRE PROVISOIRE D'HÉBERGEMENT",
    "D705": "CENTRE D'ACCUEIL DE DEMANDEURS D'ASILE",
    "D710": "AUTRES HÉBERGEMENTS POUR ADULTES ET FAMILLES EN DIFFICULTÉ",
    "D711": "SERVICE D'AIDE AUX FEMMES EN SITUATION DE VULNÉRABILITÉ",
    "E101": "TAXI-VTC", "E102": "AÉROPORT",
    "E107": "GARE DE VOYAGEURS D'INTÉRÊT NATIONAL",
    "E108": "GARE DE VOYAGEURS D'INTÉRÊT RÉGIONAL",
    "E109": "GARE DE VOYAGEURS D'INTÉRÊT LOCAL",
    "F101": "BASSIN DE NATATION", "F102": "BOULODROME", "F103": "TENNIS",
    "F105": "DOMAINE SKIABLE", "F106": "CENTRE ÉQUESTRE",
    "F107": "ATHLÉTISME", "F108": "TERRAIN DE GOLF",
    "F109": "PARCOURS SPORTIF/SANTÉ", "F110": "SPORTS DE GLACE",
    "F111": "PLATEAUX ET TERRAINS DE JEUX EXTÉRIEURS",
    "F113": "TERRAINS DE GRANDS JEUX", "F114": "SALLES DE COMBAT",
    "F116": "SALLES NON SPÉCIALISÉES", "F118": "SPORTS NAUTIQUES",
    "F119": "BOWLING", "F120": "SALLES DE REMISE EN FORME",
    "F121": "SALLES MULTISPORTS, GYMNASES",
    "F122": "CIRCUIT / PISTE DE SPORTS MÉCANIQUES",
    "F123": "MUR ET FRONTON", "F124": "PAS DE TIR",
    "F125": "SITE D'ACTIVITÉS AÉRIENNES", "F126": "SITE DE MODÉLISME",
    "F127": "STRUCTURE ARTIFICIELLE D'ESCALADE",
    "F128": "ÉQUIPEMENTS DE CYCLISME", "F129": "SALLES SPÉCIALISÉES",
    "F130": "SKATEPARK & VÉLO-FREESTYLE",
    "F201": "BAIGNADE AMÉNAGÉE", "F202": "PORT DE PLAISANCE – MOUILLAGE",
    "F203": "BOUCLE DE RANDONNÉE ET PARCOURS DE COURSE D'ORIENTATION",
    "F204": "ÉQUIPEMENTS DE SPORTS DE NATURE",
    "F303": "CINÉMA", "F305": "CONSERVATOIRE", "F307": "BIBLIOTHÈQUE",
    "F312": "EXPOSITION ET MÉDIATION CULTURELLE",
    "F313": "ESPACE REMARQUABLE ET PATRIMOINE", "F314": "ARCHIVES",
    "F315": "ARTS DU SPECTACLE",
    "G101": "AGENCE DE VOYAGE", "G102": "HÔTEL", "G103": "CAMPING",
    "G104": "INFORMATION TOURISTIQUE",
    "G105": "AUTRES HÉBERGEMENTS COLLECTIFS TOURISTIQUES",
}

# Colonnes à afficher dans le tableau résultat
COLS_AFFICH = ["Domaine", "Sous-domaine", "Type d'équipement",
               "NOMRS", "CNOMRS", "TYPVOIE", "LIBVOIE", "CADR",
               "CODPOS", "LIBCOM", "DEPCOM"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _reset(*keys):
    for k in keys:
        st.session_state[k] = None


def _enrichir(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute trois colonnes libellés DOM/SDOM/TYPEQU et trie le DataFrame."""
    out = df.copy()
    out["Domaine"]          = out["DOM"].map(lambda c: f"{c} — {DOM.get(c, c)}")
    out["Sous-domaine"]     = out["SDOM"].map(lambda c: f"{c} — {SDOM.get(c, c)}")
    out["Type d'équipement"] = out["TYPEQU"].map(lambda c: f"{c} — {TYPEQU.get(c, c)}")
    return out.sort_values(["DOM", "SDOM", "TYPEQU", "LIBCOM", "NOMRS"],
                           ignore_index=True)


# ---------------------------------------------------------------------------
# Sélecteur principal
# ---------------------------------------------------------------------------
def affiche_selecteur_bpe(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Sélecteur territoire-first : COMMUNE ou EPCI → tableau enrichi et trié.
    Retourne le DataFrame filtré (toutes colonnes + libellés) ou None.
    """

    """
    # Initialisation session_state
    for k in ("bpe_mode", "bpe_territoire", "bpe_last_territoire"):
        if k not in st.session_state:
            st.session_state[k] = None
    """

    # Initialisation session_state
    if "bpe_mode" not in st.session_state:
        st.session_state["bpe_mode"] = "Commune"   # valeur par défaut
    if "bpe_territoire" not in st.session_state:
        st.session_state["bpe_territoire"] = None
    if "bpe_last_territoire" not in st.session_state:
        st.session_state["bpe_last_territoire"] = None

    # --- Choix du mode : Commune ou EPCI ---
    mode = st.radio(
        "Rechercher par",
        options=["Commune", "EPCI"],
        horizontal=True,
        key="bpe_mode",
    )

    # Reset territoire si on change de mode
    if st.session_state.get("_bpe_mode_last") != mode:
        _reset("bpe_territoire", "bpe_last_territoire")
        st.session_state["_bpe_mode_last"] = mode
        st.rerun()

    # --- Sélecteur territoire ---
    if mode == "Commune":
        col_ter = "LIBCOM"
        label   = "Commune"
        choix   = sorted(df[col_ter].dropna().unique())
    else:
        col_ter = "EPCI"
        label   = "EPCI (code)"
        # Forcer en str pour éviter les float numpy (NaN éliminés puis cast)
        choix   = sorted(df[col_ter].dropna().astype(str).unique())
    territoire = st.selectbox(
        label,
        options=[None] + choix,
        format_func=lambda x: f"— Choisir {'une commune' if mode == 'Commune' else 'un EPCI'} —"
                               if x is None else x,
        key="bpe_territoire",
    )

    if territoire is None:
        return None

    # --- Filtrage immédiat ---
    # Pour EPCI : la colonne peut être float en mémoire, on compare en str
    if mode == "EPCI":
        df_ter = df[df[col_ter].astype(str) == territoire].copy()
    else:
        df_ter = df[df[col_ter] == territoire].copy()

    if df_ter.empty:
        st.warning(f"Aucun équipement trouvé pour : {territoire}")
        return None

    # --- Enrichissement et tri ---
    df_out = _enrichir(df_ter)

    # --- Résumé ---
    nb_eq  = len(df_out)
    nb_typ = df_out["TYPEQU"].nunique()
    titre  = territoire if mode == "Commune" else f"EPCI {territoire}"
    st.caption(f"✅ **{titre}** — {nb_eq} équipement{'s' if nb_eq > 1 else ''} · {nb_typ} type{'s' if nb_typ > 1 else ''}")

    # --- Colonnes à retourner ---
    cols_ok = [c for c in COLS_AFFICH if c in df_out.columns]
    return df_out[cols_ok + [c for c in df_out.columns if c not in cols_ok]]
