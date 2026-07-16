# Versionamento e releases

## Esquema

SemVer: `MAJOR.MINOR.PATCH`.

## Artefatos

- Source distribution;
- Wheel;
- Metadata completa;
- `py.typed`;
- Changelog e release notes.

## Processo planejado

1. Suíte completa;
2. Build limpo;
3. `twine check`;
4. Instalação em ambiente vazio;
5. TestPyPI;
6. Template consumidor;
7. Tag;
8. PyPI;
9. Release notes.

## Branches

- `dev`: evolução;
- `prod`: estado estável.
