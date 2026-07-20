# Status de implementação

## Etapa atual

ETAPAS 07 e 08 concluídas em conjunto: hooks e hardening.

## Decisões tomadas

### Hooks

- Hooks são registrados na instância, preservam ordem e ignoram duplicidade do mesmo callable;
- `on_authenticated` roda antes da sessão local;
- `AuthenticationRejected` preserva rejeição de domínio;
- Falhas inesperadas de vínculo viram `LocalBindingError`;
- `on_logout` roda depois da limpeza local;
- Falha de logout não recria autenticação removida;
- `on_error` e `on_event` não mascaram o comportamento original;
- Hooks compartilhados entre aplicações que reutilizam a mesma instância foram documentados.

### Observabilidade

- `AuthEvent` é congelado e possui schema fechado;
- Request ID válido é reaproveitado por requisição e valor inválido é substituído;
- Logging é opcional, usa mensagem constante e campos extras normalizados;
- Erros previsíveis notificam observadores uma única vez;
- Tokens, auth code, claims, segredo e payload bruto permanecem excluídos.

### Hardening de storage

- `AtomicAuthStorage.take()` representa consumo único nativo;
- `MemoryStorage.take()` é atômico dentro do processo;
- Fluxo e identidade usam `take()` quando disponível;
- Fallback namespaced é protegido apenas no adaptador local e não promete atomicidade distribuída;
- `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True` bloqueia backend sem capacidade nativa;
- Token cache continua last-write-wins e sem CAS.

### Auditoria

- `audit_security()` é somente leitura;
- Achados verificam secret de sessão, HttpOnly, SameSite, Secure, `MemoryStorage` e consumo atômico;
- `MS_ENTRA_STRICT_SECURITY=True` bloqueia apenas achados de severidade `error`;
- Mensagens de achado não contêm valores de configuração.

## Comandos executados

```bash
python -m pip install -e ".[dev]"
ruff format .
ruff check .
ruff format --check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit . --dry-run
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

Também foram executados parser YAML da CI, instalação do wheel em ambiente virtual limpo e smoke test da API empacotada.

## Resultados

Ambiente local disponível: Linux, Python 3.13.5.

- Instalação editável: aprovada;
- Ruff lint: aprovado;
- Ruff format check: aprovado, 47 arquivos Python formatados;
- mypy estrito: aprovado, 47 arquivos analisados;
- pytest principal: 465 testes aprovados e 1 teste de distribuição ignorado de forma esperada;
- Cobertura: 100% de linhas e branches, 1657 statements e 472 branches;
- Bandit: zero ocorrências em 2638 linhas de código analisadas;
- `pip-audit . --dry-run`: 17 pacotes resolvidos, sem vulnerabilidades reportadas no modo seco;
- `pip-audit .`: consulta externa não concluída porque o sandbox não resolveu `pypi.org`;
- Workflow YAML: válido, com matriz Python 3.11, 3.12, 3.13 e 3.14;
- Build isolado: aprovado;
- Wheel: `flask_ms_entra_auth-0.6.0-py3-none-any.whl`;
- Source distribution: `flask_ms_entra_auth-0.6.0.tar.gz`;
- `twine check`: aprovado para ambos;
- Inspeção de wheel e sdist: aprovada;
- Instalação do wheel em ambiente virtual limpo: aprovada;
- Smoke test de hooks, consumo atômico, auditoria, rotas e versão: aprovado.

## Riscos e limites

- Hooks executam no worker da requisição e podem acrescentar latência;
- Não existe rollback automático de banco ou de efeitos externos;
- `MemoryStorage` perde dados ao reiniciar e não compartilha estado entre workers;
- Atomicidade distribuída depende da implementação real do backend;
- Token cache pode sofrer last-write-wins em concorrência distribuída;
- Causas de exceção podem conter detalhes sensíveis e exigem logging controlado.

## Declaração de escopo

A ETAPA 09 não foi iniciada. Nenhum Redis oficial, integração com template, Microsoft Graph, frontend, Docker, deploy, TestPyPI ou publicação foi implementado.
