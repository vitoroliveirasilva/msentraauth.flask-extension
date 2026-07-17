# Contribuindo

## Ambiente

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Reinstale o pacote editável após alterar `_version.py`, para manter o metadata do ambiente sincronizado.

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

No PowerShell:

```powershell
$env:DIST_DIR = "dist"
pytest tests/test_distribution.py --no-cov
Remove-Item Env:DIST_DIR
```

## Branches

- `dev`: desenvolvimento;
- `prod`: estado estável.

## Padrões

- Python 3.11 ou superior;
- Código tipado e mypy em modo estrito;
- Application factory;
- Estado e configuração por aplicação em `app.extensions`;
- Nenhuma credencial ou token em código, teste ou log;
- Testes de sucesso e falha;
- API pública documentada;
- Comentários explicam decisões, não repetem o código;
- Nomes públicos em inglês e documentação em português;
- Changelog e status atualizados no mesmo conjunto de mudanças.

## Contrato de storage

Todo backend deve implementar `load`, `save` e `delete` conforme `AuthStorage` e passar pela suíte contratual. Regras mínimas:

- `load()` retorna `bytes` ou `None`;
- `save()` aceita apenas bytes e TTL inteiro positivo ou `None`;
- `delete()` é idempotente;
- Valores expirados são tratados como ausentes;
- Falhas externas são propagadas de forma segura como `StorageError`;
- Chaves e valores nunca aparecem em mensagens de erro;
- Concorrência e política de escrita precisam de testes explícitos.

`MemoryStorage` existe somente para desenvolvimento e testes. Backends de produção devem considerar TLS, menor privilégio, expiração, proteção em repouso, múltiplos workers e indisponibilidade.

## Configuração em testes

Use apenas valores sintéticos. Nunca use tenant, client ID, client secret, tokens, identificadores de sessão ou cache reais.
