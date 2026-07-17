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
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = wheel.read(metadata_name).decode()
        assert f"Version: {__version__}" in metadata
        assert "Requires-Python: >=3.11" in metadata
        assert "requires-dist: flask<3.2,>=3.1" in metadata.lower()
        assert "Requires-Dist: msal<2,>=1.37" in metadata

    with tarfile.open(sdists[0], "r:gz") as sdist:
        names = set(sdist.getnames())
        assert any(name.endswith("/src/flask_ms_entra_auth/py.typed") for name in names)
        assert any(name.endswith("/src/flask_ms_entra_auth/config.py") for name in names)
        assert any(name.endswith("/pyproject.toml") for name in names)
        assert any(name.endswith("/tests/test_config.py") for name in names)
