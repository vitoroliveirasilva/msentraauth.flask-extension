# Exemplos de uso

## Disponível na ETAPA 01

### Application factory com `app.config`

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
    )
    entra_auth.init_app(app)
    return app
```

### Argumentos imutáveis da instância

```python
entra_auth = MicrosoftEntraAuth(
    tenant_id="tenant-id",
    authority="https://login.microsoftonline.com/tenant-id",
    scopes=["User.Read", "Mail.Read"],
)
```

Valores não definidos na instância continuam sendo lidos de `app.config`.

### Duas aplicações com a mesma instância

```python
app_a = Flask("app_a")
app_b = Flask("app_b")

app_a.config.from_mapping(...)
app_b.config.from_mapping(...)

entra_auth.init_app(app_a)
entra_auth.init_app(app_b)
```

Cada aplicação recebe configuração e estado próprios em `app.extensions["ms_entra_auth"]`.

### Tratamento de configuração inválida

```python
from flask_ms_entra_auth import ConfigurationError

try:
    entra_auth.init_app(app)
except ConfigurationError as exc:
    app.logger.error("Configuração Microsoft Entra inválida: %s", exc)
```

A mensagem não contém client secret.

### Consulta de versão

```python
from flask_ms_entra_auth import __version__

print(__version__)
```
