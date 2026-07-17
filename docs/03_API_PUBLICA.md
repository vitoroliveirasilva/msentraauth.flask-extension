# API pública

## Disponível na ETAPA 01

```python
from flask_ms_entra_auth import (
    ConfigurationError,
    MicrosoftEntraAuth,
    MicrosoftEntraAuthError,
    __version__,
)
```

## `MicrosoftEntraAuth`

### Construção

O padrão recomendado permanece desacoplado da aplicação:

```python
extension = MicrosoftEntraAuth()
```

A construção aceita argumentos opcionais e imutáveis com precedência sobre `app.config`:

```python
extension = MicrosoftEntraAuth(
    client_id="11111111-1111-1111-1111-111111111111",
    client_secret="secret-provider-value",
    tenant_id="contoso.onmicrosoft.com",
    redirect_uri="https://app.example.com/auth/callback",
    authority="https://login.microsoftonline.com/contoso.onmicrosoft.com",
    scopes=["User.Read"],
)
```

Também é possível inicializar diretamente uma aplicação já configurada:

```python
extension = MicrosoftEntraAuth(app)
```

### `init_app(app)`

- Exige uma instância de `flask.Flask` e rejeita outros valores com `TypeError`;
- Resolve e valida a configuração antes de registrar estado;
- Registra estado em `app.extensions["ms_entra_auth"]`;
- Suporta mais de uma aplicação com a mesma instância;
- Mantém configuração e estado mutável separados entre aplicações;
- Não armazena a aplicação em `self.app`;
- Não faz chamada de rede;
- Não inicializa MSAL;
- Não registra rotas.

### Inicialização duplicada

- Repetir `init_app()` com a mesma instância e aplicação é idempotente;
- A configuração resolvida na primeira inicialização é preservada;
- Uma instância diferente tentando registrar a mesma aplicação recebe `RuntimeError`;
- Um valor incompatível já presente na chave também causa `RuntimeError`.

## Erros públicos

### `MicrosoftEntraAuthError`

Base para falhas previsíveis da extensão.

### `ConfigurationError`

Indica ausência ou invalidade de configuração. As mensagens identificam a chave ou a regra violada sem incluir client secret ou outros valores sensíveis.

## Versão

A versão pública é consultável por:

```python
from flask_ms_entra_auth import __version__
```

A fonte única é `src/flask_ms_entra_auth/_version.py`, usada também pelo Hatchling para gerar o metadata da distribuição.

## API planejada, não implementada

As APIs abaixo permanecem propostas para etapas posteriores:

- Contratos e implementações de storage;
- Identidade e `current_identity`;
- `register_routes`;
- `begin_login`;
- `complete_login`;
- `acquire_token`;
- `logout`;
- `login_required`;
- Hooks de autenticação;
- Exceções de autenticação, storage e token.