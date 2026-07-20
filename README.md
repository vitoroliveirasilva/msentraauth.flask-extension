# MS Entra Auth para Flask

Extensão Flask reutilizável e estável, para integrar aplicações web ao Microsoft Entra ID por meio do MSAL. O projeto prioriza application factory, estado server-side, identidade imutável, storage substituível, fluxo observável e contratos de segurança explícitos.

## Estado atual

O plano mestre está concluído tecnicamente. A versão `1.0.0` fornece autenticação web Microsoft Entra ID para aplicações Flask, com storage substituível, identidade imutável, fluxo MSAL server-side, hooks, auditoria e hardening.

| Componente                            |
| ------------------------------------- |
| Núcleo, configuração e storage        |
| Identidade, MSAL e token cache        |
| Login, callback, rotas e logout local |
| Hooks, observabilidade e hardening    |
| Template consumidor com Redis e Graph |
| Gate de TestPyPI/PyPI                 |

O status detalhado está em [`docs/implementation/status.md`](docs/implementation/status.md).

## Instalação

Após a publicação no índice escolhido:

```bash
python -m pip install "flask-ms-entra-auth>=1.0,<2"
```

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
        MS_ENTRA_EVENT_LOGGING=True,
        MS_ENTRA_REQUEST_ID_HEADER="X-Request-ID",
        MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True,
        MS_ENTRA_STRICT_SECURITY=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    entra_auth.init_app(app)
    return app
```

Por padrão, são registradas as rotas `GET /auth/login`, `GET /auth/callback` e `POST /auth/logout`. A inicialização não cria cliente MSAL nem acessa rede.

## Vínculo com usuário local

O hook autenticado roda depois da validação Microsoft e antes da sessão local ser estabelecida:

```python
from flask_ms_entra_auth import AuthenticationRejected, Identity

@entra_auth.on_authenticated
def vincular_usuario(identity: Identity) -> None:
    usuario = repositorio.buscar_por_entra(
        tenant_id=identity.tenant_id,
        object_id=identity.object_id,
    )
    if usuario is None or not usuario.ativo:
        raise AuthenticationRejected("usuário local indisponível")
```

`AuthenticationRejected` preserva a decisão da aplicação. Outras falhas do hook viram `LocalBindingError`, com causa preservada e mensagem pública sanitizada. Nenhum hook concede roles ou permissões automaticamente.

## Hook de logout

```python
from flask_ms_entra_auth import Identity

@entra_auth.on_logout
def registrar_logout(identity: Identity | None) -> None:
    auditoria.registrar_logout(had_identity=identity is not None)
```

A limpeza da sessão e do token cache ocorre antes do hook (uma falha posterior não restaura a autenticação removida).

## Hooks de erro e evento

```python
from flask_ms_entra_auth import AuthEvent, MicrosoftEntraAuthError

@entra_auth.on_error
def observar_erro(error: MicrosoftEntraAuthError) -> None:
    metricas.incrementar(type(error).__name__)

@entra_auth.on_event
def observar_evento(event: AuthEvent) -> None:
    metricas.evento(event.name, request_id=event.request_id)
```

Hooks de erro e evento são best effort. Falhas neles são contabilizadas, mas não substituem o erro original nem interrompem autenticação bem-sucedida.

`AuthEvent` pode conter apenas nome, timestamp, request ID, endpoint, método, duração, código normalizado e correlation ID. Não contém identidade, claims, tokens, auth code ou payload do provedor.

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

Usuários anônimos podem ser redirecionados em `GET` e `HEAD`. Métodos que alteram estado geram `AuthenticationRequired`.

## Storage e consumo atômico

O contrato mínimo continua sendo `AuthStorage`. Backends distribuídos podem implementar `AtomicAuthStorage`:

```python
from flask_ms_entra_auth import AtomicAuthStorage

class RedisAuthStorage:
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def take(self, key: str) -> bytes | None: ...  # operação única no backend

storage: AtomicAuthStorage = RedisAuthStorage()
```

`take()` deve ler e remover o valor em uma única operação do backend. Quando ausente, a extensão mantém fallback compatível protegido apenas dentro do adaptador local. Esse fallback não oferece garantia entre processos.

Use `MS_ENTRA_REQUIRE_ATOMIC_STORAGE=True` em produção quando callback e sessão puderem atingir múltiplos workers.

## Auditoria de segurança

```python
report = entra_auth.audit_security(app)

for finding in report.findings:
    print(finding.severity, finding.code, finding.message)
```

A auditoria é somente leitura e não exibe valores de secrets. Ela verifica:

- Existência e tamanho mínimo do `SECRET_KEY`;
- `SESSION_COOKIE_HTTPONLY`;
- `SESSION_COOKIE_SAMESITE`;
- `SESSION_COOKIE_SECURE` fora de loopback;
- Uso de `MemoryStorage` fora de teste ou debug;
- Suporte nativo a consumo atômico.

`MS_ENTRA_STRICT_SECURITY=True` impede inicialização quando houver achados de severidade `error`. Avisos continuam visíveis sem bloquear automaticamente o processo.

## Logging estruturado

Com `MS_ENTRA_EVENT_LOGGING=True`, a extensão usa o logger `flask_ms_entra_auth` e adiciona campos normalizados ao `LogRecord`. A mensagem é constante e nenhum valor sensível é interpolado.

O header definido por `MS_ENTRA_REQUEST_ID_HEADER` é aceito somente quando possui formato seguro. Caso contrário, a extensão gera uma referência aleatória por requisição.

## Erros públicos

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── AuthenticationCancelled
│   ├── AuthenticationRejected
│   ├── InvalidCallbackError
│   ├── InvalidNavigationTarget
│   ├── IdentityValidationError
│   └── ConsentRequired
├── HookExecutionError
│   └── LocalBindingError
├── TokenAcquisitionError
└── ProviderUnavailableError
```

O blueprint traduz erros previsíveis para respostas curtas. Rejeição local usa `403`; falhas de hook e storage usam `503`.

## Validação local

```bash
ruff check .
ruff format --check .
mypy src tests scripts
pytest
bandit -c pyproject.toml -r src scripts
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

## Release e compatibilidade

O repositório inclui gate de release, validação de tag e workflows separados para TestPyPI e PyPI por Trusted Publishing. Consulte o [checklist](docs/18_RELEASE_CHECKLIST.md) e o [guia de publicação](docs/19_TESTPYPI_E_PYPI.md).

O consumidor de referência está em `msentraauth.flask-template` e valida a série `1.x` com Redis, Microsoft Graph, frontend, health checks e Docker.

## Limites atuais

- A extensão autentica e a aplicação autoriza;
- Hooks não oferecem transação ou rollback automático de banco;
- Token cache permanece last-write-wins, sem CAS distribuído;
- `MemoryStorage` não é seguro para produção;
- Redis, Graph, interface e deploy permanecem no template consumidor;
- Logout local não encerra todas as sessões Microsoft;

- Publicação em índices externos nunca ocorre sem ação explícita do mantenedor.

Consulte o [threat model](docs/17_THREAT_MODEL.md) antes de usar a extensão em produção.
