# Status de implementação

## Etapa atual

ETAPA 01: configuração.

## Decisões tomadas

- Versão elevada de `0.1.0` para `0.2.0` por adição funcional compatível com a série experimental;
- `init_app()` valida a configuração antes de registrar estado;
- Precedência: argumentos da instância, `app.config` e padrões seguros;
- Argumentos da instância são armazenados sem referência permanente à aplicação;
- Configuração resolvida usa dataclass congelada e exclusiva por aplicação;
- Campos obrigatórios: client ID, client secret, tenant ID e redirect URI;
- Authority padrão derivada de `https://login.microsoftonline.com/<tenant>`;
- Authority customizada exige HTTPS, um único segmento e tenant correspondente;
- Aliases `common`, `organizations` e `consumers` são rejeitados na fase single-tenant;
- Redirect HTTP é permitido somente para loopback;
- Scopes são aparados, deduplicados e armazenados como tupla;
- `MicrosoftEntraAuthError` e `ConfigurationError` fazem parte da API pública;
- Mensagens e representações não incluem o client secret;
- Inicialização idempotente preserva a primeira configuração resolvida;
- Testes e smoke test passaram a consultar a versão pela fonte única, sem valor duplicado;
- Nenhum cliente MSAL, storage, identidade, fluxo ou rota foi criado.

## Comandos executados

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"

.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src tests
.venv/bin/pytest
.venv/bin/bandit -c pyproject.toml -r src
.venv/bin/pip-audit . --dry-run
.venv/bin/pip-audit .

rm -rf dist build .package-venv
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
DIST_DIR=dist .venv/bin/pytest tests/test_distribution.py --no-cov

python -m venv .package-venv
.package-venv/bin/python -m pip install dist/*.whl
```

O workflow também foi carregado por parser YAML e o wheel foi exercitado em ambiente virtual limpo com configuração sintética.

## Resultados

Ambiente local: Linux, Python 3.13.5.

- Instalação editável limpa: aprovada;
- ruff lint: aprovado;
- ruff format check: aprovado, 9 arquivos Python formatados;
- mypy estrito: aprovado, 9 arquivos analisados sem erros;
- pytest principal: 72 testes aprovados e 1 teste de distribuição ignorado de forma esperada;
- Cobertura: 100% de linhas e branches, 149 statements e 42 branches;
- Bandit: aprovado, 264 linhas analisadas e zero ocorrências;
- `pip-audit . --dry-run`: aprovado, 17 pacotes resolvidos;
- `pip-audit .`: consulta externa não concluída por falha de resolução DNS para `pypi.org` no sandbox;
- Build isolado: aprovado;
- Wheel: `flask_ms_entra_auth-0.2.0-py3-none-any.whl`;
- Source distribution: `flask_ms_entra_auth-0.2.0.tar.gz`;
- `twine check`: aprovado para os dois artefatos;
- Inspeção automatizada de wheel e sdist: 1 teste aprovado;
- Inclusão de `config.py`, `errors.py`, `extension.py` e `py.typed`: confirmada;
- Instalação limpa do wheel: aprovada;
- Smoke test da configuração instalada: aprovado;
- Comparação entre metadata instalado e `__version__`: aprovada;
- Workflow YAML: válido, com jobs `tests`, `quality` e `package`.

Versões resolvidas na validação:

- Flask 3.1.3;
- MSAL 1.37.0;
- Hatchling 1.31.0 no build isolado;
- pytest 9.1.1;
- pytest-cov 7.1.0;
- Ruff 0.15.22;
- mypy 2.3.0;
- Bandit 1.9.4;
- pip-audit 2.10.1;
- build 1.4.4;
- twine 6.2.0.

## Riscos

- A política atual é intencionalmente single-tenant e rejeita aliases genéricos;
- Authorities com múltiplos segmentos, B2C ou External ID permanecem fora do contrato;
- O client secret é obrigatório embora o MSAL ainda não seja inicializado, antecipando o contrato de aplicação web confidencial já documentado;
- Alterações diretas em atributos privados da extensão não fazem parte da API suportada.

## Declaração de escopo

Nenhuma funcionalidade de storage, login, callback, logout, token cache, aquisição silenciosa, identidade, `current_identity`, decorators, hooks, Redis, Flask-Login, Microsoft Graph, templates, frontend, Docker, deploy ou publicação foi iniciada.
