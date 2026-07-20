from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path

import pytest

from flask_ms_entra_auth import __version__


def _dist_dir() -> Path:
    configured = os.environ.get("DIST_DIR")
    if configured is None:
        pytest.skip("set DIST_DIR after running `python -m build`")
    return Path(configured)


@pytest.mark.distribution
def test_build_generated_valid_wheel_and_sdist() -> None:
    dist_dir = _dist_dir()
    wheels = list(dist_dir.glob("flask_ms_entra_auth-*.whl"))
    sdists = list(dist_dir.glob("flask_ms_entra_auth-*.tar.gz"))

    assert len(wheels) == 1
    assert len(sdists) == 1
    assert __version__ in wheels[0].name
    assert __version__ in sdists[0].name

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        assert "flask_ms_entra_auth/py.typed" in names
        assert "flask_ms_entra_auth/config.py" in names
        assert "flask_ms_entra_auth/errors.py" in names
        assert "flask_ms_entra_auth/extension.py" in names
        assert "flask_ms_entra_auth/identity.py" in names
        assert "flask_ms_entra_auth/hooks.py" in names
        assert "flask_ms_entra_auth/observability.py" in names
        assert "flask_ms_entra_auth/security.py" in names
        assert "flask_ms_entra_auth/context.py" in names
        assert "flask_ms_entra_auth/auth/client.py" in names
        assert "flask_ms_entra_auth/auth/flow.py" in names
        assert "flask_ms_entra_auth/auth/service.py" in names
        assert "flask_ms_entra_auth/auth/token_cache.py" in names
        assert "flask_ms_entra_auth/storage/base.py" in names
        assert "flask_ms_entra_auth/storage/memory.py" in names
        assert "flask_ms_entra_auth/storage/namespaced.py" in names
        assert "flask_ms_entra_auth/storage/validation.py" in names
        assert "flask_ms_entra_auth/web/models.py" in names
        assert "flask_ms_entra_auth/web/routes.py" in names
        assert "flask_ms_entra_auth/web/session.py" in names
        assert "flask_ms_entra_auth/web/urls.py" in names
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = wheel.read(metadata_name).decode()
        assert f"Version: {__version__}" in metadata
        assert "Requires-Python: >=3.11" in metadata
        assert "requires-dist: flask<3.2,>=3.1" in metadata.lower()
        assert "Requires-Dist: msal<2,>=1.37" in metadata
        assert "Development Status :: 5 - Production/Stable" in metadata

    with tarfile.open(sdists[0], "r:gz") as sdist:
        names = set(sdist.getnames())
        assert any(name.endswith("/src/flask_ms_entra_auth/py.typed") for name in names)
        assert any(
            name.endswith("/src/flask_ms_entra_auth/config.py") for name in names
        )
        assert any(name.endswith("/pyproject.toml") for name in names)
        assert any(name.endswith("/tests/test_config.py") for name in names)
        assert any(name.endswith("/tests/test_storage.py") for name in names)
        assert any(name.endswith("/tests/test_storage_contract.py") for name in names)
        assert any(name.endswith("/tests/test_identity.py") for name in names)
        assert any(name.endswith("/tests/test_context.py") for name in names)
        assert any(name.endswith("/tests/auth/test_service.py") for name in names)
        assert any(name.endswith("/tests/auth/test_flow.py") for name in names)
        assert any(name.endswith("/tests/test_extension_web.py") for name in names)
        assert any(name.endswith("/tests/test_hooks.py") for name in names)
        assert any(name.endswith("/tests/test_observability.py") for name in names)
        assert any(name.endswith("/tests/test_security.py") for name in names)
        assert any(name.endswith("/tests/test_storage_atomic.py") for name in names)
        assert any(name.endswith("/docs/17_THREAT_MODEL.md") for name in names)
        assert any(name.endswith("/.github/workflows/release.yml") for name in names)
        assert any(name.endswith("/scripts/verify_release.py") for name in names)
        assert any(name.endswith("/tests/test_release.py") for name in names)
        assert any(name.endswith("/docs/18_RELEASE_CHECKLIST.md") for name in names)
        assert any(name.endswith("/docs/19_TESTPYPI_E_PYPI.md") for name in names)
        assert any(
            name.endswith("/docs/decisoes/016_HOOKS_ORDENADOS_E_FALHAS_ISOLADAS.md")
            for name in names
        )
        assert any(
            name.endswith("/docs/decisoes/017_CONSUMO_ATOMICO_AUDITORIA_E_EVENTOS.md")
            for name in names
        )
        assert any(name.endswith("/tests/web/test_routes.py") for name in names)
        assert any(name.endswith("/tests/web/test_session.py") for name in names)
        assert any(name.endswith("/tests/web/test_urls.py") for name in names)
