import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow():
    # BaseLoader preserves GitHub's "on" key instead of YAML 1.1's boolean True.
    return yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )


def test_ci_runs_on_pull_requests_and_the_production_branch():
    config = workflow()
    assert set(config["on"]) == {"push", "pull_request", "workflow_dispatch"}
    assert config["on"]["push"]["branches"] == ["prod"]
    assert config["permissions"] == {"contents": "read"}
    assert config["concurrency"]["cancel-in-progress"] == "true"


def test_actions_are_pinned_and_checkout_does_not_leave_write_credentials():
    for job in workflow()["jobs"].values():
        assert 0 < int(job["timeout-minutes"]) <= 15
        for step in job["steps"]:
            if "uses" not in step:
                continue
            assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", step["uses"])
            if step["uses"].startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] == "false"


def test_backend_ci_does_not_skip_postgres_and_redis_integration():
    backend = workflow()["jobs"]["backend"]
    assert set(backend["services"]) == {"postgres", "redis"}
    assert backend["env"]["TEST_POSTGRES_URL"].startswith("postgresql+asyncpg://")
    assert backend["env"]["TEST_TASKIQ_REDIS_URL"].startswith("redis://127.0.0.1:")
    commands = {step.get("run") for step in backend["steps"]}
    assert "uv sync --locked --dev" in commands
    assert "uv run --no-sync ruff check ." in commands
    assert "uv run --no-sync pytest -q" in commands


def test_frontend_ci_tests_and_builds_locked_dependencies():
    job = workflow()["jobs"]["frontend"]
    assert job["defaults"]["run"]["working-directory"] == "frontend"
    commands = {step.get("run") for step in job["steps"]}
    assert {"npm ci", "npm test", "npm run build"} <= commands


def test_workflow_lint_receives_only_the_workflow_file_without_network_access():
    steps = workflow()["jobs"]["compose"]["steps"]
    command = next(
        step["run"] for step in steps if "actionlint:" in step.get("run", "")
    )
    assert "--network none" in command
    assert (
        "source=${GITHUB_WORKSPACE}/.github/workflows/ci.yml,target=/ci.yml,readonly"
        in command
    )
    assert re.search(r"actionlint:1\.7\.12@sha256:[0-9a-f]{64}", command)
