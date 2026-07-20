# API pública

## `MicrosoftEntraAuth`

Métodos principais:

- `init_app(app)`;
- `register_routes(app)`;
- `begin_login(next_url=None, scopes=None)`;
- `complete_login(auth_response)`;
- `acquire_token(scopes=None, force_refresh=False)`;
- `logout()`;
- `login_required`;
- `on_authenticated(callback)`;
- `on_logout(callback)`;
- `on_error(callback)`;
- `on_event(callback)`;
- `audit_security(app=None)`.

## Hooks

```python
@extension.on_authenticated
def bind(identity: Identity) -> None: ...

@extension.on_logout
def after_logout(identity: Identity | None) -> None: ...

@extension.on_error
def observe(error: MicrosoftEntraAuthError) -> None: ...

@extension.on_event
def metrics(event: AuthEvent) -> None: ...
```

Registros duplicados do mesmo callable são ignorados. A ordem de registro é preservada.

## `AuthEvent`

Dataclass congelada com:

- `name`;
- `timestamp`;
- `request_id`;
- `endpoint`;
- `method`;
- `duration_ms`;
- `error_code`;
- `correlation_id`.

## Storage

```python
class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...

class AtomicAuthStorage(AuthStorage, Protocol):
    def take(self, key: str) -> bytes | None: ...
```

`take()` deve consumir o valor em operação única no backend.

## Auditoria

`audit_security()` retorna `SecurityReport`, que contém uma tupla imutável de `SecurityFinding`.

- `report.passed`: nenhum achado `error`;
- `report.hardened`: nenhum achado;
- `finding.code`: identificador estável;
- `finding.severity`: `info`, `warning` ou `error`;
- `finding.message`: texto sanitizado.

## Erros

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

`AuthenticationRejected` representa decisão explícita da aplicação. `LocalBindingError` representa falha inesperada no vínculo local. `HookExecutionError` identifica falha em hook cujo efeito principal já pode ter ocorrido.
