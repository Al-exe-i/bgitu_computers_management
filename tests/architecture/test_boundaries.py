import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_http_endpoints_do_not_import_infrastructure_directly() -> None:
    violations: list[str] = []
    endpoints_dir = PROJECT_ROOT / "api" / "v1" / "endpoints"

    for path in endpoints_dir.glob("*.py"):
        forbidden = sorted(
            module
            for module in imported_modules(path)
            if module.partition(".")[0] in {"repositories", "services"}
        )
        if forbidden:
            violations.append(f"{path.name}: {', '.join(forbidden)}")

    assert violations == [], (
        "HTTP endpoints must call application use cases through dependencies: "
        + "; ".join(violations)
    )


def test_application_layer_does_not_depend_on_framework_or_infrastructure() -> None:
    violations: list[str] = []

    for path in (PROJECT_ROOT / "modules").glob("*/application/*.py"):
        forbidden = sorted(
            module
            for module in imported_modules(path)
            if module.partition(".")[0]
            in {"dependencies", "fastapi", "repositories", "services"}
        )
        if forbidden:
            violations.append(f"{path.relative_to(PROJECT_ROOT)}: {', '.join(forbidden)}")

    assert violations == [], (
        "Application modules must depend on ports, not adapters: "
        + "; ".join(violations)
    )
