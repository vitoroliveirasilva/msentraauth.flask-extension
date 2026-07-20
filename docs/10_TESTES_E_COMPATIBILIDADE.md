# Testes e compatibilidade

## Compatibilidade

- Python mínimo: 3.11;
- CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, mínimo `1.37`.

## Cobertura das ETAPAS 07 e 08

- Ordem, idempotência e isolamento de hooks;
- Rejeição local e falha de vínculo;
- Logout com limpeza anterior ao hook;
- Hooks de erro e evento que não mascaram resultados;
- Eventos imutáveis e logging sanitizado;
- Request ID válido, inválido e gerado;
- Consumo atômico nativo e fallback local;
- Falhas e retornos inválidos de backends;
- Auditoria de secret, cookies, storage e loopback;
- Modo estrito e exigência de backend atômico;
- Integração com login, callback, restauração e logout;
- Compatibilidade integral das etapas anteriores.

## Ferramentas

pytest, pytest-cov, Ruff, mypy estrito, Bandit, pip-audit, build e twine.

## Artefatos

Wheel e sdist devem conter hooks, observabilidade, auditoria, threat model, ADRs, testes e marcador `py.typed`.
