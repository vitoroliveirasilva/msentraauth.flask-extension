# Exemplos de uso disponíveis na ETAPA 00

## Application factory

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()


def create_app() -> Flask:
    app = Flask(__name__)
    entra_auth.init_app(app)
    return app
```

## Duas aplicações com a mesma instância

```python
from flask import Flask
from flask_ms_entra_auth import MicrosoftEntraAuth

entra_auth = MicrosoftEntraAuth()

app_a = Flask("app_a")
app_b = Flask("app_b")

entra_auth.init_app(app_a)
entra_auth.init_app(app_b)
```

Cada aplicação recebe estado próprio em `app.extensions["ms_entra_auth"]`.

## Consulta de versão

```python
from flask_ms_entra_auth import __version__

print(__version__)
```

# Planejado, não disponível

Os exemplos de rota protegida, token para Graph, hooks, storage próprio, login, callback e logout dependem das etapas seguintes.
