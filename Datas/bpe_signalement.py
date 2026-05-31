"""
Module Streamlit — Demande de mise à jour BPE
Intégrable dans le tableau de bord communal existant.
Génère un PDF téléchargeable et un email pré-rempli.
"""

import streamlit as st
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import urllib.parse

# ---------------------------------------------------------------------------
# Données de référence BPE (types d'équipements simplifiés)
# ---------------------------------------------------------------------------

TYPES_EQUIPEMENTS = {
    "🏫 Enseignement": [
        "École maternelle", "École primaire", "Collège", "Lycée",
        "Établissement d'enseignement supérieur", "Autre établissement scolaire",
    ],
    "🏥 Santé": [
        "Cabinet médecin généraliste", "Cabinet infirmier", "Pharmacie",
        "Cabinet dentiste", "Cabinet kinésithérapeute", "EHPAD / Maison de retraite",
        "Hôpital / Clinique", "Centre de santé", "Autre équipement de santé",
    ],
    "⚽ Sport": [
        "Complexe sportif / gymnase", "Terrain de football", "Terrain de tennis",
        "Piscine / bassin nautique", "Salle de sport / fitness", "Stade d'athlétisme",
        "Boulodrome", "Terrain multisports", "Autre équipement sportif",
    ],
    "🎭 Culture & Loisirs": [
        "Médiathèque / Bibliothèque", "Salle polyvalente / des fêtes",
        "Cinéma", "Musée", "Théâtre / salle de spectacle",
        "Espace culturel", "Autre équipement culturel",
    ],
    "🛒 Commerce & Services": [
        "Supermarché / superette", "Boulangerie", "Boucherie",
        "Banque / distributeur", "La Poste / relais postal",
        "Station-service", "Restaurant", "Autre commerce ou service",
    ],
    "🏛️ Services publics": [
        "Mairie / mairie annexe", "Gendarmerie / police", "Pompiers",
        "Agence France Travail (Pôle Emploi)", "CAF / CPAM",
        "Crèche / halte-garderie", "Autre service public",
    ],
    "🚌 Mobilité & Transport": [
        "Arrêt de bus / car interurbain", "Gare ferroviaire",
        "Covoiturage / aire de mobilité", "Autre infrastructure de transport",
    ],
}

MOTIFS = [
    "Équipement existant absent de la BPE",
    "Équipement fermé / démoli toujours référencé",
    "Informations incorrectes (nom, adresse, capacité…)",
    "Équipement déplacé / nouvelle localisation",
    "Changement de catégorie / nature de l'équipement",
    "Autre motif",
]

DESTINATAIRES = {
    "INSEE (BPE générale)": {
        "email": "contact-bpe@insee.fr",
        "objet": "Signalement anomalie Base Permanente des Équipements (BPE)",
    },
    "INJEP / RES (équipements sportifs)": {
        "email": "res@injep.fr",
        "objet": "Signalement anomalie Recensement des Équipements Sportifs (RES)",
    },
    "Direction Régionale INSEE": {
        "email": "",  # à compléter selon la région
        "objet": "Signalement anomalie BPE – territoire communal",
    },
}

# ---------------------------------------------------------------------------
# Génération PDF
# ---------------------------------------------------------------------------

def generer_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        "Titre",
        parent=styles["Title"],
        fontSize=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1a3c5e"),
        alignment=TA_CENTER,
    )
    sous_titre_style = ParagraphStyle(
        "SousTitre",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3c5e"),
        spaceBefore=12,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=4,
        leading=14,
    )

    elements = []

    # En-tête
    elements.append(Paragraph("DEMANDE DE MISE À JOUR", titre_style))
    elements.append(Paragraph("Base Permanente des Équipements (INSEE – BPE)", sous_titre_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3c5e")))
    elements.append(Spacer(1, 0.4 * cm))

    # Bloc émetteur
    elements.append(Paragraph("1. Émetteur de la demande", section_style))
    emetteur_data = [
        ["Commune", data.get("commune", "")],
        ["Code INSEE", data.get("code_insee", "")],
        ["Contact", data.get("contact", "")],
        ["Fonction", data.get("fonction", "")],
        ["Email", data.get("email_contact", "")],
        ["Téléphone", data.get("telephone", "")],
        ["Date", data.get("date_signalement", str(date.today()))],
    ]
    t = Table(emetteur_data, colWidths=[4 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf0f8")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.3 * cm))

    # Bloc équipement
    elements.append(Paragraph("2. Équipement concerné", section_style))
    equip_data = [
        ["Nom de l'équipement", data.get("nom_equip", "")],
        ["Type / Catégorie BPE", data.get("type_equip", "")],
        ["Adresse", data.get("adresse_equip", "")],
        ["Motif du signalement", data.get("motif", "")],
        ["Année de mise en service", data.get("annee_service", "")],
    ]
    t2 = Table(equip_data, colWidths=[4 * cm, 12 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf0f8")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 0.3 * cm))

    # Description détaillée
    elements.append(Paragraph("3. Description de l'anomalie", section_style))
    elements.append(Paragraph(data.get("description", "—"), normal_style))
    elements.append(Spacer(1, 0.3 * cm))

    # Sources / pièces justificatives
    elements.append(Paragraph("4. Sources et justificatifs mentionnés", section_style))
    elements.append(Paragraph(data.get("justificatifs", "—"), normal_style))
    elements.append(Spacer(1, 0.4 * cm))

    # Pied de page
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        f"Document généré le {date.today().strftime('%d/%m/%Y')} — "
        "Tableau de bord artificialisation communale",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.HexColor("#999999"), alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Génération du lien mailto
# ---------------------------------------------------------------------------

def generer_mailto(data: dict, destinataire_info: dict) -> str:
    commune = data.get("commune", "")
    nom_equip = data.get("nom_equip", "")
    type_equip = data.get("type_equip", "")
    motif = data.get("motif", "")
    contact = data.get("contact", "")
    description = data.get("description", "")
    annee = data.get("annee_service", "")

    corps = f"""Madame, Monsieur,

La commune de {commune} souhaite signaler une anomalie dans la Base Permanente des Équipements (BPE).

ÉQUIPEMENT CONCERNÉ
Nom : {nom_equip}
Type / Catégorie BPE : {type_equip}
Adresse : {data.get("adresse_equip", "")}
Année de mise en service : {annee}

MOTIF DU SIGNALEMENT
{motif}

DESCRIPTION DE L'ANOMALIE
{description}

JUSTIFICATIFS DISPONIBLES
{data.get("justificatifs", "—")}

Contact : {contact} — {data.get("fonction", "")}
Email : {data.get("email_contact", "")}
Téléphone : {data.get("telephone", "")}

Nous restons à votre disposition pour tout complément d'information.

Cordialement,
{contact}
{commune}
"""
    objet = destinataire_info["objet"] + f" – {commune} – {nom_equip}"
    email_dest = destinataire_info["email"]
    params = urllib.parse.urlencode({"subject": objet, "body": corps})
    return f"mailto:{email_dest}?{params}"


# ---------------------------------------------------------------------------
# Interface Streamlit principale
# ---------------------------------------------------------------------------

def afficher_formulaire_bpe():
    st.markdown("""
    <style>
    .bpe-header {
        background: linear-gradient(135deg, #1a3c5e 0%, #2d6a9f 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .bpe-header h2 { margin: 0; font-size: 1.2rem; }
    .bpe-header p  { margin: 0.3rem 0 0; font-size: 0.85rem; opacity: 0.85; }
    .section-label {
        font-weight: 600;
        color: #1a3c5e;
        font-size: 0.95rem;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
        border-left: 3px solid #2d6a9f;
        padding-left: 0.5rem;
    }
    </style>
    <div class="bpe-header">
        <h2>📋 Demande de mise à jour BPE</h2>
        <p>Signalez un équipement manquant, erroné ou fermé dans la Base Permanente des Équipements (INSEE).</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Section 1 : Émetteur ----
    st.markdown('<div class="section-label">1 · Émetteur de la demande</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        commune = st.text_input("Nom de la commune *", placeholder="Ex : Saint-Gilles-du-Gard")
    with col2:
        code_insee = st.text_input("Code INSEE *", placeholder="30258", max_chars=5)

    col3, col4 = st.columns(2)
    with col3:
        contact = st.text_input("Nom du contact *", placeholder="Prénom Nom")
    with col4:
        fonction = st.text_input("Fonction", placeholder="Ex : Directeur général des services")

    col5, col6 = st.columns(2)
    with col5:
        email_contact = st.text_input("Email de contact *", placeholder="contact@mairie-xxx.fr")
    with col6:
        telephone = st.text_input("Téléphone", placeholder="05 XX XX XX XX")

    date_signalement = st.date_input("Date du signalement", value=date.today())

    st.divider()

    # ---- Section 2 : Équipement ----
    st.markdown('<div class="section-label">2 · Équipement concerné</div>', unsafe_allow_html=True)

    nom_equip = st.text_input("Nom de l'équipement *", placeholder="Ex : Complexe sportif Marcel Pagnol")
    adresse_equip = st.text_input("Adresse de l'équipement", placeholder="Ex : 12 rue des Sports, 30258 Saint-Gilles-du-Gard")

    col7, col8 = st.columns([2, 1])
    with col7:
        categorie = st.selectbox("Catégorie BPE *", options=list(TYPES_EQUIPEMENTS.keys()))
    with col8:
        annee_service = st.number_input(
            "Année de mise en service",
            min_value=1900, max_value=date.today().year,
            value=2020, step=1
        )

    type_equip = st.selectbox(
        "Type d'équipement *",
        options=TYPES_EQUIPEMENTS.get(categorie, [])
    )

    motif = st.selectbox("Motif du signalement *", options=MOTIFS)

    st.divider()

    # ---- Section 3 : Description ----
    st.markdown('<div class="section-label">3 · Description de l\'anomalie</div>', unsafe_allow_html=True)
    description = st.text_area(
        "Description détaillée *",
        placeholder=(
            "Décrivez précisément l'anomalie constatée dans la BPE.\n"
            "Ex : Le complexe sportif communal 'Marcel Pagnol' (gymnase + terrain foot) "
            "a été inauguré en septembre 2020 et n'apparaît pas dans la BPE 2024."
        ),
        height=120,
    )

    justificatifs = st.text_area(
        "Sources / pièces justificatives disponibles",
        placeholder=(
            "Ex : Délibération du conseil municipal n°2019-45, "
            "arrêté de permis de construire, article de presse local, "
            "photos, extrait cadastral…"
        ),
        height=80,
    )

    st.divider()

    # ---- Section 4 : Destinataire ----
    st.markdown('<div class="section-label">4 · Destinataire du signalement</div>', unsafe_allow_html=True)

    # Suggestion automatique selon la catégorie
    suggestion = "INJEP / RES (équipements sportifs)" if "Sport" in categorie else "INSEE (BPE générale)"
    destinataire_label = st.selectbox(
        "Envoyer à *",
        options=list(DESTINATAIRES.keys()),
        index=list(DESTINATAIRES.keys()).index(suggestion),
    )
    destinataire_info = DESTINATAIRES[destinataire_label]

    if destinataire_label == "Direction Régionale INSEE":
        email_dr = st.text_input(
            "Email de la DR INSEE de votre région",
            placeholder="dr-xxx@insee.fr"
        )
        destinataire_info = dict(destinataire_info)
        destinataire_info["email"] = email_dr

    st.divider()

    # ---- Génération ----
    champs_obligatoires = [commune, code_insee, contact, email_contact, nom_equip, type_equip, motif, description]
    formulaire_valide = all(str(c).strip() for c in champs_obligatoires)

    data = {
        "commune": commune,
        "code_insee": code_insee,
        "contact": contact,
        "fonction": fonction,
        "email_contact": email_contact,
        "telephone": telephone,
        "date_signalement": date_signalement.strftime("%d/%m/%Y"),
        "nom_equip": nom_equip,
        "adresse_equip": adresse_equip,
        "type_equip": f"{categorie} — {type_equip}",
        "annee_service": str(annee_service),
        "motif": motif,
        "description": description,
        "justificatifs": justificatifs,
    }

    col_pdf, col_mail = st.columns(2)

    with col_pdf:
        if st.button("📄 Générer le PDF", use_container_width=True, disabled=not formulaire_valide):
            pdf_buffer = generer_pdf(data)
            nom_fichier = f"signalement_bpe_{code_insee}_{nom_equip[:20].replace(' ', '_')}.pdf"
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=pdf_buffer,
                file_name=nom_fichier,
                mime="application/pdf",
                use_container_width=True,
            )

    with col_mail:
        if formulaire_valide:
            mailto_url = generer_mailto(data, destinataire_info)
            st.markdown(
                f'<a href="{mailto_url}" target="_blank">'
                f'<button style="width:100%;padding:0.5rem;background:#2d6a9f;color:white;'
                f'border:none;border-radius:4px;cursor:pointer;font-size:0.9rem;">'
                f'✉️ Ouvrir dans ma messagerie</button></a>',
                unsafe_allow_html=True,
            )
        else:
            st.button("✉️ Ouvrir dans ma messagerie", use_container_width=True, disabled=True)

    if not formulaire_valide:
        st.caption("⚠️ Remplissez tous les champs obligatoires (*) pour activer la génération.")


# ---------------------------------------------------------------------------
# Point d'entrée (page autonome ou intégration)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(
        page_title="Signalement BPE",
        page_icon="📋",
        layout="centered",
    )
    afficher_formulaire_bpe()
