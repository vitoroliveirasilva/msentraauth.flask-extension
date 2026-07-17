# Testes e compatibilidade

## Compatibilidade

- Python mínimo: 3.11;
- matriz de CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, com mínimo `1.37`.

## Casos implementados

### Fundação e integração Flask

- Import e API pública;
- Registro em `app.extensions`;
- Mesma instância em duas aplicações;
- Ausência de `self.app`;
- Isolamento de estado e configuração;
- Inicialização duplicada idempotente;
- Conflito com outra instância;
- Rejeição de argumento inválido;
- Ausência de registro de rotas.

### Configuração

- Precedência entre argumentos, `app.config` e padrões;
- Campos obrigatórios ausentes, vazios, não textuais ou placeholders;
- Proteção do client secret em mensagens e representação;
- Tenant single-tenant e caracteres aceitos;
- Authority derivada, customizada, divergente e malformada;
- Redirect URI HTTPS, loopback HTTP e rejeição de HTTP externo;
- Scopes padrão, inválidos, vazios, duplicados e geradores;
- Configuração imutável após inicialização;
- Uso da mesma instância em apps com configurações distintas.

## Artefatos

Após `python -m build`, a suíte de distribuição valida:

- Existência de um wheel e um source distribution;
- Versão nos nomes e no metadata;
- Requisito de Python e dependências diretas;
- Inclusão de `py.typed`, `config.py`, `errors.py` e `extension.py`;
- Inclusão do código e dos testes no sdist.

## Ferramentas

- pytest e pytest-cov;
- Ruff para lint e formatação;
- mypy em modo estrito;
- Bandit;
- pip-audit;
- build;
- twine check.

## Camadas futuras

Storage, identidade, fluxo, callback, token silencioso, logout, hooks e integração com o template pertencem às etapas seguintes.
