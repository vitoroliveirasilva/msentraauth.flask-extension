# Versionamento e releases

## Esquema

SemVer: `MAJOR.MINOR.PATCH`.

A série `0.x` é experimental. As ETAPAS 05 e 06 formam uma única evolução funcional e elevam a versão de `0.4.0` para `0.5.0`.

## Fonte única

`src/flask_ms_entra_auth/_version.py` é lido pelo Hatchling e exportado como `__version__`.

## Artefatos

- Source distribution;
- Wheel universal Python 3;
- `py.typed`;
- Módulos de fluxo e web;
- Documentação, ADRs e testes.

## Processo de validação

1. Ruff;
2. mypy estrito;
3. pytest e cobertura;
4. Bandit;
5. pip-audit;
6. build isolado;
7. `twine check`;
8. Inspeção de wheel e sdist;
9. Instalação limpa do wheel;
10. Smoke test sem rede.

TestPyPI, tag, release e PyPI permanecem fora do escopo.
