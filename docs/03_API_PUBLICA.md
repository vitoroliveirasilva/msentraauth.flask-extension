# API pública

## Disponível na ETAPA 02

```python
from flask_ms_entra_auth import (
    AuthStorage,
    ConfigurationError,
    MemoryStorage,
    MicrosoftEntraAuth,
    MicrosoftEntraAuthError,
    StorageError,
    __version__,
)
```

## `MicrosoftEntraAuth`

O padrão recomendado permanece desacoplado da aplicação:

```python
extension = MicrosoftEntraAuth()
```

A construção aceita configuração imutável e backend opcional:

```python
extension = MicrosoftEntraAuth(
    client_id="client-id",
    client_secret="secret-provider-value",
    tenant_id="tenant-id",
    redirect_uri="https://app.example.com/auth/callback",
    scopes=["User.Read"],
    session_namespace="app-principal",
    storage=meu_storage,
)
```

### `init_app(app)`

- Valida aplicação e configuração;
- Registra estado em `app.extensions["ms_entra_auth"]`;
- Seleciona `MemoryStorage` quando não há backend explícito;
- Aplica namespace antes de qualquer chamada ao backend;
- Suporta múltiplas aplicações com a mesma instância;
- Não armazena a aplicação em `self.app`;
- Não acessa rede, não inicializa MSAL e não registra rotas.

## `AuthStorage`

Contrato estrutural e verificável em runtime:

```python
class AuthStorage(Protocol):
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

### Garantias esperadas

- Ausência ou expiração retorna `None`;
- Valores são bytes;
- TTL é inteiro positivo ou `None`;
- `delete()` é idempotente;
- Falhas de infraestrutura são representadas por `StorageError`.

## `MemoryStorage`

Backend público para desenvolvimento e testes:

```python
storage = MemoryStorage()
storage.save("flow", b"payload", ttl=300)
assert storage.load("flow") == b"payload"
storage.delete("flow")
```

Também oferece `purge_expired() -> int`. Não é adequado para produção, múltiplos processos ou persistência após reinício.

## Erros públicos

### `MicrosoftEntraAuthError`

Base para falhas previsíveis da extensão.

### `ConfigurationError`

Indica configuração ausente ou inválida.

### `StorageError`

Indica chave, valor, TTL, expiração ou operação de backend inválida. Quando uma falha externa é encapsulada, a causa original fica disponível em `__cause__`, sem ser copiada para a mensagem pública.

## Versão

A versão pública vem de `src/flask_ms_entra_auth/_version.py` e é usada dinamicamente pelo Hatchling.

## API planejada, não implementada

- Identidade e `current_identity`;
- `register_routes`;
- `begin_login` e `complete_login`;
- Aquisição silenciosa de token;
- Logout e decorators;
- Hooks;
- Serialização e uso real do token cache MSAL.
