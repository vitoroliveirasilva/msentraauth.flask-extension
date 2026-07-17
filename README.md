# MS Entra Auth para Flask

Extensão Flask reutilizável, em desenvolvimento, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado isolado por aplicação, identidade imutável, token cache server-side e API pública tipada.

## Estado atual

As **ETAPAS 03 e 04** estão implementadas em conjunto. A versão de desenvolvimento `0.4.0` fornece fundação instalável, configuração validada, storage substituível, identidade autenticada imutável, contexto Flask e núcleo MSAL para aquisição silenciosa.

|                                     Componente |
| ---------------------------------------------: |
|                  Empacotamento, qualidade e CI |
|                         Configuração fail-fast |
|          Storage substituível, namespace e TTL |
|                `Identity` e `current_identity` |
|                              Cliente MSAL lazy |
| `SerializableTokenCache` persistente por conta |
|                  Aquisição silenciosa de token |
|      Login, callback e Authorization Code Flow |
|                      Rotas, decorators e hooks |
|                             Publicação no PyPI |

O status detalhado está em [`docs/implementation/status.md`](docs/implementation/status.md).

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
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Application factory

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="11111111-1111-1111-1111-111111111111",
        MS_ENTRA_CLIENT_SECRET="obtido-de-um-secret-provider",
        MS_ENTRA_TENANT_ID="22222222-2222-2222-2222-222222222222",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SCOPES=["User.Read"],
        MS_ENTRA_SESSION_NAMESPACE="minha-aplicacao",
        MS_ENTRA_TOKEN_CACHE_TTL=28_800,
    )
    entra_auth.init_app(app)
    return app
```

`init_app()` valida a configuração, registra storage e serviço MSAL em `app.extensions["ms_entra_auth"]`, mas não cria cliente MSAL, não acessa rede e não registra rotas.

## Identidade

```python
from flask_ms_entra_auth import Identity, current_identity

identity = Identity.from_claims(
    {
        "oid": "object-id",
        "tid": "tenant-id",
        "sub": "subject",
        "name": "Nome de apresentação",
        "preferred_username": "usuario@example.com",
    },
    home_account_id="home-account-id",
    expected_tenant_id="tenant-id",
)
```

`Identity` é congelada, profundamente imutável, não contém access token e expõe `stable_id` como `(tenant_id, object_id)`. Email e username são apenas apresentação, nunca chave de autorização.

`current_identity` é um proxy de contexto Flask. Fora de uma requisição ativa, sem extensão inicializada ou sem identidade autenticada, falha explicitamente. A vinculação automática da identidade ocorrerá no futuro callback da ETAPA 05.

## Aquisição silenciosa

```python
from flask_ms_entra_auth import ConsentRequired, current_identity

@app.get("/token-interno")
def token_interno() -> dict[str, str]:
    # Esta rota pressupõe que uma etapa futura já vinculou current_identity
    token = entra_auth.acquire_token(["User.Read"])
    return {"account": current_identity.home_account_id, "status": "token obtido"}
```

O token é retornado somente ao código servidor. Ele não entra em `Identity`, sessão client-side, logs ou respostas por padrão. A operação:

1. Localiza a conta MSAL pelo `home_account_id` da identidade;
2. Carrega um `SerializableTokenCache` persistido por conta;
3. Executa aquisição silenciosa;
4. Salva o cache apenas quando alterado;
5. Usa chave de storage derivada por SHA-256, sem expor o identificador da conta.

Se interação for necessária, a extensão gera `ConsentRequired`. Erros do provedor e resultados inválidos são sanitizados.

## Storage

Sem backend explícito, cada aplicação recebe `MemoryStorage`, adequado somente para desenvolvimento e testes. Um backend próprio implementa `AuthStorage`:

```python
from flask_ms_entra_auth import AuthStorage, MicrosoftEntraAuth


class MeuStorage:
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...


storage: AuthStorage = MeuStorage()
entra_auth = MicrosoftEntraAuth(storage=storage)
```

A extensão adiciona namespace por aplicação. O cache MSAL é armazenado exclusivamente como bytes serializados pelo `SerializableTokenCache`; refresh tokens nunca são manipulados diretamente.

## Erros públicos

```python
from flask_ms_entra_auth import (
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    IdentityValidationError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
```

Mensagens públicas não repetem client secret, token, cache, claims completas, chave de storage nem erro bruto do provedor.

## Validação local

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

## Limites atuais

Ainda não existem login, callback, state, nonce, replay protection, rotas, logout, decorators, hooks ou integração com Microsoft Graph. Nenhuma aplicação consegue autenticar um usuário apenas com a versão `0.4.0`; a identidade e o núcleo MSAL estão preparados para serem conectados pelo fluxo web da ETAPA 05.

## Princípios

1. Segurança antes de conveniência;
2. Pouca mágica e comportamento observável;
3. Application factory como requisito;
4. Estado isolado por aplicação, requisição e conta;
5. Tokens apenas no servidor;
6. API pública pequena, tipada e previsível;
7. MSAL como única autoridade sobre refresh tokens e cache de tokens.

## Identidade do pacote

|         Contexto | Nome                          |
| ---------------: | :---------------------------- |
|      Repositório | `msentraauth.flask-extension` |
|     Distribuição | `flask-ms-entra-auth`         |
|           Import | `flask_ms_entra_auth`         |
| Classe principal | `MicrosoftEntraAuth`          |

## Documentação

O índice completo está em [`docs/README.md`](docs/README.md).

## Branches

- `dev`: desenvolvimento e integração;
- `prod`: estado considerado estável.

## Segurança e contribuição

Consulte [`SECURITY.md`](SECURITY.md) e [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licença e marcas

Licenciado sob a [Licença MIT](LICENSE). Este é um projeto independente, não oficial e sem afiliação, manutenção ou endosso da Microsoft. Microsoft, Microsoft Entra, Microsoft Graph e MSAL são marcas de seus respectivos proprietários.
