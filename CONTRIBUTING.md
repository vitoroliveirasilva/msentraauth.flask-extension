# Contribuindo

## Ambiente pretendido

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Validação obrigatória

```bash
ruff check .
ruff format --check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

## Branches

- `dev`: desenvolvimento;
- `prod`: estado estável.

## Padrões

- Python 3.11 ou superior;
- Código tipado e mypy em modo estrito;
- Application factory;
- Estado por aplicação em `app.extensions`;
- Nenhuma credencial em código ou testes;
- Testes de sucesso e falha;
- API pública documentada;
- Comentários explicam decisões, não repetem o código;
- Changelog e status atualizados no mesmo conjunto de mudanças.
