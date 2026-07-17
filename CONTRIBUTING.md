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

## Padrões

- Código tipado e mypy em modo estrito;
- Application factory e estado por aplicação em `app.extensions`;
- Estado por requisição somente no contexto Flask;
- Nenhuma aplicação armazenada permanentemente em `self.app`;
- Nenhuma credencial, token, cache ou claim real em código, teste ou log;
- Testes de sucesso, falha, isolamento e sanitização;
- API pública documentada;
- Nomes públicos em inglês e documentação em português;
- Changelog e status atualizados no mesmo conjunto de mudanças.

## Identidade

- `Identity` deve permanecer imutável e sem credenciais;
- `tenant_id` e `object_id` formam a identidade estável;
- Email, username e display name são apenas apresentação;
- Claims devem ser JSON-compatible e somente leitura;
- Access token, refresh token, client secret, token cache e ID token bruto são proibidos em `Identity`;
- Alterações no contrato público exigem testes e documentação.

## MSAL e token cache

- OAuth, OIDC, refresh e cache de tokens pertencem ao MSAL;
- Use somente `SerializableTokenCache` para serialização;
- Não leia, altere ou persista refresh tokens diretamente;
- O cliente MSAL deve continuar lazy e não pode ser criado em `init_app()`;
- Testes não podem acessar rede e devem injetar uma fábrica de cliente;
- Cache persistente deve ser isolado por aplicação e conta;
- Erros do provedor não podem copiar `error_description`, token ou resposta bruta;
- Tokens retornados existem apenas no servidor.

## Storage

Todo backend deve implementar `load`, `save` e `delete` conforme `AuthStorage`. `MemoryStorage` existe apenas para desenvolvimento e testes. Backends de produção devem considerar TLS, menor privilégio, expiração, proteção em repouso, múltiplos workers e indisponibilidade.

## Branches

- `dev`: desenvolvimento e integração;
- `prod`: estado considerado estável.
