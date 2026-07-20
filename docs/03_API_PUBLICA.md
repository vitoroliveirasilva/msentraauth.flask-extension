# API pública

## Símbolos exportados

- `MicrosoftEntraAuth`;
- `Identity`;
- `LoginResult`;
- `current_identity`;
- `AuthStorage`;
- `MemoryStorage`;
- `MicrosoftEntraAuthError` e subclasses públicas;
- `__version__`.

## `MicrosoftEntraAuth`

### Inicialização

```python
extension = MicrosoftEntraAuth()
extension.init_app(app)
```

A mesma instância pode inicializar múltiplas aplicações. Repetir `init_app()` na mesma aplicação é idempotente.

### Rotas

```python
extension.register_routes(app)
```

Registra login, callback e logout quando a aplicação opta por desabilitar o registro automático. A operação é idempotente e rejeita colisão de nome de blueprint.

### Login

```python
auth_uri = extension.begin_login(next_url="/painel", scopes=["User.Read"])
```

Valida o destino, cria e persiste o fluxo e retorna somente a URL segura do provedor.

```python
result = extension.complete_login(request.args.to_dict(flat=True))
```

Consome o fluxo pendente, valida callback, persiste a identidade e retorna `LoginResult(identity, next_url)`.

### Logout

```python
redirect_uri = extension.logout()
```

Remove fluxo pendente, identidade e token cache da sessão atual. Retorna o destino pós-logout configurado.

### Proteção de endpoints

```python
@extension.login_required
def view(): ...

@extension.login_required(on_missing="raise")
def api_view(): ...
```

`on_missing` aceita `redirect` ou `raise`. Métodos não seguros nunca são convertidos em redirect.

### Aquisição silenciosa

```python
access_token = extension.acquire_token(["User.Read"], force_refresh=False)
```

Usa `current_identity` e token cache server-side. O token é retornado ao código servidor e não é persistido na identidade.

## `Identity`

Modelo congelado e profundamente imutável. Campos principais:

- `object_id`;
- `tenant_id`;
- `subject`;
- `home_account_id`;
- `display_name`;
- `username`;
- `claims`;
- `stable_id` como `(tenant_id, object_id)`.

## `current_identity`

Proxy de contexto Flask. Fora de requisição, sem extensão ou sem identidade autenticada, falha explicitamente.

## `LoginResult`

Resultado imutável do callback:

```python
result.identity
result.next_url
```

## Erros

```text
MicrosoftEntraAuthError
├── ConfigurationError
├── StorageError
├── AuthenticationError
│   ├── AuthenticationRequired
│   ├── AuthenticationCancelled
│   ├── InvalidCallbackError
│   ├── InvalidNavigationTarget
│   ├── IdentityValidationError
│   └── ConsentRequired
├── TokenAcquisitionError
└── ProviderUnavailableError
```

O blueprint pode converter esses erros em respostas sanitizadas. Com tratamento interno desativado, a aplicação pode tratá-los diretamente.
