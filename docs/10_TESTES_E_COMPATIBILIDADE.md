# Testes e compatibilidade

## Compatibilidade da ETAPA 00

- Python mínimo: 3.11;
- Matriz de CI: Python 3.11, 3.12, 3.13 e 3.14;
- Flask: série `3.1.x`;
- MSAL: série `1.x`, com mínimo `1.37` para alinhar a matriz declarada com Python 3.14.

## Casos unitários implementados

- Import do pacote;
- Export público de `MicrosoftEntraAuth`;
- Consulta da versão;
- Registro em `app.extensions`;
- Mesma instância em duas aplicações;
- Ausência de `self.app`;
- Isolamento de estado mutável;
- Inicialização duplicada idempotente com a mesma instância;
- Rejeição de outra instância na mesma aplicação;
- Rejeição de argumento inválido;
- Ausência de registro de rotas.

## Artefatos

Após `python -m build`, a suíte de distribuição valida:

- Existência de um wheel e um source distribution;
- Versão nos nomes e no metadata;
- Requisito de Python;
- Dependências diretas;
- Inclusão de `py.typed` no wheel e no sdist;
- Inclusão do código e dos testes no sdist.

## Ferramentas

- Pytest e pytest-cov;
- Ruff para lint e formatação;
- Mypy em modo estrito;
- Bandit;
- Pip-audit;
- Build;
- Twine check.