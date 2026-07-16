# Exemplos de uso propostos

## Factory

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_prefixed_env()
    entra_auth.init_app(app)
    entra_auth.register_routes(app)
    return app
```

## Rota protegida

```python
from flask_ms_entra_auth import current_identity, login_required

@app.get('/conta')
@login_required
def conta():
    return {
        'nome': current_identity.display_name,
        'usuario': current_identity.username,
    }
```

## Token para Graph

```python
token = entra_auth.acquire_token(['User.Read'])
```

A aplicação realiza a chamada HTTP downstream.

## Hook local

```python
@entra_auth.on_authenticated
def vincular(identity):
    return repositorio.obter_ou_criar(
        tenant_id=identity.tenant_id,
        object_id=identity.object_id,
    )
```

## Rotas próprias

```python
@app.get('/entrar')
def entrar():
    return entra_auth.begin_login(next_url='/painel')
```

## Storage próprio

```python
class MeuStorage:
    def load(self, key: str) -> bytes | None: ...
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```
