from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

import streamlit as st

from config import (
    DEMO_MODE,
    GITHUB_DATA_BRANCH,
    GITHUB_DATA_REPO,
    GITHUB_TOKEN,
    INSTRUCTOR_PIN,
)
from optimizer import Assignment, Person, ROLES, optimize_teams
from storage import GitHubStorage, LocalStorage


st.set_page_config(
    page_title="Tiny Software Engineering Team Builder",
    page_icon="🧩",
    layout="wide",
)


ROLE_HELP = {
    "Product Owner / Integration": (
        "Anforderungen klären, Issues koordinieren, Integration im Blick behalten."
    ),
    "Test Team": (
        "Anforderungen in Tests übersetzen, Randfälle suchen, "
        "Implementierung kritisch prüfen."
    ),
    "Software Development": (
        "Module/Funktionen implementieren und gegen die vereinbarten "
        "Schnittstellen entwickeln."
    ),
    "Review / Release": (
        "Pull Requests, Integration, CI und finale Qualität im Blick behalten."
    ),
}


def get_storage():
    """Return the configured storage backend.

    In demo mode, submissions are stored locally.
    Otherwise, the configured GitHub repository is used.
    """
    if DEMO_MODE:
        return LocalStorage(), "lokal"

    return (
        GitHubStorage(
            token=GITHUB_TOKEN,
            repo=GITHUB_DATA_REPO,
            branch=GITHUB_DATA_BRANCH,
        ),
        "GitHub",
    )


def csv_bytes(
    rows: list[dict[str, object]],
    fields: list[str],
) -> bytes:
    """Convert rows to CSV bytes for download."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8-sig")


def markdown_table(
    rows: list[dict[str, object]],
    columns: list[str],
) -> str:
    """Render a small table without pandas/pyarrow."""

    def cell(value: object) -> str:
        text = str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    body = [
        "| "
        + " | ".join(
            cell(row.get(column, ""))
            for column in columns
        )
        + " |"
        for row in rows
    ]

    return "\n".join(
        [
            header,
            separator,
            *body,
        ]
    )


storage, storage_mode = get_storage()


st.title("Tiny Software Engineering Team Builder")
st.caption(
    "Rollenwünsche sammeln und Teams mit 4–6 Personen "
    "möglichst wunschgerecht zusammenstellen."
)


student_tab, instructor_tab = st.tabs(
    [
        "Studierende",
        "Instructor",
    ]
)


# ---------------------------------------------------------------------
# Student view
# ---------------------------------------------------------------------

with student_tab:
    st.subheader("Deine Rollenwünsche")

    st.write(
        "Bitte wähle drei **verschiedene** Rollen in der Reihenfolge "
        "deiner Präferenz. Die Einteilung versucht zuerst möglichst "
        "viele Erstwünsche, danach Zweit- und Drittwünsche zu erfüllen."
    )

    with st.expander("Was bedeuten die Rollen?"):
        for role in ROLES:
            st.markdown(
                f"**{role}**  \n"
                f"{ROLE_HELP[role]}"
            )

    with st.form("preference_form"):
        name = st.text_input(
            "Name",
            placeholder="Vorname Nachname",
        )

        identifier = st.text_input(
            "GitHub-Username",
            help=(
                "Dient als eindeutiger Schlüssel. "
                "Ein erneutes Absenden aktualisiert deinen Eintrag."
            ),
        )

        first = st.selectbox(
            "1. Wunsch",
            ROLES,
            index=2,
        )

        second = st.selectbox(
            "2. Wunsch",
            ROLES,
            index=1,
        )

        third = st.selectbox(
            "3. Wunsch",
            ROLES,
            index=0,
        )

        submitted = st.form_submit_button(
            "Wünsche speichern",
            type="primary",
        )

    if submitted:
        if not name.strip() or not identifier.strip():
            st.error(
                "Bitte Name und GitHub-Username angeben."
            )

        elif len({first, second, third}) != 3:
            st.error(
                "Bitte drei verschiedene Rollen auswählen."
            )

        else:
            submission = {
                "identifier": identifier.strip(),
                "name": name.strip(),
                "choices": [
                    first,
                    second,
                    third,
                ],
                "submitted_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            try:
                storage.save_submission(submission)
                st.success("Gespeichert. Danke!")

            except Exception as exc:
                st.error(
                    f"Speichern fehlgeschlagen: {exc}"
                )

    if storage_mode == "lokal":
        st.info(
            "Die App läuft im lokalen Demo-Modus. "
            "Einträge werden nur lokal gespeichert und nicht "
            "in das GitHub-Datenrepository geschrieben."
        )


# ---------------------------------------------------------------------
# Instructor view
# ---------------------------------------------------------------------

with instructor_tab:
    st.subheader("Instructor Dashboard")

    pin = st.text_input(
        "Instructor PIN",
        type="password",
    )

    if DEMO_MODE:
        st.warning(
            "Die App läuft im Demo-Modus. "
            "Der Instructor-PIN ist standardmäßig `demo`, "
            "sofern kein anderer `INSTRUCTOR_PIN` gesetzt wurde."
        )

    if pin == INSTRUCTOR_PIN:
        try:
            submissions = storage.list_submissions()

        except Exception as exc:
            st.error(
                "Submissions konnten nicht geladen werden: "
                f"{exc}"
            )
            submissions = []

        st.metric(
            "Abgegebene Präferenzen",
            len(submissions),
        )

        if submissions:
            display_rows = [
                {
                    "Name": submission["name"],
                    "GitHub": submission["identifier"],
                    "1. Wunsch": submission["choices"][0],
                    "2. Wunsch": submission["choices"][1],
                    "3. Wunsch": submission["choices"][2],
                }
                for submission in submissions
            ]

            st.markdown(
                markdown_table(
                    display_rows,
                    [
                        "Name",
                        "GitHub",
                        "1. Wunsch",
                        "2. Wunsch",
                        "3. Wunsch",
                    ],
                )
            )

            all_ids = [
                submission["identifier"]
                for submission in submissions
            ]

            selected_ids = st.multiselect(
                "Anwesende Studierende",
                options=all_ids,
                default=all_ids,
                help=(
                    "Hier können Abwesende vor der "
                    "Teamgenerierung ausgeschlossen werden."
                ),
            )

            if st.button(
                "Teams optimieren",
                type="primary",
            ):
                selected = [
                    submission
                    for submission in submissions
                    if submission["identifier"] in selected_ids
                ]

                people = [
                    Person(
                        identifier=submission["identifier"],
                        name=submission["name"],
                        choices=tuple(
                            submission["choices"]
                        ),
                    )
                    for submission in selected
                ]

                try:
                    assignments, stats = optimize_teams(people)

                    st.session_state["assignments"] = assignments
                    st.session_state["stats"] = stats

                except Exception as exc:
                    st.error(
                        "Teamgenerierung fehlgeschlagen: "
                        f"{exc}"
                    )

        assignments: list[Assignment] = (
            st.session_state.get(
                "assignments",
                [],
            )
        )

        stats = st.session_state.get("stats")

        if assignments and stats:
            st.divider()

            st.subheader("Optimierte Einteilung")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "1. Wunsch",
                stats["first_choices"],
            )

            c2.metric(
                "2. Wunsch",
                stats["second_choices"],
            )

            c3.metric(
                "3. Wunsch",
                stats["third_choices"],
            )

            c4.metric(
                "Nicht gerankt",
                stats["unranked"],
            )

            st.caption(
                "Teamgrößen: "
                + ", ".join(
                    map(
                        str,
                        stats["team_sizes"],
                    )
                )
            )

            teams = sorted(
                {
                    assignment.team
                    for assignment in assignments
                }
            )

            for team in teams:
                st.markdown(
                    f"### Team {team}"
                )

                rows = []

                for assignment in assignments:
                    if assignment.team != team:
                        continue

                    if assignment.preference_rank:
                        rank = (
                            f"{assignment.preference_rank}. Wunsch"
                        )
                    else:
                        rank = "nicht gerankt"

                    rows.append(
                        {
                            "Name": assignment.name,
                            "GitHub": assignment.identifier,
                            "Rolle": assignment.role,
                            "Präferenz": rank,
                        }
                    )

                st.markdown(
                    markdown_table(
                        rows,
                        [
                            "Name",
                            "GitHub",
                            "Rolle",
                            "Präferenz",
                        ],
                    )
                )

            export_rows = [
                {
                    "team": assignment.team,
                    "name": assignment.name,
                    "github": assignment.identifier,
                    "role": assignment.role,
                    "preference_rank": (
                        assignment.preference_rank or ""
                    ),
                }
                for assignment in assignments
            ]

            st.download_button(
                "Team-Einteilung als CSV herunterladen",
                data=csv_bytes(
                    export_rows,
                    [
                        "team",
                        "name",
                        "github",
                        "role",
                        "preference_rank",
                    ],
                ),
                file_name="w4_team_assignment.csv",
                mime="text/csv",
            )

    elif pin:
        st.error("PIN nicht korrekt.")