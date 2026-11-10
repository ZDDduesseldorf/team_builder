# Software Engineering Team Builder

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
