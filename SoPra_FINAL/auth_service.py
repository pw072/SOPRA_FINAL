from db import fetch_df


def pruefe_login(username, passwort):
    """
    Prüft Benutzername und Passwort gegen die Tabelle T_USER.
    Gibt True zurück, wenn genau dieser Benutzer mit diesem Passwort
    existiert, sonst False.
    """
    sql = """
        SELECT COUNT(*) AS Treffer
        FROM dbo.T_USER
        WHERE USERNAME = ?
          AND USERPASS = ?
    """
    ergebnis = fetch_df(sql, (username, passwort))
    return int(ergebnis["Treffer"].iloc[0]) > 0


def get_user_level(username):
    """
    Liest den SecurityLevel des Benutzers über die in der Datenbank
    vorhandene Funktion dbo.fn_get_user_securitylevel (Quelle:
    T_USER.SECURITYLEVEL). Gibt 0 zurück, wenn nichts gefunden wird.

    Dieses Level steuert über permissions.py / berechtigungen.json,
    welche Aktionen ein Benutzer ausführen darf.
    """
    df = fetch_df("SELECT dbo.fn_get_user_securitylevel(?) AS Level", (username,))
    if df.empty:
        return 0
    wert = df["Level"].iloc[0]
    return int(wert) if wert is not None else 0