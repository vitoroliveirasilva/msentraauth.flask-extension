# Versionamento e releases

## Esquema

A versão `1.0.0` estabelece o primeiro contrato público estável e mudanças incompatíveis exigem nova versão major.

## Fonte única

`src/flask_ms_entra_auth/_version.py` é lido pelo Hatchling, exportado como `__version__` e comparado ao metadata instalado.

## Gate

1. Ruff;
2. mypy estrito;
3. pytest com 100% de linhas e branches;
4. Bandit e pip-audit;
5. Build isolado;
6. `twine check`;
7. Inspeção de wheel e sdist;
8. `scripts/verify_release.py`;
9. Instalação limpa do wheel;
10. Validação do template consumidor.

## Publicação

- TestPyPI: execução manual do workflow `Release`;
- PyPI: publicação de GitHub Release com tag `vMAJOR.MINOR.PATCH`;
- Credencial: Trusted Publishing por OIDC;
- Artefato: a mesma dupla de wheel e sdist atravessa todos os jobs;

Consulte [Checklist de release](18_RELEASE_CHECKLIST.md) e [TestPyPI/PyPI](19_TESTPYPI_E_PYPI.md).
