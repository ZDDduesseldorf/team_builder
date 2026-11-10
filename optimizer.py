"""Team and role assignment optimizer for the W4 software engineering lab.

The optimization is deliberately dependency-free. Students rank three of four roles.
The optimizer first chooses balanced team sizes, then assigns roles globally.
Assignments outside a person's three ranked roles are avoided whenever a fully
ranked solution is feasible. Among equally feasible ranked solutions, lower
preference ranks are preferred. Finally, people are placed into teams while
respecting per-team role constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Iterable

ROLES = (
    "Product Owner / Integration",
    "Test Team",
    "Software Development",
    "Review / Release",
)


@dataclass(frozen=True)
class Person:
    identifier: str
    name: str
    choices: tuple[str, str, str]


@dataclass(frozen=True)
class Assignment:
    identifier: str
    name: str
    team: int
    role: str
    preference_rank: int | None


@dataclass
class _Edge:
    to: int
    rev: int
    cap: int
    cost: int
    original_cap: int


def choose_team_sizes(n: int) -> list[int]:
    """Choose team sizes close to five, with 4..6 members whenever possible.

    If no such partition exists, one team of three is allowed. Fewer than three
    participants cannot be assigned.
    """
    if n < 3:
        raise ValueError("At least three participants are required.")

    feasible: list[tuple[float, int, list[int]]] = []
    for teams in range(1, n + 1):
        if 4 * teams <= n <= 6 * teams:
            q, r = divmod(n, teams)
            sizes = [q + 1] * r + [q] * (teams - r)
            if all(4 <= size <= 6 for size in sizes):
                feasible.append((abs(n / teams - 5.0), teams, sorted(sizes, reverse=True)))

    if feasible:
        # Prefer average size closest to five; on ties prefer fewer teams.
        return min(feasible, key=lambda x: (x[0], x[1]))[2]

    # Fallback: exactly one team of three and all other teams between four and six.
    if n == 3:
        return [3]

    feasible_fallback: list[tuple[float, int, list[int]]] = []
    for teams in range(2, n + 1):
        remaining = n - 3
        other_teams = teams - 1
        if 4 * other_teams <= remaining <= 6 * other_teams:
            q, r = divmod(remaining, other_teams)
            other_sizes = [q + 1] * r + [q] * (other_teams - r)
            sizes = sorted(other_sizes + [3], reverse=True)
            feasible_fallback.append((abs(n / teams - 5.0), teams, sizes))

    if not feasible_fallback:
        raise ValueError(f"Cannot construct valid teams for {n} participants.")
    return min(feasible_fallback, key=lambda x: (x[0], x[1]))[2]


def _base_role_counts(team_sizes: list[int]) -> dict[str, int]:
    normal = sum(size >= 4 for size in team_sizes)
    three = sum(size == 3 for size in team_sizes)
    return {
        ROLES[0]: len(team_sizes),
        ROLES[1]: len(team_sizes),
        ROLES[2]: 2 * normal + three,
        ROLES[3]: 0,
    }


def _optional_capacity(team_sizes: list[int]) -> tuple[int, int]:
    """Return (number of optional slots, max extras per optional role)."""
    extras = sum(max(0, size - 4) for size in team_sizes)
    active_teams = sum(size >= 5 for size in team_sizes)
    return extras, active_teams


def _feasible_role_totals(team_sizes: list[int]) -> list[dict[str, int]]:
    base = _base_role_counts(team_sizes)
    extras, active = _optional_capacity(team_sizes)
    totals: list[dict[str, int]] = []

    # Each size-5/6 team can add at most one extra Test, Dev, or Reviewer slot.
    for extra_test in range(active + 1):
        for extra_dev in range(active + 1):
            extra_review = extras - extra_test - extra_dev
            if 0 <= extra_review <= active:
                totals.append(
                    {
                        ROLES[0]: base[ROLES[0]],
                        ROLES[1]: base[ROLES[1]] + extra_test,
                        ROLES[2]: base[ROLES[2]] + extra_dev,
                        ROLES[3]: extra_review,
                    }
                )
    return totals


def _add_edge(graph: list[list[_Edge]], u: int, v: int, cap: int, cost: int) -> _Edge:
    fwd = _Edge(v, len(graph[v]), cap, cost, cap)
    rev = _Edge(u, len(graph[u]), 0, -cost, 0)
    graph[u].append(fwd)
    graph[v].append(rev)
    return fwd


def _rank(person: Person, role: str) -> int | None:
    try:
        return person.choices.index(role) + 1
    except ValueError:
        return None


def _role_assignment(
    people: list[Person], team_sizes: list[int]
) -> tuple[int, dict[str, str], dict[str, int]]:
    """Assign every participant to a role in one min-cost-flow run.

    Role minima are represented by strongly rewarded mandatory capacity on the
    role-to-sink edges. Because every participant can be assigned to every role,
    these minima are always feasible.

    Preference costs are chosen so that reducing the number of unranked
    assignments always dominates any improvement among ranked assignments. This
    means an unranked role is used only when the role constraints make it
    unavoidable. With the same number of unranked assignments, the optimizer
    then prefers 1st choices over 2nd choices and 2nd choices over 3rd choices.
    """
    n = len(people)
    source = 0
    person_start = 1
    role_start = person_start + n
    sink = role_start + len(ROLES)
    graph: list[list[_Edge]] = [[] for _ in range(sink + 1)]

    # Minimize dissatisfaction rather than maximizing first-choice rewards.
    #
    # A single unranked assignment costs more than the maximum possible ranked
    # dissatisfaction of the entire cohort. Therefore, any solution with fewer
    # unranked assignments always wins if it satisfies the same hard role
    # constraints.
    ranked_penalty = {
        1: 0,
        2: 1,
        3: 3,
    }
    unranked_penalty = n * max(ranked_penalty.values()) + 1
    preference_cost = {
        1: ranked_penalty[1],
        2: ranked_penalty[2],
        3: ranked_penalty[3],
        None: unranked_penalty,
    }

    person_role_edges: dict[tuple[int, str], _Edge] = {}
    for i, person in enumerate(people):
        pnode = person_start + i
        _add_edge(graph, source, pnode, 1, 0)
        for r_index, role in enumerate(ROLES):
            rnode = role_start + r_index
            person_role_edges[(i, role)] = _add_edge(
                graph, pnode, rnode, 1, preference_cost[_rank(person, role)]
            )

    base = _base_role_counts(team_sizes)
    _, active = _optional_capacity(team_sizes)
    upper = {
        ROLES[0]: base[ROLES[0]],
        ROLES[1]: base[ROLES[1]] + active,
        ROLES[2]: base[ROLES[2]] + active,
        ROLES[3]: active,
    }

    # Filling every required minimum must dominate every possible preference gain.
    mandatory_bonus = 10 * (n + 1) ** 4
    for r_index, role in enumerate(ROLES):
        rnode = role_start + r_index
        if base[role]:
            _add_edge(graph, rnode, sink, base[role], -mandatory_bonus)
        optional = upper[role] - base[role]
        if optional:
            _add_edge(graph, rnode, sink, optional, 0)

    flow = 0
    cost = 0
    nodes = len(graph)
    while flow < n:
        dist = [10**40] * nodes
        prev_v = [-1] * nodes
        prev_e = [-1] * nodes
        in_queue = [False] * nodes
        dist[source] = 0
        q: deque[int] = deque([source])
        in_queue[source] = True

        while q:
            u = q.popleft()
            in_queue[u] = False
            for ei, edge in enumerate(graph[u]):
                if edge.cap <= 0:
                    continue
                nd = dist[u] + edge.cost
                if nd < dist[edge.to]:
                    dist[edge.to] = nd
                    prev_v[edge.to] = u
                    prev_e[edge.to] = ei
                    if not in_queue[edge.to]:
                        q.append(edge.to)
                        in_queue[edge.to] = True

        if prev_v[sink] == -1:
            raise RuntimeError("No feasible role assignment found.")

        v = sink
        while v != source:
            u = prev_v[v]
            edge = graph[u][prev_e[v]]
            edge.cap -= 1
            graph[v][edge.rev].cap += 1
            v = u
        flow += 1
        cost += dist[sink]

    assigned: dict[str, str] = {}
    totals = {role: 0 for role in ROLES}
    for i, person in enumerate(people):
        for role in ROLES:
            edge = person_role_edges[(i, role)]
            if edge.original_cap == 1 and edge.cap == 0:
                assigned[person.identifier] = role
                totals[role] += 1
                break

    # Defensive check that all mandatory role minima were actually met.
    if any(totals[role] < base[role] for role in ROLES):
        raise RuntimeError("Internal optimizer error: required role minimum not met.")

    return cost, assigned, totals


def _allocate_optional_roles(
    team_sizes: list[int], role_totals: dict[str, int]
) -> list[dict[str, int]]:
    """Turn global role totals into valid per-team role compositions."""
    compositions: list[dict[str, int]] = []
    for size in team_sizes:
        if size == 3:
            compositions.append({ROLES[0]: 1, ROLES[1]: 1, ROLES[2]: 1, ROLES[3]: 0})
        else:
            compositions.append({ROLES[0]: 1, ROLES[1]: 1, ROLES[2]: 2, ROLES[3]: 0})

    base = _base_role_counts(team_sizes)
    extras_needed = {
        role: role_totals[role] - base[role]
        for role in (ROLES[1], ROLES[2], ROLES[3])
    }

    # Small max-flow: teams -> optional roles. A team can use a role at most once.
    active = [i for i, size in enumerate(team_sizes) if size >= 5]
    source = 0
    team_start = 1
    role_start = team_start + len(active)
    sink = role_start + 3
    graph: list[list[_Edge]] = [[] for _ in range(sink + 1)]
    team_role_edges: dict[tuple[int, str], _Edge] = {}

    for local_i, team_i in enumerate(active):
        demand = team_sizes[team_i] - 4
        _add_edge(graph, source, team_start + local_i, demand, 0)
        for r_i, role in enumerate((ROLES[1], ROLES[2], ROLES[3])):
            team_role_edges[(team_i, role)] = _add_edge(
                graph, team_start + local_i, role_start + r_i, 1, 0
            )

    for r_i, role in enumerate((ROLES[1], ROLES[2], ROLES[3])):
        _add_edge(graph, role_start + r_i, sink, extras_needed[role], 0)

    required = sum(team_sizes[i] - 4 for i in active)
    flow = 0
    while flow < required:
        prev: list[tuple[int, int] | None] = [None] * len(graph)
        q: deque[int] = deque([source])
        prev[source] = (-1, -1)
        while q and prev[sink] is None:
            u = q.popleft()
            for ei, edge in enumerate(graph[u]):
                if edge.cap > 0 and prev[edge.to] is None:
                    prev[edge.to] = (u, ei)
                    q.append(edge.to)
        if prev[sink] is None:
            raise RuntimeError("Could not distribute role slots across teams.")
        v = sink
        while v != source:
            u, ei = prev[v]  # type: ignore[misc]
            edge = graph[u][ei]
            edge.cap -= 1
            graph[v][edge.rev].cap += 1
            v = u
        flow += 1

    for (team_i, role), edge in team_role_edges.items():
        if edge.original_cap == 1 and edge.cap == 0:
            compositions[team_i][role] += 1

    return compositions


def optimize_teams(people: Iterable[Person]) -> tuple[list[Assignment], dict[str, object]]:
    people = list(people)
    if len({p.identifier.lower() for p in people}) != len(people):
        raise ValueError("Participant identifiers must be unique.")
    for person in people:
        if len(person.choices) != 3 or len(set(person.choices)) != 3:
            raise ValueError(f"{person.name}: exactly three distinct preferences are required.")
        if any(choice not in ROLES for choice in person.choices):
            raise ValueError(f"{person.name}: unknown role in preferences.")

    team_sizes = choose_team_sizes(len(people))
    _, best_roles, best_totals = _role_assignment(people, team_sizes)
    compositions = _allocate_optional_roles(team_sizes, best_totals)

    # Fill each team's role slots. Within a role, distribute less-satisfied people
    # first to the currently most-satisfied teams to avoid concentrating compromises.
    team_members: list[list[tuple[Person, str, int | None]]] = [[] for _ in team_sizes]
    team_penalty = [0] * len(team_sizes)

    people_by_role: dict[str, list[Person]] = {role: [] for role in ROLES}
    for person in people:
        people_by_role[best_roles[person.identifier]].append(person)

    def penalty(person: Person, role: str) -> int:
        rank = _rank(person, role)
        return {1: 0, 2: 1, 3: 3, None: 8}[rank]

    for role in ROLES:
        role_people = sorted(
            people_by_role[role],
            key=lambda p: (-penalty(p, role), p.identifier.lower()),
        )
        slots: list[int] = []
        for team_i, composition in enumerate(compositions):
            slots.extend([team_i] * composition[role])

        for person in role_people:
            # Choose among teams that still need this role.
            candidate_teams = sorted(set(slots), key=lambda t: (team_penalty[t], t))
            team_i = candidate_teams[0]
            slots.remove(team_i)
            rank = _rank(person, role)
            team_members[team_i].append((person, role, rank))
            team_penalty[team_i] += penalty(person, role)

    assignments: list[Assignment] = []
    for team_i, members in enumerate(team_members, start=1):
        for person, role, rank in sorted(members, key=lambda x: (ROLES.index(x[1]), x[0].name.lower())):
            assignments.append(
                Assignment(
                    identifier=person.identifier,
                    name=person.name,
                    team=team_i,
                    role=role,
                    preference_rank=rank,
                )
            )

    ranks = [a.preference_rank for a in assignments]
    stats = {
        "participants": len(people),
        "teams": len(team_sizes),
        "team_sizes": team_sizes,
        "first_choices": sum(r == 1 for r in ranks),
        "second_choices": sum(r == 2 for r in ranks),
        "third_choices": sum(r == 3 for r in ranks),
        "unranked": sum(r is None for r in ranks),
        "role_totals": best_totals,
    }
    return assignments, stats
