# Versionamento e releases

## Esquema

SemVer: `MAJOR.MINOR.PATCH`.

A série `0.x` é experimental. As ETAPAS 07 e 08 formam uma evolução funcional e elevam a versão de `0.5.0` para `0.6.0`.

## Fonte única

`src/flask_ms_entra_auth/_version.py` é lido pelo Hatchling e exportado como `__version__`.

## Artefatos

- Source distribution;
- Wheel universal Python 3;
- `py.typed`;
- Hooks, observabilidade e auditoria;
- Threat model, ADRs, documentação e testes.

## Processo

1. Ruff;
2. mypy estrito;
3. pytest com 100% de linhas e branches;
4. Bandit;
5. pip-audit;
6. build isolado;
7. `twine check`;
8. inspeção de wheel e sdist;
9. instalação limpa do wheel;
10. smoke test sem rede.

TestPyPI, tag, release e PyPI permanecem fora do escopo.
