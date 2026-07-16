# Testes e compatibilidade

## Camadas

### Unitários

Configuração, redirect, identidade, storage, erros, next URL, seleção de conta e cache.

### Integração

Factory, blueprint, sessão, login/callback mockados, token silencioso, logout, hooks e múltiplas apps.

### Contrato de storage

Toda implementação deve passar pela mesma suíte.

### Template

O template instala a extensão e valida cenários de integração.

## Casos mínimos

- Callback válido;
- State divergente;
- Fluxo ausente;
- Replay;
- Cancelamento;
- Tenant inesperado;
- Claims ausentes;
- Cache corrompido;
- Token encontrado e renovado;
- Reautenticação;
- Storage indisponível;
- Logout;
- Next externa;
- Duas apps;
- Sessões concorrentes.

## Compatibilidade

A matriz inicial deve refletir as versões do Python suportadas pelo Flask em uso, além de Flask 3.1+ e a versão mínima compatível do MSAL.

## Metas

- 95% de cobertura do núcleo;
- 100% das ramificações de callback;
- Exceções públicas validadas;
- Suporte a `py.typed`;
- mypy com configurações rigorosas;
- API pública totalmente tipada.

## Ferramentas planejadas

pytest, pytest-cov, Ruff, mypy, Bandit, pip-audit, build e twine check.