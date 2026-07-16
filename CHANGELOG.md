# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo, seguindo [Keep a Changelog](https://keepachangelog.com/) e [Semantic Versioning](https://semver.org/).

## Adicionado

- Empacotamento com `pyproject.toml`, Hatchling e estrutura `src`;
- Pacote tipado `flask_ms_entra_auth` e marcador `py.typed`;
- API pública inicial com `MicrosoftEntraAuth` e `__version__`;
- `init_app()` compatível com application factory e múltiplas aplicações;
- Estado isolado por aplicação em `app.extensions["ms_entra_auth"]`;
- Política explícita para inicialização duplicada;
- Testes unitários e validação de wheel e source distribution;
- Ruff, mypy, pytest-cov, Bandit, pip-audit, build e twine;
- Workflow mínimo de CI para Python 3.11, 3.12, 3.13 e 3.14;
- Registro de status da implementação e ADR da inicialização duplicada.

## Alterado

- README, documentação de arquitetura, API, testes, versionamento, plano, critérios e exemplos para distinguir o que existe do que permanece planejado.

## Segurança

- Auditoria estática com Bandit e auditoria de dependências com pip-audit adicionadas à validação local e à CI.

## Limites

- Nenhum fluxo Microsoft Entra ID ou comportamento MSAL foi implementado.
