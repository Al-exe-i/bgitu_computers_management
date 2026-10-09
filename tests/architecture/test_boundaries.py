import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = path.relative_to(PROJECT_ROOT).parts[:-1]
                module = ".".join(
                    (*package[: len(package) - node.level + 1], module)
                ).rstrip(".")
            imports.add(module)
            imports.update(f"{module}.{alias.name}" for alias in node.names)
    return imports


def test_http_endpoints_do_not_import_infrastructure_directly() -> None:
    violations: list[str] = []
    endpoints_dir = PROJECT_ROOT / "api" / "v1" / "endpoints"

    for path in endpoints_dir.glob("*.py"):
        forbidden = sorted(
            module
            for module in imported_modules(path)
            if module.partition(".")[0] in {"repositories", "services"}
            or (
                module.startswith("modules.")
                and len(module.split(".")) > 2
                and module.split(".")[2]
                in {"models", "repositories", "services", "adapters"}
            )
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
            violations.append(
                f"{path.relative_to(PROJECT_ROOT)}: {', '.join(forbidden)}"
            )

    assert violations == [], (
        "Application modules must depend on ports, not adapters: "
        + "; ".join(violations)
    )


def assert_no_imports(paths, forbidden) -> None:
    violations = []
    for path in paths:
        for module in imported_modules(path):
            if any(
                module == prefix or module.startswith(prefix + ".")
                for prefix in forbidden
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}: {module}")
    assert not violations, "Forbidden dependencies:\n" + "\n".join(sorted(violations))


@pytest.mark.parametrize(
    "module_name, enum_file",
    [
        ("identity", "roles.py"),
        ("inventory", "types.py"),
        ("notifications", "schemas.py"),
        ("administration", "schemas.py"),
    ],
)
def test_application_and_contracts_are_infrastructure_free(
    module_name, enum_file
) -> None:
    identity = PROJECT_ROOT / "modules" / module_name
    paths = [*identity.glob("application/**/*.py"), *identity.glob("schemas/*.py")]
    paths += list(identity.glob("*contracts.py"))
    paths += [
        identity / name for name in ("public.py", enum_file, "contracts.py", "ports.py")
    ]
    assert_no_imports(
        paths,
        (
            "sqlalchemy",
            "fastapi",
            "redis",
            "db",
            "models",
            "dependencies",
            "repositories",
            "services",
            "modules.identity.models",
            "modules.identity.repositories",
            "modules.identity.services",
            "modules.identity.adapters",
            "modules.inventory.models",
            "modules.inventory.repositories",
            "modules.inventory.services",
            "modules.inventory.adapters",
            "modules.notifications.models",
            "modules.notifications.repositories",
            "modules.notifications.services",
            "modules.administration.models",
            "modules.administration.repositories",
            "modules.administration.services",
            "modules.administration.adapters",
        ),
    )


def test_identity_repositories_do_not_manage_cache_passwords_or_transactions() -> None:
    assert_no_imports(
        (PROJECT_ROOT / "modules/identity/repositories").glob("*.py"),
        (
            "redis",
            "core.security",
            "db.post_commit",
            "db.transaction",
            "modules.identity.adapters",
            "modules.identity.services",
            "utils.tokens",
        ),
    )


@pytest.mark.parametrize(
    "module_name", ["identity", "inventory", "notifications", "administration"]
)
def test_other_business_modules_use_only_public_contracts(module_name) -> None:
    roots = ("modules", "services", "repositories", "schemas", "utils")
    violations = []
    for root in roots:
        for path in (PROJECT_ROOT / root).rglob("*.py"):
            if path.is_relative_to(PROJECT_ROOT / "modules" / module_name):
                continue
            for module in imported_modules(path):
                if module.startswith(f"modules.{module_name}.") and not (
                    module == f"modules.{module_name}.public"
                    or module.startswith(f"modules.{module_name}.public.")
                ):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}: {module}")
    assert not violations, "Module internals are private:\n" + "\n".join(
        sorted(violations)
    )


@pytest.mark.parametrize(
    "module_name", ["inventory", "notifications", "administration"]
)
def test_repositories_do_not_manage_services_or_transactions(module_name):
    paths = list((PROJECT_ROOT / "modules" / module_name / "repositories").glob("*.py"))
    assert_no_imports(
        paths,
        (
            "redis",
            "db.post_commit",
            "db.transaction",
            "services",
            "dependencies",
            "modules.inventory.services",
            "modules.inventory.adapters",
            "modules.notifications.services",
            "modules.administration.services",
            "modules.administration.adapters",
        ),
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"commit", "rollback"}
            for node in ast.walk(tree)
        ), str(path)


def test_old_inventory_implementations_are_removed():
    names = ("audience", "hardware", "hardware_file", "office", "spec_template")
    obsolete = [f"models/{name}.py" for name in names]
    obsolete += [
        f"schemas/{name}.py" for name in (*names, "analytics", "specifications")
    ]
    obsolete += [
        f"services/{name}_service.py"
        for name in (*names, "analytics", "audience_grid", "hardware_file_streaming")
    ]
    obsolete += [
        f"repositories/{name}_repo.py"
        for name in (
            "audience",
            "hardware",
            "hw_files",
            "office",
            "spec_template",
            "analytics",
        )
    ]
    obsolete += [
        f"utils/{name}.py" for name in ("hw_specs", "grid_utils", "audience_landmarks")
    ]
    obsolete.append("services/cache_invalidation.py")
    assert not [path for path in obsolete if (PROJECT_ROOT / path).exists()]


def test_cli_entry_points_do_not_access_models_or_services_directly():
    assert_no_imports(
        [
            PROJECT_ROOT / "management/users.py",
            PROJECT_ROOT / "management/bootstrap.py",
        ],
        (
            "sqlalchemy",
            "models",
            "repositories",
            "services",
            "modules.identity.models",
            "modules.identity.repositories",
            "modules.identity.services",
            "modules.inventory.models",
            "modules.inventory.repositories",
            "modules.inventory.services",
        ),
    )


def test_old_identity_implementations_are_removed() -> None:
    obsolete = (
        "services/auth_service.py",
        "services/user_service.py",
        "services/user_cache.py",
        "services/user_session_service.py",
        "services/invite_service.py",
        "services/avatar_storage.py",
        "repositories/user_repo.py",
        "repositories/user_session_repo.py",
        "repositories/invite_repo.py",
        "models/user.py",
        "models/user_session.py",
        "models/invite_link.py",
        "models/used_refresh_token.py",
        "schemas/user.py",
        "schemas/user_session.py",
        "schemas/invite.py",
        "models/base.py",
    )
    assert not [path for path in obsolete if (PROJECT_ROOT / path).exists()]


def test_old_notification_implementations_are_removed():
    obsolete = (
        "services/realtime_notification_service.py",
        "services/notification_subscription_service.py",
        "repositories/notification_subscription_repo.py",
        "models/notification_subscription.py",
        "schemas/notification.py",
    )
    assert not [path for path in obsolete if (PROJECT_ROOT / path).exists()]
