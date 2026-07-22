from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest
from packaging.version import Version

from flask_ms_entra_auth import __version__


class ReleaseModule(Protocol):
    def verify_version(self, version_text: str) -> Version: ...

    def verify_tag(self, tag: str | None, version: Version) -> None: ...

    def verify_distributions(self, dist_dir: Path, version: Version) -> tuple[Path, Path]: ...

    def main(self, argv: list[str] | None = None) -> int: ...


def release_module() -> ReleaseModule:
    path = Path(__file__).parents[1] / "scripts" / "verify_release.py"
    spec = importlib.util.spec_from_file_location("verify_release", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    assert isinstance(module, ModuleType)
    spec.loader.exec_module(module)
    return cast(ReleaseModule, module)


def write_wheel(
    path: Path,
    *,
    name: str = "flask-ms-entra-auth",
    version: str = "1.0.0",
    duplicate_metadata: bool = False,
) -> None:
    metadata = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "flask_ms_entra_auth-1.0.0.dist-info/METADATA",
            metadata,
        )
        if duplicate_metadata:
            archive.writestr("other.dist-info/METADATA", metadata)


def write_sdist(
    path: Path,
    *,
    name: str = "flask-ms-entra-auth",
    version: str = "1.0.0",
    metadata_path: str = "flask_ms_entra_auth-1.0.0/PKG-INFO",
) -> None:
    payload = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n".encode()
    member = tarfile.TarInfo(metadata_path)
    member.size = len(payload)
    with tarfile.open(path, "w:gz") as archive:
        archive.addfile(member, io.BytesIO(payload))


def test_stable_version_and_tag_contract() -> None:
    module = release_module()
    version = module.verify_version(__version__)
    assert version == Version("1.0.0")
    module.verify_tag("v1.0.0", version)
    module.verify_tag(None, version)


@pytest.mark.parametrize(
    "version",
    ["1.0", "1.0.0rc1", "1.0.0.dev1", "1.0.0.post1", "1.0.0+local", "invalid"],
)
def test_rejects_non_release_versions(version: str) -> None:
    with pytest.raises(ValueError):
        release_module().verify_version(version)


@pytest.mark.parametrize("tag", ["1.0.0", "v1.0", "v1.0.1", "release-v1.0.0"])
def test_rejects_mismatched_release_tags(tag: str) -> None:
    with pytest.raises(ValueError, match="tag"):
        release_module().verify_tag(tag, Version("1.0.0"))


def test_distribution_validation_and_cli(tmp_path: Path) -> None:
    module = release_module()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    wheel = dist_dir / "flask_ms_entra_auth-1.0.0-py3-none-any.whl"
    sdist = dist_dir / "flask_ms_entra_auth-1.0.0.tar.gz"
    write_wheel(wheel)
    write_sdist(sdist)

    selected = module.verify_distributions(dist_dir, Version("1.0.0"))

    assert selected == (wheel, sdist)
    assert module.main(["--tag", "v1.0.0", "--dist-dir", str(dist_dir)]) == 0


def test_distribution_validation_rejects_missing_or_invalid_metadata(
    tmp_path: Path,
) -> None:
    module = release_module()
    with pytest.raises(ValueError, match="exactly one"):
        module.verify_distributions(tmp_path, Version("1.0.0"))

    wheel = tmp_path / "flask_ms_entra_auth-1.0.0-py3-none-any.whl"
    sdist = tmp_path / "flask_ms_entra_auth-1.0.0.tar.gz"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("package/file.py", "")
    write_sdist(sdist)
    with pytest.raises(ValueError, match="metadata"):
        module.verify_distributions(tmp_path, Version("1.0.0"))


def test_distribution_validation_rejects_ambiguous_or_mismatched_artifacts(
    tmp_path: Path,
) -> None:
    module = release_module()
    wheel = tmp_path / "flask_ms_entra_auth-1.0.0-py3-none-any.whl"
    sdist = tmp_path / "flask_ms_entra_auth-1.0.0.tar.gz"

    write_wheel(wheel, duplicate_metadata=True)
    write_sdist(sdist)
    with pytest.raises(ValueError, match="exactly one metadata"):
        module.verify_distributions(tmp_path, Version("1.0.0"))

    write_wheel(wheel)
    write_sdist(sdist, version="1.0.1")
    with pytest.raises(ValueError, match="identity"):
        module.verify_distributions(tmp_path, Version("1.0.0"))

    sdist.write_bytes(b"not-a-tar-archive")
    with pytest.raises(ValueError, match="sdist could not be read"):
        module.verify_distributions(tmp_path, Version("1.0.0"))


def test_cli_failure_is_sanitized(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert release_module().main(["--dist-dir", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "release validation failed" in captured.err


def test_script_executes_from_checkout(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "verify_release.py"),
            "--dist-dir",
            str(tmp_path),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "release validation failed" in result.stderr


def test_release_workflow_has_manual_test_index_and_release_only_production() -> None:
    workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "release.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "release:" in workflow
    assert "environment:\n      name: testpypi" in workflow
    assert "environment:\n      name: pypi" in workflow
    assert "if: github.event_name == 'workflow_dispatch'" in workflow
    assert "if: github.event_name == 'release'" in workflow
    assert workflow.count("id-token: write") == 2
    assert "password:" not in workflow
    assert "PYPI_API_TOKEN" not in workflow
