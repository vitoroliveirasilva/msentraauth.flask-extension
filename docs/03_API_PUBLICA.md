# API pública proposta

## Import

```python
from flask_ms_entra_auth import MicrosoftEntraAuth
```

## `MicrosoftEntraAuth`

### `init_app(app)`

- Valida configuração;
- Registra `app.extensions['ms_entra_auth']`;
- Suporta mais de uma aplicação;
- Não faz chamada de rede na inicialização.

### `register_routes(app, url_prefix='/auth')`

| Método | Caminho | Finalidade |
|---|---|---|
| GET | `/auth/login` | Iniciar login |
| GET | `/auth/callback` | Concluir login |
| POST | `/auth/logout` | Encerrar sessão |
| GET | `/auth/logged-out` | Página opcional |

### Métodos avançados

- `begin_login(next_url=None)`;
- `complete_login(auth_response)`;
- `acquire_token(scopes, force_refresh=False)`;
- `logout()`.

## Identidade atual

```python
from flask_ms_entra_auth import current_identity
```

Propriedades:

- `is_authenticated`;
- `object_id`;
- `tenant_id`;
- `subject`;
- `display_name`;
- `username`;
- `home_account_id`;
- `claims` somente leitura.

## Decorator

```python
from flask_ms_entra_auth import login_required
```

A resposta para não autenticado deve ser configurável entre redirecionamento HTML e `401` para APIs.

## Hooks

- `on_authenticated`;
- `on_logout`;
- `on_authentication_error`;
- `on_token_refreshed`.

Hooks nunca recebem client secret, refresh token ou cache serializado.

## Exceções públicas

- `ConfigurationError`;
- `AuthenticationError`;
- `AuthenticationRequired`;
- `ConsentRequired`;
- `InvalidCallbackError`;
- `IdentityValidationError`;
- `StorageError`;
- `TokenAcquisitionError`.

Após `1.0.0`, imports e exceções públicas fazem parte da compatibilidade semântica.