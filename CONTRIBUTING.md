# Contribuindo

## Instalação para desenvolvimento

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Validação obrigatória

```bash
ruff check .
ruff format --check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit .
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
```

## Padrões

- Python 3.11 ou superior;
- Tipagem estrita e API pública documentada;
- Application factory e estado por aplicação em `app.extensions`;
- Estado por usuário somente no storage e no contexto de requisição;
- Nenhuma credencial, claim real, token, auth code ou chave de storage em teste ou log;
- Testes de sucesso, falha, isolamento, concorrência e sanitização;
- Changelog, ADRs e status atualizados no mesmo conjunto de mudanças.

## Hooks

- `on_authenticated` roda antes da sessão local e pode rejeitar com `AuthenticationRejected`;
- Falhas inesperadas de vínculo viram `LocalBindingError`;
- `on_logout` roda depois da limpeza local;
- `on_error` e `on_event` nunca podem substituir o comportamento original;
- Hooks são registrados na instância da extensão e compartilhados pelas aplicações inicializadas por essa mesma instância;
- Hooks não devem retornar secrets, mutar `Identity` ou implementar autorização implícita.

## Observabilidade

Eventos públicos devem permanecer pequenos e sanitizados. Alterações em `AuthEvent` exigem revisão de privacidade, testes de logging e atualização do threat model.

É proibido registrar client secret, Authorization, cookie, auth code, tokens, cache, claims completas, query string completa do callback ou chaves de storage.

## Storage

Todo backend implementa `AuthStorage`. Backends que prometem consumo único distribuído implementam também `AtomicAuthStorage.take()` como operação realmente atômica no serviço de persistência.

Não declare suporte atômico quando a implementação fizer `load()` seguido de `delete()`. A estratégia do token cache continua last-write-wins; CAS exige ADR próprio.

## Segurança

Novos controles devem ser verificáveis sem ler ou exibir valores sensíveis. Achados do `audit_security()` possuem código estável, severidade e mensagem sanitizada. Alterar severidade pode afetar `MS_ENTRA_STRICT_SECURITY` e exige nota de compatibilidade.
