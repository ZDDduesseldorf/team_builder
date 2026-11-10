import os


def get_required_env(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


DEMO_MODE = os.environ.get("TEAM_BUILDER_DEMO", "false").lower() in {
    "1",
    "true",
    "yes",
}

if DEMO_MODE:
    INSTRUCTOR_PIN = os.environ.get("INSTRUCTOR_PIN", "demo")

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_DATA_REPO = os.environ.get("GITHUB_DATA_REPO")
    GITHUB_DATA_BRANCH = os.environ.get("GITHUB_DATA_BRANCH", "main")
else:
    INSTRUCTOR_PIN = get_required_env("INSTRUCTOR_PIN")
    GITHUB_TOKEN = get_required_env("GITHUB_TOKEN")
    GITHUB_DATA_REPO = get_required_env("GITHUB_DATA_REPO")
    GITHUB_DATA_BRANCH = os.environ.get("GITHUB_DATA_BRANCH", "main")