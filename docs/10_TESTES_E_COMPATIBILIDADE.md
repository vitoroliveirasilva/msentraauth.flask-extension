# Testes e compatibilidade

## Compatibilidade

- Python mínimo: 3.11;
- CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, mínimo `1.37`.

## Cobertura das ETAPAS 05 e 06

- Início de fluxo, scopes, state e TTL;
- Fluxos MSAL inválidos e hosts inesperados;
- Callback válido, cancelado, corrompido, duplicado e replay;
- Conta ausente, ambígua ou de tenant divergente;
- Persistência e rotação da identidade;
- Cookie sem auth code, claims ou token;
- Restauração request-local;
- Login, callback e logout pelo blueprint;
- Rotas automáticas, manuais e prefixo customizado;
- `login_required` nos modos redirect e raise;
- Métodos não seguros sem redirect;
- Next URL local, allowlist e rejeição de open redirect;
- Tratamento de erros habilitado e propagado;
- Logout preservando dados alheios da sessão;
- Integração completa sem rede com cliente MSAL falso.

## Ferramentas

pytest, pytest-cov, Ruff, mypy estrito, Bandit, pip-audit, build e twine.

## Artefatos

Wheel e sdist são inspecionados para confirmar módulos `auth.flow`, `web`, marcador `py.typed`, metadata, testes e documentação.
