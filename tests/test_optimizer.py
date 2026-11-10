import random

from optimizer import ROLES, Person, choose_team_sizes, optimize_teams


def people(n: int, seed: int = 42):
    rng = random.Random(seed)
    result = []
    for i in range(n):
        choices = list(ROLES)
        rng.shuffle(choices)
        result.append(Person(f"user{i:03d}", f"Student {i}", tuple(choices[:3])))
    return result


def test_team_sizes_common_cohorts():
    for n in range(4, 80):
        if n == 7:
            continue
        sizes = choose_team_sizes(n)
        assert sum(sizes) == n
        assert all(4 <= s <= 6 for s in sizes)


def test_seven_uses_one_team_of_three():
    sizes = choose_team_sizes(7)
    assert sorted(sizes) == [3, 4]


def test_three_is_allowed():
    assert choose_team_sizes(3) == [3]


def test_optimizer_respects_team_and_role_constraints():
    for n in (7, 8, 9, 10, 11, 12, 17, 23, 31, 47):
        assignments, stats = optimize_teams(people(n, seed=n))
        assert len(assignments) == n
        assert len({a.identifier for a in assignments}) == n
        for team in range(1, stats["teams"] + 1):
            members = [a for a in assignments if a.team == team]
            assert 3 <= len(members) <= 6
            if len(members) != 3:
                assert len(members) >= 4
            roles = [a.role for a in members]
            assert roles.count(ROLES[0]) == 1
            assert roles.count(ROLES[1]) >= 1
            if len(members) == 3:
                assert roles.count(ROLES[2]) >= 1
            else:
                assert roles.count(ROLES[2]) >= 2
            assert roles.count(ROLES[1]) <= 2
            assert roles.count(ROLES[2]) <= 3
            assert roles.count(ROLES[3]) <= 1


def test_all_can_get_first_choice_when_preferences_fit():
    cohort = [
        Person("po1", "PO", (ROLES[0], ROLES[1], ROLES[2])),
        Person("test1", "Test 1", (ROLES[1], ROLES[3], ROLES[0])),
        Person("test2", "Test 2", (ROLES[1], ROLES[0], ROLES[3])),
        Person("dev1", "Dev 1", (ROLES[2], ROLES[1], ROLES[0])),
        Person("dev2", "Dev 2", (ROLES[2], ROLES[3], ROLES[1])),
    ]
    _, stats = optimize_teams(cohort)
    assert stats["first_choices"] == 5
    assert stats["unranked"] == 0


def test_avoids_unranked_role_when_ranked_solution_exists():
    cohort = [
        Person(
            "ggg",
            "Dirk FF",
            (
                ROLES[3],  # Review / Release
                ROLES[2],  # Software Development
                ROLES[1],  # Test Team
            ),
        ),
        Person(
            "ggg22",
            "Peter P",
            (
                ROLES[1],  # Test Team
                ROLES[3],  # Review / Release
                ROLES[2],  # Software Development
            ),
        ),
        Person(
            "ggg224",
            "Beter B",
            (
                ROLES[2],  # Software Development
                ROLES[0],  # Product Owner / Integration
                ROLES[3],  # Review / Release
            ),
        ),
    ]

    assignments, stats = optimize_teams(cohort)
    by_name = {assignment.name: assignment for assignment in assignments}

    assert stats["unranked"] == 0
    assert by_name["Dirk FF"].role == ROLES[2]
    assert by_name["Dirk FF"].preference_rank == 2
    assert by_name["Peter P"].role == ROLES[1]
    assert by_name["Peter P"].preference_rank == 1
    assert by_name["Beter B"].role == ROLES[0]
    assert by_name["Beter B"].preference_rank == 2
