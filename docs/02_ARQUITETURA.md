# Arquitetura

## Estado atual: ETAPAS 05 e 06

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      +-- Configuração imutável
      +-- Storage namespaced
      +-- MsalService lazy
      +-- AuthCodeFlowService
      +-- WebSessionManager
      +-- before_request de restauração
      +-- Blueprint opcional
      |
      v
app.extensions["ms_entra_auth"]

GET /auth/login
      |
      +-- Valida next
      +-- Cria state
      +-- Inicia fluxo MSAL
      +-- Persiste fluxo server-side
      v
Microsoft Entra ID
      |
GET /auth/callback
      |
      +-- Consome referência e fluxo uma vez
      +-- Valida state e resposta MSAL
      +-- Valida tenant e conta
      +-- Persiste Identity server-side
      v
Cookie Flask contém apenas session_id aleatório

Requisições seguintes
      |
      +-- before_request restaura Identity
      +-- current_identity request-local
      +-- login_required protege endpoints
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
│   ├── flow.py
│   ├── protocols.py
│   ├── service.py
│   └── token_cache.py
├── storage/
│   ├── __init__.py
│   ├── base.py
│   ├── memory.py
│   ├── namespaced.py
│   └── validation.py
└── web/
    ├── __init__.py
    ├── models.py
    ├── routes.py
    ├── session.py
    └── urls.py
```

## Responsabilidades

### `MicrosoftEntraAuth`

Compõe dependências por aplicação, registra rotas opcionais, inicia e completa login, executa logout local, oferece aquisição silenciosa e o decorator `login_required`. A instância nunca guarda `app`.

### `AuthCodeFlowService`

Orquestra o dicionário de Authorization Code Flow produzido pelo MSAL. Fluxo e state são persistidos no servidor com TTL. O fluxo é apagado antes da redenção do código para garantir consumo único.

### `WebSessionManager`

Mantém no cookie Flask somente referências aleatórias. Fluxos, identidades e caches ficam no `AuthStorage`. Também restaura a identidade no início de cada requisição e limpa exclusivamente o estado da extensão no logout.

### Blueprint

O blueprint interno fornece login, callback e logout. É registrado automaticamente por padrão, pode usar prefixo customizado e pode ser desativado para aplicações com rotas próprias.

### `login_required`

Consulta `current_identity`. Em métodos seguros pode redirecionar para login. Em métodos de alteração de estado sempre falha explicitamente, evitando transformação silenciosa de uma operação em navegação.

## Estado por camada

- Por aplicação: configuração, storage, serviços e flags em `app.extensions`;
- Por navegador: referências mínimas no cookie Flask assinado;
- Por fluxo: dicionário MSAL e destino no storage com TTL curto;
- Por sessão autenticada: identidade no storage com TTL de sessão;
- Por requisição: `current_identity` no contexto Flask;
- Por conta: `SerializableTokenCache` no storage;
- Proibido: `self.app`, usuário global, token global, auth code em cookie ou refresh token manipulado manualmente.

## Rede

`init_app()` não cria cliente MSAL nem acessa rede. A rede pode ocorrer somente ao iniciar/completar fluxo ou adquirir token. Testes usam fábrica injetável e não acessam provedor real.

## Fronteiras futuras

Hooks pertencem à ETAPA 07. Hardening distribuído e revisão de ameaça pertencem à ETAPA 08. Template, Redis e Graph pertencem à ETAPA 09.
