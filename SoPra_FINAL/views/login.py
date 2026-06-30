import textwrap

import streamlit as st

from auth_service import pruefe_login
from permissions import level_fuer_benutzer


def _login_design():
    """Nur das Login-Design. Die Login-Logik bleibt unverändert."""
    st.markdown(
        textwrap.dedent(
            """
        <style>
        /* =====================================================================
           Login-Seite: modernes Design im Stil der gelieferten Grafik
           ===================================================================== */

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 18%, rgba(37,99,235,.10) 0, rgba(37,99,235,0) 28%),
                radial-gradient(circle at 88% 82%, rgba(37,99,235,.12) 0, rgba(37,99,235,0) 30%),
                linear-gradient(135deg, #F8FBFF 0%, #EEF5FF 48%, #F7FAFF 100%);
        }

        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: .45;
            background-image:
                linear-gradient(90deg, rgba(37,99,235,.08) 1px, transparent 1px),
                linear-gradient(rgba(37,99,235,.08) 1px, transparent 1px);
            background-size: 42px 42px;
            mask-image: radial-gradient(circle at 50% 50%, transparent 0%, black 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            transform: translateY(.75rem);
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        /* Login-Karte */
        [data-testid="stMain"] .block-container {
            max-width: 560px !important;
            margin: 3.2rem auto 2rem auto !important;
            padding: 2.6rem 3rem 2.8rem !important;
            background: rgba(255,255,255,.94) !important;
            border: 1px solid rgba(226,232,240,.95) !important;
            border-radius: 28px !important;
            box-shadow:
                0 28px 70px rgba(15,23,42,.14),
                0 2px 6px rgba(15,23,42,.05) !important;
            backdrop-filter: blur(14px);
        }

        .login-hero {
            text-align: center;
            margin-bottom: 1.25rem;
        }

        .login-pictogram {
            width: 180px;
            height: 132px;
            margin: 0 auto .9rem;
            display: block;
        }

        .login-title {
            margin: 0;
            color: #0F2A4A;
            font-size: 1.3rem;
            line-height: 1.16;
            font-weight: 500;
            letter-spacing: -.035em;
}

        .login-subtitle {
            margin: .7rem auto 1.1rem;
            color: #64748B;
            font-size: .96rem;
            line-height: 1.45;
            max-width: 390px;
        }

        .login-divider {
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 1.15rem auto 1.75rem;
            max-width: 410px;
        }

        .login-divider::before,
        .login-divider::after {
            content: "";
            height: 1px;
            flex: 1;
            background: #D8E4F5;
        }

        .login-divider span {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #2563EB;
            box-shadow: 0 0 0 5px rgba(37,99,235,.10);
        }

        /* Streamlit-Felder passend zur Grafik */
        [data-testid="stTextInput"] {
            margin-bottom: 1rem !important;
        }

        [data-testid="stWidgetLabel"] p {
            color: #0F2A4A !important;
            font-size: .95rem !important;
            font-weight: 700 !important;
            margin-bottom: .35rem !important;
        }

        /* Wichtig: Nicht nur input stylen, sondern auch den Streamlit/BaseWeb-Container */
        [data-testid="stTextInput"] [data-baseweb="input"] {
            height: 54px !important;
            min-height: 54px !important;
            border-radius: 13px !important;
            border: 1px solid #C9D7EA !important;
            background: #FFFFFF !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.03) !important;
            overflow: visible !important;
            display: flex !important;
            align-items: center !important;
        }

        [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 4px rgba(37,99,235,.13) !important;
        }

        [data-testid="stTextInput"] input {
            height: 52px !important;
            min-height: 52px !important;
            line-height: 52px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 1rem !important;
            color: #0F172A !important;
            font-size: 1rem !important;
            background: transparent !important;
        }

        [data-testid="stTextInput"] input::placeholder {
            color: #94A3B8 !important;
        }

        /* Passwort-Auge sauber mittig halten */
        [data-testid="stTextInput"] button {
            height: 52px !important;
            min-height: 52px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        .stButton {
            margin-top: 1.05rem;
        }

        .stButton > button {
            width: 100%;
            min-height: 56px;
            border-radius: 13px !important;
            border: 1px solid #1D4ED8 !important;
            background: linear-gradient(135deg, #2563EB 0%, #0F6FD9 100%) !important;
            color: #FFFFFF !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            box-shadow: 0 12px 24px rgba(37,99,235,.25) !important;
            transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
        }

        .stButton > button:hover {
            filter: brightness(.98);
            box-shadow: 0 15px 30px rgba(37,99,235,.30) !important;
            transform: translateY(-1px);
        }

        .stButton > button:active {
            transform: translateY(0) scale(.99);
        }

        [data-testid="stAlert"] {
            border-radius: 13px !important;
            margin-top: 1rem;
        }

        footer {
            visibility: hidden;
        }

        @media (max-width: 700px) {
            [data-testid="stMain"] .block-container {
                margin: 1rem .75rem !important;
                padding: 2rem 1.4rem 2.2rem !important;
                border-radius: 22px !important;
            }

            .login-title {
                font-size: 1.3rem;
            }

            .login-pictogram {
                width: 152px;
                height: 112px;
            }
        }
        </style>
        """
        ),
        unsafe_allow_html=True,
    )


def _login_kopf():
    """Grafischer Kopfbereich mit Piktogramm, Überschrift und Trennlinie."""
    st.markdown(
        textwrap.dedent(
            """
        <div class="login-hero">
            <svg class="login-pictogram" viewBox="0 0 260 190" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <circle cx="132" cy="91" r="74" fill="#EAF2FF"/>
                <rect x="112" y="32" width="74" height="108" rx="10" fill="#163A5F"/>
                <rect x="124" y="47" width="50" height="78" rx="5" fill="#FFFFFF"/>
                <rect x="136" y="21" width="27" height="25" rx="7" fill="#163A5F"/>
                <circle cx="150" cy="33" r="4" fill="#D9E8FF"/>
                <path d="M135 67l7 7 15-17" stroke="#2563EB" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M135 91l7 7 15-17" stroke="#2563EB" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M135 115l7 7 15-17" stroke="#2563EB" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="164" y="82" width="62" height="45" rx="6" fill="#2563EB"/>
                <path d="M226 99h17l15 16v12h-32V99z" fill="#F8FBFF"/>
                <path d="M233 105h10l8 9h-18v-9z" fill="#6EA8FF"/>
                <circle cx="179" cy="134" r="10" fill="#1E293B"/>
                <circle cx="239" cy="134" r="10" fill="#1E293B"/>
                <circle cx="179" cy="134" r="4" fill="#CBD5E1"/>
                <circle cx="239" cy="134" r="4" fill="#CBD5E1"/>
                <path d="M28 88h73v50H28V88z" fill="#D79B55"/>
                <path d="M28 88l36-20 37 20H28z" fill="#E6B36D"/>
                <path d="M101 88l-37-20v50l37 20V88z" fill="#C98743"/>
                <path d="M64 68v50" stroke="#B5783B" stroke-width="5"/>
                <rect x="37" y="119" width="26" height="9" rx="2" fill="#F8FAFC"/>
                <path d="M78 120v-13m0 0l-7 7m7-7l7 7" stroke="#8B5E34" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="123" cy="135" r="25" fill="#2563EB" stroke="#FFFFFF" stroke-width="8"/>
                <path d="M111 134l9 9 17-20" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 93h16M13 111h11M0 126h18" stroke="#C8DAF5" stroke-width="5" stroke-linecap="round"/>
            </svg>
            <h1 class="login-title">Lager &amp; Versand – SoPra G06</h1>
            <div class="login-divider"><span></span></div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def anzeigen():
    _login_design()
    _login_kopf()

    username = st.text_input("Benutzername", placeholder="Benutzername")
    passwort = st.text_input("Passwort", type="password", placeholder="Passwort")

    if st.button("Anmelden", type="primary"):
        try:
            if pruefe_login(username, passwort):
                # Anmeldung erfolgreich -> Benutzer und Level merken.
                # Das Level kommt aus berechtigungen.json:
                #   - Benutzer in "benutzer_level" -> dort eingetragenes Level
                #   - sonst "standard_level" (Standard: 1 = Sachbearbeiter)
                st.session_state["eingeloggt"] = True
                st.session_state["benutzer"] = username
                st.session_state["level"] = level_fuer_benutzer(username)

                # Alternative, falls ihr das Level direkt aus der Datenbank
                # (T_USER.SECURITYLEVEL) nehmen wollt -- dann diese Zeile statt
                # der oberen verwenden (benötigt keine JSON-Pflege):
                #   from auth_service import get_user_level
                #   st.session_state["level"] = get_user_level(username)

                st.rerun()
            else:
                st.error("Benutzername oder Passwort ist falsch.")
        except Exception as fehler:
            st.error("Die Anmeldung konnte nicht geprüft werden.")
            st.exception(fehler)
