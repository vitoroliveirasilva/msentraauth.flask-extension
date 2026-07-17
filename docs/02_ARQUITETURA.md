# Arquitetura

## Estado atual: ETAPAS 03 e 04

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      +-- configuração validada e imutável
      +-- storage namespaced por aplicação
      +-- MsalService lazy, sem rede no startup
      |
      v
app.extensions["ms_entra_auth"]
      |
      +-- config
      +-- storage
      +-- msal service

Requisição Flask
      |
      +-- Identity imutável em contexto local
      +-- current_identity (LocalProxy)
      |
      v
MicrosoftEntraAuth.acquire_token()
      |
      +-- home_account_id da identidade
      +-- SerializableTokenCache por conta
      +-- ConfidentialClientApplication sob demanda
      +-- acquire_token_silent_with_error
      +-- persistência apenas quando cache muda
```

## Pacote atual

```text
src/flask_ms_entra_auth/
├── __init__.py
├── _version.py
├── config.py
├── context.py
├── errors.py
├── extension.py
├── identity.py
├── py.typed
├── auth/
│   ├── __init__.py
│   ├── client.py
│   ├── protocols.py
│   ├── service.py
│   └── token_cache.py
└── storage/
    ├── __init__.py
    ├── base.py
    ├── memory.py
    ├── namespaced.py
    └── validation.py
```

## Responsabilidades

### `MicrosoftEntraAuth`

Resolve dependências por aplicação, registra estado, suporta application factory e múltiplas apps, não guarda `app` e expõe aquisição silenciosa server-side.

### Configuração

É resolvida uma vez por aplicação, congelada e protegida contra exposição do client secret. Inclui TTL do token cache.

### Storage

Persiste bytes por contrato substituível. O adaptador de namespace impede colisão entre aplicações. `MemoryStorage` é somente para desenvolvimento.

### Identidade

`Identity` representa claims validadas, sem credenciais. A aplicação continua responsável por usuário local e autorização. Claims são profundamente imutáveis e `stable_id` usa tenant + object ID.

### Contexto

`current_identity` é request-local e falha explicitamente sem contexto, extensão ou autenticação. A vinculação e restauração automáticas pertencem ao fluxo web futuro.

### Serviço MSAL

`MsalService` é application-scoped, mas não contém estado de usuário. Recebe configuração, storage e fábrica de cliente. Cada operação carrega cache específico da conta, cria cliente sob demanda e persiste alterações.

### Token cache

A serialização usa exclusivamente `SerializableTokenCache`. O cache é separado por `home_account_id`, mas a chave persistida usa SHA-256 para não revelar o identificador.

## Estado por camada

- Por aplicação: configuração, storage namespaced e serviço MSAL em `app.extensions`;
- Por requisição: identidade em contexto Flask;
- Por conta: token cache serializado no backend;
- Proibido: `self.app`, usuário global, token global, refresh token manipulado manualmente ou token em `Identity`.

## Rede

`init_app()` não cria `ConfidentialClientApplication` nem acessa rede. A construção ocorre somente quando uma operação MSAL é solicitada. Testes injetam fábrica sem rede.

## Fronteiras futuras

Login, callback, state, nonce, replay protection e restauração da identidade pertencem à ETAPA 05. Blueprint, decorator e logout pertencem à ETAPA 06. Hooks permanecem na ETAPA 07.
