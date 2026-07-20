# Exemplos de uso

## Fluxo padrão

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth, current_identity

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "secret-provider-value"
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="app-principal",
    )
    entra_auth.init_app(app)

    @app.get("/conta")
    @entra_auth.login_required
    def conta() -> dict[str, str]:
        return {"object_id": current_identity.object_id}

    return app
```

Acessar `/conta` redireciona para `/auth/login`, conclui o callback e retorna ao destino original.

## API sem redirect automático

```python
@app.get("/api/conta")
@entra_auth.login_required(on_missing="raise")
def api_conta() -> dict[str, str]:
    return {"tenant_id": current_identity.tenant_id}
```

## Rotas customizadas

```python
app.config["MS_ENTRA_AUTO_REGISTER_ROUTES"] = False

@app.get("/entrar")
def entrar():
    return redirect(entra_auth.begin_login(next_url=request.args.get("next")))

@app.get("/oauth/callback")
def callback():
    result = entra_auth.complete_login(request.args.to_dict(flat=True))
    return redirect(result.next_url)

@app.post("/sair")
def sair():
    return redirect(entra_auth.logout())
```

A redirect URI registrada no Entra deve corresponder à rota customizada.

## Destino externo permitido

```python
app.config.from_mapping(
    MS_ENTRA_ALLOWED_NEXT_HOSTS=["portal.example.com"],
    MS_ENTRA_POST_LOGIN_REDIRECT_URI="https://portal.example.com/inicio",
)
```

A comparação usa host e porta exatos e HTTP externo não é aceito.

## Token no servidor

```python
@app.get("/graph-status")
@entra_auth.login_required
def graph_status() -> dict[str, str]:
    token = entra_auth.acquire_token(["User.Read"])
    # Use token em uma chamada server-side (não o devolva ao navegador).
    return {"status": "token-disponivel"}
```

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
entra_auth = MicrosoftEntraAuth(storage=storage, session_namespace="app-principal")
```

Redis é exemplo de contrato, não dependência do pacote.
