import html
import json
from datetime import date, datetime

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

import pagination
from delivery_service import (
    get_lieferscheine,
    get_lieferschein_details,
    get_erlaubte_lieferschein_status,
    lieferschein_status_aendern,
    material_nachbuchung,
)
from permissions import can


ANZEIGE_SPALTEN = [
    "LieferscheinID",
    "KundenauftragID",
    "Kundenfirma",
    "Lieferdatum",
    "Lieferstatus",
]

# Status-Codes (DELIVERYSTATUS)
DELIVERY_IN_TRANSIT = 52
DELIVERY_DELIVERED = 65
DELIVERY_CANCELED = 66
DELIVERY_RETOURNIERT = 68


# -----------------------------------------------------------------------------
# Druckfunktion
# Erweitert die bestehende Ansicht nur um einen echten druckbaren Lieferschein.
# Es wird keine Druckvorschau in Streamlit angezeigt; beim Klick wird direkt der
# Browser-/Windows-Druckdialog für ein verstecktes Druckdokument geöffnet.
# -----------------------------------------------------------------------------
def _wert_ist_leer(wert):
    """Prüft Datenbankwerte sicher auf None/NaN."""
    try:
        return pd.isna(wert)
    except Exception:
        return wert is None


def _text(wert, fallback="—"):
    """Formatiert Datenbankwerte robust als Text."""
    if _wert_ist_leer(wert):
        return fallback
    text = str(wert).strip()
    return text if text else fallback


def _html(wert, fallback="—"):
    """Escaped Text für die HTML-Druckansicht."""
    return html.escape(_text(wert, fallback))


def _datum(wert):
    """Formatiert Datum für den Lieferschein im deutschen Format."""
    if _wert_ist_leer(wert):
        return "—"

    if isinstance(wert, pd.Timestamp):
        return wert.strftime("%d.%m.%Y")

    if isinstance(wert, (datetime, date)):
        return wert.strftime("%d.%m.%Y")

    try:
        datum = pd.to_datetime(wert)
        if pd.isna(datum):
            return _text(wert)
        return datum.strftime("%d.%m.%Y")
    except Exception:
        return _text(wert)


def _menge(wert):
    """Zeigt Mengen ohne unnötige Nachkommastellen."""
    if _wert_ist_leer(wert):
        return "—"

    try:
        zahl = float(wert)
        if zahl.is_integer():
            return str(int(zahl))
        return f"{zahl:g}"
    except Exception:
        return _text(wert)


def _lieferadresse_zeilen(kopf_daten):
    """Baut die Empfängeradresse aus den vorhandenen Lieferschein-Daten."""
    zeilen = [
        _text(kopf_daten.get("Kundenfirma"), ""),
        _text(kopf_daten.get("Ansprechpartner"), ""),
        _text(kopf_daten.get("Lieferadresse_Strasse"), ""),
        " ".join(
            teil
            for teil in [
                _text(kopf_daten.get("Lieferadresse_PLZ"), ""),
                _text(kopf_daten.get("Lieferadresse_Ort"), ""),
            ]
            if teil
        ),
        _text(kopf_daten.get("Lieferadresse_Bundesland"), ""),
    ]
    return [zeile for zeile in zeilen if zeile]


def _lieferschein_druck_html(details):
    """Erzeugt das HTML-Dokument, das direkt an den Druckdialog gegeben wird."""
    kopf_daten = details.iloc[0]
    lieferdatum = _datum(kopf_daten.get("Lieferdatum"))
    druckdatum = datetime.now().strftime("%d.%m.%Y")

    empfaenger_html = "<br>".join(
        html.escape(zeile) for zeile in _lieferadresse_zeilen(kopf_daten)
    ) or "—"

    positions_zeilen = []
    for position, (_, zeile) in enumerate(details.iterrows(), start=1):
        positions_zeilen.append(
            "<tr>"
            f"<td class='pos'>{position}</td>"
            f"<td>{_html(zeile.get('Artikelnummer'))}</td>"
            f"<td>{_html(zeile.get('Artikelbezeichnung'))}</td>"
            f"<td class='menge'>{_menge(zeile.get('Menge'))}</td>"
            "</tr>"
        )

    return f"""
    <!doctype html>
    <html lang="de">
    <head>
        <meta charset="utf-8">
        <title>Lieferschein {_html(kopf_daten.get('LieferscheinID'), '')}</title>
        <style>
            @page {{ size: A4; margin: 14mm; }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                color: #111827;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }}
            .kopf {{
                display: flex;
                justify-content: space-between;
                gap: 24px;
                border-bottom: 2px solid #111827;
                padding-bottom: 16px;
                margin-bottom: 24px;
            }}
            .titel {{ font-size: 28px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
            .untertitel {{ margin-top: 6px; color: #6B7280; }}
            .nummer {{ text-align: right; min-width: 210px; }}
            .nummer-label {{ color: #6B7280; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }}
            .nummer-wert {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
            .adressbereich {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 18px;
                margin-bottom: 22px;
            }}
            .box {{ border: 1px solid #D1D5DB; border-radius: 6px; padding: 12px; min-height: 105px; }}
            .box h2 {{ margin: 0 0 8px; font-size: 11px; color: #6B7280; text-transform: uppercase; letter-spacing: .08em; }}
            .box p {{ margin: 0; }}
            .meta {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                border: 1px solid #D1D5DB;
                margin-bottom: 22px;
            }}
            .meta div {{ padding: 9px 10px; border-right: 1px solid #D1D5DB; }}
            .meta div:last-child {{ border-right: 0; }}
            .meta span {{ display: block; color: #6B7280; font-size: 10px; margin-bottom: 4px; text-transform: uppercase; }}
            .meta strong {{ font-size: 12px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{
                background: #F3F4F6;
                border-top: 1px solid #D1D5DB;
                border-bottom: 1px solid #D1D5DB;
                padding: 8px;
                text-align: left;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: .04em;
            }}
            td {{ border-bottom: 1px solid #E5E7EB; padding: 9px 8px; vertical-align: top; }}
            .pos {{ width: 42px; color: #6B7280; }}
            .menge {{ width: 80px; text-align: right; font-weight: 700; }}
            .hinweis {{
                margin-top: 24px;
                padding: 10px 12px;
                border: 1px solid #E5E7EB;
                background: #F9FAFB;
            }}
            .unterschriften {{ display: grid; grid-template-columns: 1fr 1fr; gap: 56px; margin-top: 58px; }}
            .unterschrift {{ border-top: 1px solid #111827; padding-top: 7px; color: #6B7280; }}
            .fuss {{
                margin-top: 34px;
                padding-top: 9px;
                border-top: 1px solid #D1D5DB;
                display: flex;
                justify-content: space-between;
                color: #6B7280;
                font-size: 10px;
            }}
        </style>
    </head>
    <body>
        <section class="kopf">
            <div>
                <div class="titel">Lieferschein</div>
                <div class="untertitel">Warenbegleitdokument</div>
            </div>
            <div class="nummer">
                <div class="nummer-label">Lieferschein-Nr.</div>
                <div class="nummer-wert">{_html(kopf_daten.get('LieferscheinID'))}</div>
            </div>
        </section>

        <section class="adressbereich">
            <div class="box">
                <h2>Lieferadresse</h2>
                <p>{empfaenger_html}</p>
            </div>
            <div class="box">
                <h2>Absenderadresse</h2>
                <p>{_html(kopf_daten.get('Absenderadresse'))}</p>
            </div>
        </section>

        <section class="meta">
            <div><span>Kundenauftrag</span><strong>{_html(kopf_daten.get('KundenauftragID'))}</strong></div>
            <div><span>Lieferdatum</span><strong>{lieferdatum}</strong></div>
            <div><span>Status</span><strong>{_html(kopf_daten.get('Lieferstatus'))}</strong></div>
            <div><span>Druckdatum</span><strong>{druckdatum}</strong></div>
        </section>

        <table>
            <thead>
                <tr>
                    <th>Pos.</th>
                    <th>Artikelnummer</th>
                    <th>Artikelbezeichnung</th>
                    <th class="menge">Menge</th>
                </tr>
            </thead>
            <tbody>
                {''.join(positions_zeilen)}
            </tbody>
        </table>

        <div class="hinweis">
            Bitte prüfen Sie die Lieferung bei Erhalt auf Vollständigkeit und sichtbare Beschädigungen.
        </div>

        <section class="unterschriften">
            <div class="unterschrift">Ware ausgegeben / Versand</div>
            <div class="unterschrift">Ware erhalten / Empfänger</div>
        </section>

        <section class="fuss">
            <span>Lieferschein {_html(kopf_daten.get('LieferscheinID'))}</span>
            <span>Automatisch erzeugt aus Lager &amp; Versand</span>
        </section>
    </body>
    </html>
    """


def _druck_button_anzeigen(details):
    """Zeigt nur das Drucker-Symbol und öffnet per Klick direkt den Druckdialog."""
    druck_html = _lieferschein_druck_html(details)
    components.html(
        f"""
        <style>
            .druck-button {{
                width: 100%;
                min-height: 20px;
                border: 1px solid #E2E2E5;
                border-radius: 10px;
                background: #FFFFFF;
                color: #111827;
                font-size: 18px;
                cursor: pointer;
            }}
            .druck-button:hover {{ background: #FAFAFB; border-color: #C9C9CE; }}
        </style>

        <button class="druck-button" title="Lieferschein drucken" onclick="druckeLieferschein()">🖨️</button>

        <script>
            const lieferscheinHtml = {json.dumps(druck_html)};

            function druckeLieferschein() {{
                let frame = document.getElementById("print-frame");
                if (!frame) {{
                    frame = document.createElement("iframe");
                    frame.id = "print-frame";
                    frame.style.position = "absolute";
                    frame.style.width = "0";
                    frame.style.height = "0";
                    frame.style.border = "0";
                    frame.style.visibility = "hidden";
                    document.body.appendChild(frame);
                }}

                frame.onload = function() {{
                    frame.contentWindow.focus();
                    frame.contentWindow.print();
                }};
                frame.srcdoc = lieferscheinHtml;
            }}
        </script>
        """,
        height=42,
    )


# -----------------------------------------------------------------------------
# Spediteur-Popup (Modal)
# Wird ausgelöst, sobald ein Lieferschein auf IN TRANSIT gesetzt wurde.
# Simuliert den Spediteur: "Delivered" oder "Retoure".
# -----------------------------------------------------------------------------
@st.dialog("Spediteur")
def spediteur_dialog(delivery_id, benutzer):
    st.write("Konnte die Lieferung zugestellt werden?")

    spalte_links, spalte_rechts = st.columns(2)

    with spalte_links:
        if st.button("Delivered", key="sped_delivered", use_container_width=True):
            try:
                # IN TRANSIT -> DELIVERED (keine Bestands-/Reservierungsänderung)
                lieferschein_status_aendern(
                    delivery_id=delivery_id,
                    neuer_status_id=DELIVERY_DELIVERED,
                    benutzer=benutzer,
                )
                st.session_state.pop("spediteur_delivery_id", None)
                st.session_state["ls_bestaetigung"] = "Lieferung als zugestellt (DELIVERED) gebucht."
                st.rerun()
            except Exception as fehler:
                st.error("Konnte nicht auf DELIVERED gesetzt werden.")
                st.exception(fehler)

    with spalte_rechts:
        if st.button("Retoure", key="sped_retoure", use_container_width=True):
            try:
                # Retoure ist in der DB nur als DELIVERED -> RETOURNIERT erlaubt.
                # Daher zuerst auf DELIVERED, dann auf RETOURNIERT setzen.
                # Beim Schritt auf RETOURNIERT erhöht die Prozedur den Bestand wieder.
                lieferschein_status_aendern(
                    delivery_id=delivery_id,
                    neuer_status_id=DELIVERY_DELIVERED,
                    benutzer=benutzer,
                )
                lieferschein_status_aendern(
                    delivery_id=delivery_id,
                    neuer_status_id=DELIVERY_RETOURNIERT,
                    benutzer=benutzer,
                )
                # Bestätigung mit Bestandsbuchung (RETOURNIERT erhöht den Bestand)
                meldung = material_nachbuchung(delivery_id, DELIVERY_RETOURNIERT, benutzer)
                st.session_state.pop("spediteur_delivery_id", None)
                st.session_state["ls_bestaetigung"] = meldung or "Lieferung als Retoure (RETOURNIERT) gebucht."
                st.rerun()
            except Exception as fehler:
                st.error("Die Retoure konnte nicht gebucht werden.")
                st.exception(fehler)


def anzeigen():
    st.header("Lieferscheine")

    benutzer = st.session_state.get("benutzer", "UNKNOWN")
    level = st.session_state.get("level", 0)

    # Bestätigungsmeldung nach einem Statuswechsel (übersteht das st.rerun)
    if "ls_bestaetigung" in st.session_state:
        st.success(st.session_state.pop("ls_bestaetigung"))

    # Spediteur-Popup anzeigen, falls eine Lieferung gerade auf IN TRANSIT
    # gesetzt wurde. Die ID steht im Session State; das Popup bleibt offen,
    # bis "Delivered" oder "Retoure" gewählt wurde.
    if "spediteur_delivery_id" in st.session_state:
        spediteur_dialog(st.session_state["spediteur_delivery_id"], benutzer)

    try:
        lieferscheine = get_lieferscheine()

        if lieferscheine.empty:
            st.info("Es gibt aktuell keine Lieferscheine.")
            return

        # =====================================================================
        # Übersicht: Suche + Sortierung + Tabelle (mit Seiten) + Zeilenauswahl
        # =====================================================================
        st.subheader("Übersicht")

        such_spalte1, such_spalte2, such_spalte3 = st.columns(3)
        with such_spalte1:
            such_kunde = st.text_input("Kundenname", key="ls_f_kunde")
        with such_spalte2:
            such_auftrag = st.text_input("KundenauftragID", key="ls_f_auftrag")
        with such_spalte3:
            such_lieferschein = st.text_input("LieferscheinID", key="ls_f_lieferschein")

        sort_spalte, richtung_spalte = st.columns(2)
        with sort_spalte:
            sortieren_nach = st.selectbox(
                "Sortieren nach",
                ["LieferscheinID", "KundenauftragID", "Kundenfirma", "Lieferdatum", "Lieferstatus"]
            )
        with richtung_spalte:
            reihenfolge = st.radio(
                "Reihenfolge",
                ["Aufsteigend", "Absteigend"],
                horizontal=True
            )

        gefiltert = lieferscheine.copy()
        if such_kunde:
            gefiltert = gefiltert[gefiltert["Kundenfirma"].str.contains(such_kunde, case=False, na=False)]
        if such_auftrag:
            gefiltert = gefiltert[gefiltert["KundenauftragID"].astype(str).str.contains(such_auftrag, na=False)]
        if such_lieferschein:
            gefiltert = gefiltert[gefiltert["LieferscheinID"].astype(str).str.contains(such_lieferschein, na=False)]

        aufsteigend = (reihenfolge == "Aufsteigend")
        gefiltert = gefiltert.sort_values(by=sortieren_nach, ascending=aufsteigend)

        if gefiltert.empty:
            st.info("Kein Lieferschein gefunden. Bitte Suche anpassen.")
            return

        seiten_gesamt = pagination.anzahl_seiten(len(gefiltert))
        seite = pagination.aktuelle_seite("seite_lieferschein", seiten_gesamt)
        start = (seite - 1) * pagination.SEITENGROESSE
        seiten_daten = gefiltert.iloc[start:start + pagination.SEITENGROESSE]

        tabellen_key = f"tab_ls_s{seite}_{such_kunde}_{such_auftrag}_{such_lieferschein}_{sortieren_nach}_{reihenfolge}"
        auswahl = st.dataframe(
            seiten_daten[ANZEIGE_SPALTEN],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=tabellen_key
        )

        pagination.navigation("seite_lieferschein", seite, seiten_gesamt)

        # =====================================================================
        # Detailansicht: zeigt den in der Tabelle ausgewählten Lieferschein
        # =====================================================================
        detail_titel, detail_druck = st.columns([0.88, 0.12])
        with detail_titel:
            st.subheader("Detailansicht")

        if not auswahl.selection["rows"]:
            with detail_druck:
                st.button("🖨️", disabled=True, use_container_width=True, help="Bitte zuerst einen Lieferschein auswählen")
            st.info("Bitte in der Tabelle eine Zeile anklicken, um den Lieferschein zu öffnen.")
            return

        position = auswahl.selection["rows"][0]
        gewaehlt = seiten_daten.iloc[position]

        details = get_lieferschein_details(int(gewaehlt["LieferscheinID"]))
        kopf_daten = details.iloc[0]

        with detail_druck:
            _druck_button_anzeigen(details)

        spalte_links, spalte_rechts = st.columns(2)

        with spalte_links:
            st.write(f"**Lieferschein:** {kopf_daten['LieferscheinID']}")
            st.write(f"**Kundenauftrag:** {kopf_daten['KundenauftragID']}")
            st.write(f"**Kunde:** {kopf_daten['Kundenfirma']}")
            st.write(f"**Ansprechpartner:** {kopf_daten['Ansprechpartner']}")
            st.write(f"**Status:** {kopf_daten['Lieferstatus']}")
            st.write(f"**Lieferdatum:** {kopf_daten['Lieferdatum']}")

        with spalte_rechts:
            st.write("**Lieferadresse:**")
            st.write(kopf_daten["Lieferadresse_Strasse"])
            st.write(f"{kopf_daten['Lieferadresse_PLZ']} {kopf_daten['Lieferadresse_Ort']}")
            st.write(kopf_daten["Lieferadresse_Bundesland"])
            st.write("**Absenderadresse:**")
            st.write(kopf_daten["Absenderadresse"])

        st.write("**Positionen:**")
        st.dataframe(
            details[["Artikelnummer", "Artikelbezeichnung", "Menge"]],
            use_container_width=True
        )

        # --- Status ändern ---
        st.subheader("Status ändern")

        # 1) Grobe Berechtigung: Darf diese Rolle Lieferstatus überhaupt ändern?
        if not can(level, "change_delivery_status"):
            st.info("Ihre Rolle darf den Lieferstatus nicht ändern (nur Ansicht).")
            return

        # 2) Feine Prüfung aus der DB: erlaubte Folgestatus (LOV_STATUS_FOLGE),
        #    bereits nach dem SecurityLevel des Benutzers gefiltert.
        erlaubte = get_erlaubte_lieferschein_status(
            int(kopf_daten["LieferscheinID"]), level
        )

        if erlaubte.empty:
            st.info(
                "Für diesen Lieferschein gibt es aktuell keinen erlaubten Folgestatus "
                "(oder Ihr Level reicht für die möglichen Übergänge nicht aus)."
            )
            return

        erlaubte = erlaubte.copy()
        erlaubte["Anzeige"] = (
            erlaubte["CODE_NEXT_ID"].astype(str) + " - " + erlaubte["STATUS_NEXT"]
        )

        neuer_status_label = st.selectbox(
            "Neuer Status",
            list(erlaubte["Anzeige"]),
            key=f"status_lieferschein_{kopf_daten['LieferscheinID']}"
        )

        if st.button(
            "Status speichern",
            key=f"btn_status_lieferschein_{kopf_daten['LieferscheinID']}"
        ):
            zeile = erlaubte[erlaubte["Anzeige"] == neuer_status_label]
            neuer_status_id = int(zeile["CODE_NEXT_ID"].iloc[0])

            try:
                delivery_id = int(kopf_daten["LieferscheinID"])

                # 1) Statuswechsel (die G06-Prozedur bucht den Bestand selbst)
                lieferschein_status_aendern(
                    delivery_id=delivery_id,
                    neuer_status_id=neuer_status_id,
                    benutzer=benutzer
                )

                # 2) Material-Nachbuchung (Reservierung) + Bestätigungstext
                meldung = material_nachbuchung(delivery_id, neuer_status_id, benutzer)
                if meldung:
                    st.session_state["ls_bestaetigung"] = meldung
                else:
                    st.session_state["ls_bestaetigung"] = f"Status wurde auf {neuer_status_label} geändert."

                # 3) Bei IN TRANSIT zusätzlich das Spediteur-Popup auslösen
                if neuer_status_id == DELIVERY_IN_TRANSIT:
                    st.session_state["spediteur_delivery_id"] = delivery_id

                st.rerun()
            except Exception as fehler:
                st.error("Der Status konnte nicht geändert werden.")
                st.exception(fehler)

    except Exception as fehler:
        st.error("Die Lieferscheine konnten nicht geladen werden.")
        st.exception(fehler)
