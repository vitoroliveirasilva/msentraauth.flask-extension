# MS Entra Auth para Flask

Extensão Flask reutilizável, em desenvolvimento, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado isolado por aplicação e requisição, fluxo server-side, identidade imutável, token cache substituível e API pública tipada.

## Estado atual

As **ETAPAS 05 e 06** estão implementadas em conjunto. A versão de desenvolvimento `0.5.0` oferece o primeiro fluxo web completo da extensão: login, callback, identidade persistida no servidor, rotas opcionais, proteção de endpoints e logout local.

| Componente                                    |
| --------------------------------------------- |
| Empacotamento, qualidade e CI                 |
| Configuração fail-fast                        |
| Storage substituível, namespace e TTL         |
| `Identity` e `current_identity`               |
| Cliente MSAL lazy e token cache por conta     |
| Login e callback Authorization Code Flow      |
| State, consumo único e proteção contra replay |
| Blueprint e `login_required`                  |
| Logout local por `POST`                       |
| Hooks públicos                                |
| Publicação no PyPI                            |

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
    app.secret_key = "obtido-de-um-secret-provider"
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="11111111-1111-1111-1111-111111111111",
        MS_ENTRA_CLIENT_SECRET="obtido-de-um-secret-provider",
        MS_ENTRA_TENANT_ID="22222222-2222-2222-2222-222222222222",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SCOPES=["User.Read"],
        MS_ENTRA_SESSION_NAMESPACE="minha-aplicacao",
        MS_ENTRA_TOKEN_CACHE_TTL=28_800,
        MS_ENTRA_FLOW_TTL=600,
        MS_ENTRA_IDENTITY_TTL=28_800,
    )
    entra_auth.init_app(app)
    return app
```

Por padrão, `init_app()` registra:

- `GET /auth/login`;
- `GET /auth/callback`;
- `POST /auth/logout`.

A inicialização não cria cliente MSAL nem acessa rede. O cliente é construído somente quando login ou aquisição de token é solicitado.

## Proteção de endpoints

```python
from flask_ms_entra_auth import current_identity

@app.get("/conta")
@entra_auth.login_required
def conta() -> dict[str, str]:
    return {
        "object_id": current_identity.object_id,
        "tenant_id": current_identity.tenant_id,
    }
```

Em requisições `GET` e `HEAD`, o modo padrão redireciona usuários anônimos para `/auth/login` e preserva um destino local validado. Métodos que alteram estado geram `AuthenticationRequired` em vez de redirecionar silenciosamente.

Também é possível exigir falha explícita:

```python
@app.get("/api/conta")
@entra_auth.login_required(on_missing="raise")
def api_conta() -> dict[str, str]:
    return {"object_id": current_identity.object_id}
```

## Fluxo web

1. A rota de login valida `next`, cria state imprevisível e persiste o dicionário do MSAL no storage server-side;
2. O navegador é redirecionado ao `auth_uri` retornado pelo MSAL;
3. O callback consome a referência do fluxo antes da troca do código;
4. State e o fluxo do MSAL são validados;
5. Claims e tenant criam uma `Identity` imutável;
6. A identidade é persistida no servidor e o cookie Flask guarda somente uma referência aleatória;
7. Requisições seguintes restauram `current_identity` automaticamente.

O auth code, tokens, claims completas e cache nunca são colocados no cookie da aplicação.

## Login e logout explícitos

Aplicações com rotas customizadas podem usar os métodos públicos:

```python
from flask import redirect, request

@app.get("/entrar")
def entrar():
    return redirect(entra_auth.begin_login(next_url=request.args.get("next")))

@app.get("/retorno")
def retorno():
    result = entra_auth.complete_login(request.args.to_dict(flat=True))
    return redirect(result.next_url)

@app.post("/sair")
def sair():
    return redirect(entra_auth.logout())
```

Para esse modo, configure `MS_ENTRA_AUTO_REGISTER_ROUTES=False` e registre suas rotas com as mesmas garantias de método, validação e tratamento de erro.

O logout remove apenas o fluxo pendente, a identidade e o cache da sessão atual. Ele não promete encerrar todas as sessões Microsoft do usuário.

## Aquisição silenciosa

```python
@app.get("/dados-internos")
@entra_auth.login_required
def dados_internos() -> dict[str, str]:
    access_token = entra_auth.acquire_token(["User.Read"])
    # Use o token somente no servidor para chamar uma API downstream
    return {"status": "pronto"}
```

O token não entra em `Identity`, cookie ou logs. Refresh tokens permanecem sob responsabilidade exclusiva do `SerializableTokenCache` do MSAL.

## Rotas opcionais e tratamento de erros

Configurações principais:

```python
app.config.from_mapping(
    MS_ENTRA_URL_PREFIX="/auth",
    MS_ENTRA_AUTO_REGISTER_ROUTES=True,
    MS_ENTRA_HANDLE_ROUTE_ERRORS=True,
    MS_ENTRA_UNAUTHENTICATED_MODE="redirect",
    MS_ENTRA_POST_LOGIN_REDIRECT_URI="/",
    MS_ENTRA_POST_LOGOUT_REDIRECT_URI="/",
    MS_ENTRA_ALLOWED_NEXT_HOSTS=[],
)
```

Com `MS_ENTRA_HANDLE_ROUTE_ERRORS=True`, o blueprint retorna respostas curtas e sanitizadas. Com `False`, exceções públicas são propagadas para o tratamento da aplicação.

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

Produção exige storage compartilhado entre workers, TTL, TLS quando aplicável, menor privilégio e proteção dos dados em repouso.

## Erros públicos

```python
from flask_ms_entra_auth import (
    AuthenticationCancelled,
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    IdentityValidationError,
    InvalidCallbackError,
    InvalidNavigationTarget,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
```

Mensagens públicas não repetem client secret, auth code, token, cache, claims completas, chave de storage nem descrição bruta do provedor.

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

Hooks de autenticação e logout, integração automática com usuário local, hardening distribuído, Redis oficial, Microsoft Graph, template consumidor e publicação ainda não foram implementados. Autorização por roles, groups ou permissões continua fora do núcleo.

## Princípios

1. Segurança antes de conveniência;
2. Pouca mágica e comportamento observável;
3. Application factory como requisito;
4. Estado isolado por aplicação, requisição, sessão e conta;
5. Tokens apenas no servidor;
6. API pública pequena, tipada e previsível;
7. MSAL como única autoridade sobre OAuth, OIDC, refresh tokens e cache.

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
