# Status de implementação

## Etapa atual

ETAPA 00: fundação executável, empacotamento, qualidade e CI mínima.

## Decisões tomadas

- Python mínimo 3.11;
- Matriz de CI 3.11, 3.12, 3.13 e 3.14;
- Hatchling como backend;
- `build>=1.4.4,<1.5`, evitando a versão 1.5.1 retirada do índice durante a resolução;
- Estrutura `src`;
- Flask `>=3.1,<3.2`;
- MSAL `>=1.37,<2`, declarado mas não importado ou inicializado;
- Estado específico em `app.extensions["ms_entra_auth"]`;
- Instância da extensão sem `self.app`;
- Duplicidade idempotente para a mesma instância e erro para instância diferente;
- 100% de cobertura de linhas e branches exigida para o núcleo da fundação;
- CI separada em matriz de testes, qualidade e empacotamento.

## Comandos

```bash
python3.13 -m venv /tmp/msentra-pip-venv
/tmp/msentra-pip-venv/bin/python -m pip install --upgrade pip
/tmp/msentra-pip-venv/bin/python -m pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy src tests
DIST_DIR=dist pytest
bandit -c pyproject.toml -r src
pip-audit . --dry-run
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov

python3.13 -m venv .package-venv
.package-venv/bin/python -m pip install dist/*.whl
```

## Riscos

- O ambiente local disponível possui Python 3.13 e as demais versões são cobertas pela configuração de CI, mas não foram executadas localmente;
- MSAL está declarado como dependência planejada, embora nenhum fluxo seja usado na ETAPA 00.

## Declaração de escopo

Nenhuma funcionalidade de login, callback, logout, token cache, aquisição silenciosa, storage, identidade, decorators, hooks, Redis, Flask-Login, Graph, templates, frontend, Docker, deploy ou publicação foi iniciada.
