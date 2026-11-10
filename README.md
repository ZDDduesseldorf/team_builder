# W4 Team Builder

Kleine Streamlit-App zum Sammeln von Rollenwünschen und zur automatischen Einteilung der Studierenden für das W4-Teampraktikum.

## Rollen

Standardmäßig werden vier Rollen verwendet:

- **Product Owner / Integration** – genau 1 Person pro Team
- **Test Team** – 1–2 Personen pro Team
- **Software Development** – 2–3 Personen pro Team (bei einem notwendigen 3er-Team: mindestens 1)
- **Review / Release** – 0–1 Person pro Team

Teams haben grundsätzlich **4–6 Personen**. Nur wenn sich die Anzahl der anwesenden Studierenden rechnerisch nicht in 4er- bis 6er-Teams aufteilen lässt, wird ein einzelnes **3er-Team** zugelassen.

## Wie optimiert das Tool?

Jede Person wählt drei verschiedene Rollen als 1., 2. und 3. Wunsch. Die Optimierung ist lexikographisch:

1. zuerst möglichst viele Erstwünsche,
2. unter diesen Lösungen möglichst viele Zweitwünsche,
3. anschließend möglichst viele Drittwünsche,
4. nur falls nötig werden nicht gerankte Rollen verwendet.

Das Tool verwendet dafür einen kleinen, dependency-freien **Min-Cost-Flow-Algorithmus** in `optimizer.py`.

## Warum Streamlit und nicht GitHub Pages?

GitHub Pages hostet statische Dateien und führt keinen Python-Server aus. Diese App benötigt aber zentrale Speicherung der Eingaben und eine serverseitige Instructor-Ansicht. Der Quellcode kann vollständig auf GitHub liegen; die App wird anschließend über **Streamlit Community Cloud** als `*.streamlit.app` veröffentlicht.

## Lokal starten

Mit `uv` (empfohlen):

```bash
uv run python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
```

Danach im Browser öffnen:

```text
http://127.0.0.1:8501
```

Der Streamlit-Prozess bleibt im Terminal aktiv, bis er mit `Ctrl+C` beendet wird. Wenn der Befehl sofort zurückkehrt, zuerst prüfen:

```bash
uv run python -m streamlit version
uv run python -m streamlit hello
```

Für ausführliche Startmeldungen:

```bash
uv run python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --logger.level=debug
```

Ohne konfigurierte Secrets verwendet die App `data/submissions.json`. Dieser Modus ist nur für Entwicklung/Demo gedacht.

Instructor-PIN im lokalen Demo-Modus: `demo`.

## Empfohlenes Deployment

### 1. App-Repository

Dieses Repository kann öffentlich in `ZDDduesseldorf` liegen, z. B.:

```text
ZDDduesseldorf/w4-team-builder-2026
```

### 2. Privates Daten-Repository anlegen

Zum Beispiel:

```text
ZDDduesseldorf/team-builder-data-2026
```

Dieses Repository **privat** lassen und mit einem README initialisieren.

Die App speichert für jede Person eine Datei unter:

```text
submissions/<github-username>.json
```

Dadurch gibt es keine gemeinsame CSV-Datei, die bei gleichzeitigen Eingaben ständig Merge-Konflikte erzeugt.

### 3. Fine-grained GitHub Token

Einen Fine-grained Personal Access Token erstellen, der nur Zugriff auf das Daten-Repository besitzt und dort `Contents: Read and write` darf.

Der Token gehört **nicht** in Git oder in dieses öffentliche Repository.

### 4. Streamlit Secrets

Beim Deployment in Streamlit Community Cloud folgende Secrets setzen:

```toml
instructor_pin = "EIN-LANGER-INSTRUCTOR-PIN"

[github]
token = "github_pat_..."
data_repo = "ZDDduesseldorf/team-builder-data-2026"
branch = "main"
```

Siehe auch `.streamlit/secrets.toml.example`.

### 5. App deployen

In Streamlit Community Cloud das öffentliche GitHub-Repository auswählen und `app.py` als Entrypoint verwenden.

Danach kann die `*.streamlit.app`-URL an die Studierenden verteilt werden.

## Ablauf im Praktikum

1. Studierende öffnen die URL auf ihrem Smartphone/Laptop.
2. Name + GitHub-Username eingeben.
3. Drei verschiedene Rollenwünsche auswählen.
4. Absenden.
5. Instructor öffnet den zweiten Tab und gibt den PIN ein.
6. Abwesende können vor der Einteilung aus der Auswahl entfernt werden.
7. **Teams optimieren** anklicken.
8. Ergebnis prüfen und als CSV herunterladen.

## Datenschutz / organisatorischer Hinweis

Im empfohlenen Setup liegen Namen und Wünsche ausschließlich im privaten Daten-Repository. Das öffentliche App-Repository enthält keine Teilnehmerdaten. Nach Abschluss des Praktikums kann das Daten-Repository gelöscht bzw. geleert werden.

## Anpassung der Rollen

Die Rollennamen stehen in `optimizer.py` in `ROLES`; die Beschreibungen stehen in `app.py` in `ROLE_HELP`.

Die aktuellen Teamregeln sind bewusst auf das W4-Praktikum zugeschnitten. Bei einer Änderung der Rollen sollte auch die Funktion `_base_role_counts()` bzw. die Zusammensetzung der optionalen Slots angepasst werden.
