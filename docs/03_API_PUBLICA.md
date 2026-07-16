# API pública

```python
from flask_ms_entra_auth import MicrosoftEntraAuth, __version__
```

A lista pública atual contém somente `MicrosoftEntraAuth` e `__version__`.

## `MicrosoftEntraAuth`

### Construção

```python
extension = MicrosoftEntraAuth()
```

Também é possível inicializar diretamente uma aplicação:

```python
extension = MicrosoftEntraAuth(app)
```

O padrão recomendado permanece a construção desacoplada seguida de `init_app`, por compatibilidade com application factory.

### `init_app(app)`

- Exige uma instância de `flask.Flask` e rejeita outros valores com `TypeError`;
- Registra estado em `app.extensions["ms_entra_auth"]`;
- Suporta mais de uma aplicação com a mesma instância;
- Mantém estado mutável separado entre aplicações;
- Não armazena a aplicação em `self.app`;
- Não faz chamada de rede;
- Não inicializa MSAL;
- Não registra rotas;
- Não valida credenciais ou configuração de autenticação nesta etapa.

### Inicialização duplicada

- Repetir `init_app()` com a mesma instância e aplicação é idempotente e preserva o estado existente;
- Uma instância diferente tentando registrar a mesma aplicação recebe `RuntimeError`;
- Um valor incompatível já presente na chave também causa `RuntimeError`.

## Versão

A versão pública é consultável por:

```python
from flask_ms_entra_auth import __version__
```

A fonte única é `src/flask_ms_entra_auth/_version.py`, usada também pelo Hatchling para gerar o metadata da distribuição.

## API planejada, não implementada

As APIs abaixo permanecem propostas para etapas posteriores:

- `register_routes`;
- `begin_login`;
- `complete_login`;
- `acquire_token`;
- `logout`;
- `current_identity`;
- `login_required`;
- Hooks de autenticação;
- Exceções públicas de configuração, autenticação, storage e token.