# Checklist de release

## Pré-condições

- Versão estável `MAJOR.MINOR.PATCH` em `_version.py`;
- Template consumidor validado contra o wheel candidato.

## Gate local

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src tests scripts
pytest
bandit -c pyproject.toml -r src scripts
pip-audit .
rm -rf dist build
python -m build
python -m twine check dist/*
python scripts/verify_release.py
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

## Falha segura

- Não publicar artefato criado localmente fora do gate;
- Não adicionar token estático ao workflow;
- Não ignorar divergência entre tag, metadata e `__version__`;
- Em caso de erro após publicação, lançar nova versão corretiva (pacotes publicados não devem ser substituídos).
