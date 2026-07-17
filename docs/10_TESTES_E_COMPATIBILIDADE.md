# Testes e compatibilidade

## Compatibilidade

- Python mínimo: 3.11;
- matriz de CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, com mínimo `1.37`.

## Casos implementados

### Fundação e configuração

Import, API pública, application factory, múltiplas apps, ausência de `self.app`, inicialização duplicada, configuração fail-fast, precedência, imutabilidade, authority, redirect URI, scopes e proteção de segredos.

### Storage

- Suíte contratual para backend direto e adaptador namespaced;
- Ausência, save, load e delete idempotente;
- Last-write-wins sequencial e concorrente;
- TTL, expiração preguiçosa e limpeza explícita;
- Chaves, valores, TTLs e namespaces inválidos;
- Isolamento entre namespaces no mesmo backend;
- Backend padrão separado entre aplicações;
- Backend compartilhado com namespaces distintos;
- Falhas externas encapsuladas e causa preservada;
- Respostas inválidas do backend rejeitadas;
- Armazenamento preservado em inicialização duplicada.

## Artefatos

Após `python -m build`, a suíte valida:

- Wheel e source distribution;
- Versão e metadata;
- Requisitos de Python e dependências diretas;
- `py.typed`, configuração, erros, extensão e módulos de storage;
- Testes de configuração, storage e contrato no sdist.

## Ferramentas

pytest, pytest-cov, Ruff, mypy estrito, Bandit, pip-audit, build e twine check.

## Camadas futuras

Identidade, fluxo, callback, token silencioso, logout, hooks e integração com o template pertencem às etapas seguintes.
