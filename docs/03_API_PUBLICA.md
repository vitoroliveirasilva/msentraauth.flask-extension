# API pública

## Disponível na versão `0.4.0`

```python
from flask_ms_entra_auth import (
    AuthStorage,
    AuthenticationError,
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    Identity,
    IdentityValidationError,
    MemoryStorage,
    MicrosoftEntraAuth,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
    current_identity,
    __version__,
)
```

## `MicrosoftEntraAuth`

```python
extension = MicrosoftEntraAuth(
    client_id=None,
    client_secret=None,
    tenant_id=None,
    redirect_uri=None,
    authority=None,
    scopes=None,
    session_namespace=None,
    token_cache_ttl=None,
    storage=None,
    msal_client_factory=None,
)
```

`msal_client_factory` é uma seam avançada para testes e integrações controladas. A fábrica recebe configuração resolvida e `SerializableTokenCache`. O cliente padrão é `ConfidentialClientApplication` com PII logging desligado.

### `init_app(app)`

- Valida aplicação e configuração;
- Registra estado em `app.extensions["ms_entra_auth"]`;
- Seleciona storage e aplica namespace;
- Registra `MsalService` sem construir cliente MSAL;
- Suporta a mesma instância em várias apps;
- É idempotente para a mesma instância na mesma app;
- Não armazena `app`, não acessa rede e não registra rotas.

### `acquire_token(scopes=None, *, force_refresh=False) -> str`

Adquire silenciosamente um access token delegado para `current_identity`.

- Exige contexto de requisição e identidade autenticada;
- Usa scopes configurados quando `scopes` é `None`;
- Localiza conta pelo `home_account_id`;
- Carrega e persiste cache MSAL por conta;
- Retorna token somente ao código servidor;
- Não adiciona token à identidade nem ao cookie Flask.

Pode gerar `AuthenticationRequired`, `ConsentRequired`, `StorageError`, `TokenAcquisitionError` ou `ProviderUnavailableError`.

## `Identity`

```python
identity = Identity.from_claims(
    claims,
    home_account_id="...",
    expected_tenant_id="...",
)
```

Campos:

- `object_id: str`;
- `tenant_id: str`;
- `home_account_id: str`;
- `subject: str | None`;
- `display_name: str | None`;
- `username: str | None`;
- `claims: Mapping[str, object]` somente leitura;
- `stable_id -> tuple[str, str]`.

`Identity` é congelada, não expõe claims em `repr` e rejeita access token, refresh token, ID token bruto, client secret e token cache.

## `current_identity`

Proxy Flask para a identidade da requisição. Falha explicitamente:

- Fora de request context;
- Quando a extensão não está inicializada;
- Quando não existe identidade autenticada.

A API pública não oferece vinculação manual da identidade. Essa integração é interna e será acionada pelo callback futuro.

## Storage

`AuthStorage` e `MemoryStorage` mantêm o contrato da ETAPA 02. O cache MSAL usa o mesmo storage namespaced.

## Erros públicos

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
└── ProviderUnavailableError
```

`TokenAcquisitionError` pode expor `code` e `correlation_id` quando esses valores passam pela sanitização da extensão. Descrições brutas do provedor não são copiadas.

## API ainda planejada

- `register_routes`;
- `begin_login` e `complete_login`;
- Callback e persistência de fluxo;
- Logout;
- `login_required`;
- Hooks.
