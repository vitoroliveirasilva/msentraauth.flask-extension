# Status de implementação

## Etapa atual

ETAPA 02: storage.

## Decisões tomadas

- Versão elevada de `0.2.0` para `0.3.0`;
- `AuthStorage` é um `Protocol` público e verificável em runtime;
- Contrato mínimo permanece `load`, `save` e `delete` com valores binários;
- `MemoryStorage` é fornecido somente para desenvolvimento e testes;
- Cada aplicação recebe backend próprio em memória quando nenhum storage é injetado;
- Backends injetados são acessados por adaptador namespaced;
- Namespace explícito usa `MS_ENTRA_SESSION_NAMESPACE` ou argumento do construtor;
- Namespace padrão é derivado de nome da app, client ID e tenant ID, sem client secret;
- Chaves delegadas usam prefixo `msentra:<namespace>:`;
- TTL aceita inteiro positivo em segundos ou `None`;
- Expiração em memória usa relógio monotônico;
- `delete()` é idempotente;
- Operações em memória usam `RLock`;
- Política de concorrência é last-write-wins;
- Falhas externas são convertidas em `StorageError` com causa preservada;
- Mensagens públicas não repetem chave, valor ou erro bruto do backend;
- Nenhum token, cache MSAL, identidade ou fluxo de autenticação foi criado.

## Comandos

```bash
python -m venv .venv
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

## Riscos

- `MemoryStorage` perde dados ao reiniciar e não compartilha estado entre processos;
- Namespace derivado depende do nome da aplicação, client ID e tenant ID;
- Aplicações distintas que compartilham backend devem definir namespace explícito quando a derivação não representar sua fronteira lógica;
- A política last-write-wins não detecta conflitos;
- Causas de exceções externas podem conter dados sensíveis e não devem ser logadas sem sanitização;
- Token cache e serialização ainda não foram implementados.

## Declaração de escopo

Nenhuma funcionalidade de identidade, `current_identity`, login, callback, logout, token cache MSAL, aquisição silenciosa, decorators, hooks, Redis, Flask-Login, Microsoft Graph, templates, frontend, Docker, deploy ou publicação foi iniciada.