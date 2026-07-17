# Versionamento e releases

## Esquema

SemVer: `MAJOR.MINOR.PATCH`.

A série `0.x` é experimental. As ETAPAS 03 e 04 formam uma única entrega funcional compatível e elevam a versão de `0.3.0` para `0.4.0`.

## Fonte única

`src/flask_ms_entra_auth/_version.py` é lido pelo Hatchling e exportado como `__version__`.

## Artefatos

- Source distribution;
- Wheel universal Python 3;
- Metadata completa;
- `py.typed`;
- Módulos de identidade, contexto, MSAL e storage;
- Changelog e status.

## Processo de validação

1. Ruff;
2. mypy estrito;
3. pytest e cobertura;
4. Bandit;
5. pip-audit;
6. build isolado;
7. `twine check`;
8. Inspeção de wheel e sdist;
9. Instalação do wheel em ambiente vazio;
10. Smoke test sem rede.

TestPyPI, tag, release e PyPI permanecem fora do escopo atual.
