# Exemplos de uso

## Application factory

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
        MS_ENTRA_SCOPES=["User.Read"],
        MS_ENTRA_SESSION_NAMESPACE="app-principal",
        MS_ENTRA_TOKEN_CACHE_TTL=28_800,
    )
    entra_auth.init_app(app)
    return app
```

## Construção de identidade

```python
from flask_ms_entra_auth import Identity

identity = Identity.from_claims(
    {
        "oid": "object-id",
        "tid": "tenant-id",
        "sub": "subject",
        "name": "Nome",
        "preferred_username": "usuario@example.com",
    },
    home_account_id="home-account-id",
    expected_tenant_id="tenant-id",
)

assert identity.stable_id == ("tenant-id", "object-id")
```

A construção não autentica uma requisição. O callback futuro será responsável por validar a resposta MSAL e vincular a identidade ao contexto.

## Identidade atual

```python
from flask_ms_entra_auth import current_identity

@app.get("/conta")
def conta() -> dict[str, str]:
    return {
        "object_id": current_identity.object_id,
        "tenant_id": current_identity.tenant_id,
    }
```

Sem identidade autenticada, o acesso gera `AuthenticationRequired`.

## Token silencioso no servidor

```python
from flask_ms_entra_auth import ConsentRequired

@app.get("/dados-internos")
def dados_internos() -> dict[str, str]:
    try:
        access_token = entra_auth.acquire_token(["User.Read"])
    except ConsentRequired:
        return {"status": "interacao-necessaria"}

    # O servidor pode usar access_token para chamar uma API downstream
    # Não devolva o token ao navegador e não o registre em logs
    return {"status": "pronto"}
```

Essa chamada depende de `current_identity`, que ainda será preenchida pelo fluxo da ETAPA 05.

## Backend próprio

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

Redis continua sendo apenas exemplo de contrato, não dependência do pacote.

## Teste sem rede com fábrica injetável

```python
extension = MicrosoftEntraAuth(msal_client_factory=fake_factory)
```

A fábrica recebe configuração resolvida e `SerializableTokenCache`. Essa seam é avançada e serve para testes determinísticos.

## Ainda indisponível

Login, callback, rotas, decorator, logout e hooks permanecem planejados. A versão `0.4.0` não oferece um fluxo completo de autenticação para usuário final.
