from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from zipfile import ZipFile

from packaging.version import InvalidVersion, Version

from flask_ms_entra_auth import __version__

_TAG_RE = re.compile(r"^v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$")


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
    # Exije exatamente um wheel e uma distribuição de origem para a versão
    wheel_pattern = f"flask_ms_entra_auth-{version}-*.whl"
    sdist_pattern = f"flask_ms_entra_auth-{version}.tar.gz"
    wheels = sorted(dist_dir.glob(wheel_pattern))
    sdists = sorted(dist_dir.glob(sdist_pattern))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("dist must contain exactly one matching wheel and one matching sdist")

    with ZipFile(wheels[0]) as wheel:
        metadata_name = next(
            (name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")),
            None,
        )
        if metadata_name is None:
            raise ValueError("wheel metadata is missing")
        metadata = wheel.read(metadata_name).decode("utf-8")
        if f"Version: {version}" not in metadata:
            raise ValueError("wheel metadata version does not match")
    return wheels[0], sdists[0]


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
    except (OSError, ValueError, StopIteration) as exc:
        print(f"release validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"release validation passed: {wheel.name}, {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
