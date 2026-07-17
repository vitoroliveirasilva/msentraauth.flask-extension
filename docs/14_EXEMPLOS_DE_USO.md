# Exemplos de uso

## Disponível na ETAPA 02

### Application factory com storage padrão

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="secret-provider-value",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="app-principal",
    )
    entra_auth.init_app(app)
    return app
```

A aplicação recebe `MemoryStorage` isolado (use apenas em desenvolvimento e testes).

### Backend próprio

```python
from flask_ms_entra_auth import AuthStorage, MicrosoftEntraAuth


class RedisStorage:
    def load(self, key: str) -> bytes | None:
        return redis_client.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        redis_client.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        redis_client.delete(key)


storage: AuthStorage = RedisStorage()
entra_auth = MicrosoftEntraAuth(
    storage=storage,
    session_namespace="app-principal",
)
```

O exemplo ilustra o contrato, mas Redis não é dependência nem implementação fornecida pelo pacote.

### Uso direto de `MemoryStorage`

```python
from flask_ms_entra_auth import MemoryStorage

storage = MemoryStorage()
storage.save("flow", b"serialized", ttl=300)
value = storage.load("flow")
storage.delete("flow")
```

### Tratamento de falha

```python
from flask_ms_entra_auth import StorageError

try:
    storage.save("flow", b"serialized", ttl=300)
except StorageError as exc:
    app.logger.error("Falha segura de storage: %s", exc)
```

Não registre `exc.__cause__` sem sanitização, pois a implementação externa pode incluir detalhes sensíveis.

### Duas aplicações com backend compartilhado

```python
backend = MeuStorage()
extension = MicrosoftEntraAuth(storage=backend)

app_a.config["MS_ENTRA_SESSION_NAMESPACE"] = "app-a"
app_b.config["MS_ENTRA_SESSION_NAMESPACE"] = "app-b"

extension.init_app(app_a)
extension.init_app(app_b)
```

## Planejado, não disponível

Identidade, rotas protegidas, token para Graph, hooks, login, callback, logout e uso real do cache MSAL dependem das etapas seguintes. A versão `0.3.0` não exporta essas APIs.
