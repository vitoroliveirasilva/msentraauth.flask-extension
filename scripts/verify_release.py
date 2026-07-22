from __future__ import annotations

import argparse
import re
import sys
import tarfile
from pathlib import Path
from zipfile import BadZipFile, LargeZipFile, ZipFile

from packaging.version import InvalidVersion, Version

from flask_ms_entra_auth import __version__

_TAG_RE = re.compile(r"^v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$")
_PROJECT_NAME = "flask-ms-entra-auth"
_MAX_METADATA_BYTES = 1_048_576


def verify_version(version_text: str) -> Version:
    # Requer uma versão pública estável, normalizada e de três componentes
    try:
        version = Version(version_text)
    except InvalidVersion as exc:
        raise ValueError("package version is not PEP 440 compatible") from exc
    if version.is_prerelease or version.is_devrelease or version.is_postrelease or version.local:
        raise ValueError("release version must be a stable public version")
    if len(version.release) != 3 or str(version) != version_text:
        raise ValueError("release version must use normalized MAJOR.MINOR.PATCH")
    return version


def verify_tag(tag: str | None, version: Version) -> None:
    # Exige que as tags de lançamento correspondam exatamente à versão do pacote
    if tag is None:
        return
    matched = _TAG_RE.fullmatch(tag)
    if matched is None or matched.group("version") != str(version):
        raise ValueError("release tag must be exactly v<package-version>")


def verify_distributions(dist_dir: Path, version: Version) -> tuple[Path, Path]:
    # Exige exatamente um wheel e uma distribuição de origem válidos para a versão
    wheel_pattern = f"flask_ms_entra_auth-{version}-*.whl"
    sdist_pattern = f"flask_ms_entra_auth-{version}.tar.gz"
    wheels = sorted(dist_dir.glob(wheel_pattern))
    sdists = sorted(dist_dir.glob(sdist_pattern))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("dist must contain exactly one matching wheel and one matching sdist")

    _verify_wheel_metadata(wheels[0], version)
    _verify_sdist_metadata(sdists[0], version)
    return wheels[0], sdists[0]


def _verify_wheel_metadata(wheel_path: Path, version: Version) -> None:
    try:
        with ZipFile(wheel_path) as wheel:
            metadata_names = [
                name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_names) != 1:
                raise ValueError("wheel must contain exactly one metadata file")
            info = wheel.getinfo(metadata_names[0])
            if info.file_size > _MAX_METADATA_BYTES:
                raise ValueError("wheel metadata exceeds the supported size")
            metadata = wheel.read(info)
    except (BadZipFile, LargeZipFile, OSError) as exc:
        raise ValueError("wheel could not be read") from exc
    _verify_core_metadata(metadata, version, artifact="wheel")


def _verify_sdist_metadata(sdist_path: Path, version: Version) -> None:
    expected_name = f"flask_ms_entra_auth-{version}/PKG-INFO"
    try:
        with tarfile.open(sdist_path, mode="r:gz") as sdist:
            metadata = _read_sdist_metadata(sdist, expected_name)
    except (OSError, tarfile.ReadError) as exc:
        raise ValueError("sdist could not be read") from exc
    _verify_core_metadata(metadata, version, artifact="sdist")


def _read_sdist_metadata(sdist: tarfile.TarFile, expected_name: str) -> bytes:
    matches = []
    for member in sdist:
        if member.isfile() and member.name == expected_name:
            matches.append(member)
    if len(matches) != 1:
        raise ValueError("sdist must contain exactly one root metadata file")

    member = matches[0]
    if member.size > _MAX_METADATA_BYTES:
        raise ValueError("sdist metadata exceeds the supported size")
    extracted = sdist.extractfile(member)
    if extracted is None:
        raise ValueError("sdist metadata could not be read")
    return extracted.read(_MAX_METADATA_BYTES + 1)


def _verify_core_metadata(payload: bytes, version: Version, *, artifact: str) -> None:
    if len(payload) > _MAX_METADATA_BYTES:
        raise ValueError(f"{artifact} metadata exceeds the supported size")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{artifact} metadata is not valid UTF-8") from exc

    name = _single_metadata_value(text, "Name")
    metadata_version = _single_metadata_value(text, "Version")
    if name != _PROJECT_NAME or metadata_version != str(version):
        raise ValueError(f"{artifact} metadata identity does not match")


def _single_metadata_value(metadata: str, field: str) -> str:
    prefix = f"{field}:"
    values = [
        line[len(prefix) :].strip() for line in metadata.splitlines() if line.startswith(prefix)
    ]
    if len(values) != 1 or not values[0]:
        raise ValueError(f"artifact metadata must contain exactly one {field} field")
    return values[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag")
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        version = verify_version(__version__)
        verify_tag(args.tag, version)
        wheel, sdist = verify_distributions(args.dist_dir, version)
    except (OSError, ValueError) as exc:
        print(f"release validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"release validation passed: {wheel.name}, {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
