# Arquitetura

## Visão

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth
      |
      +-- configuração validada
      +-- rotas opcionais
      +-- serviço de autenticação
      +-- identidade atual
      +-- token cache
      +-- hooks
      |
      v
MSAL Python
      |
      v
Microsoft Entra ID
```

## Pacote planejado

```text
src/flask_ms_entra_auth/
├── __init__.py
├── extension.py
├── config.py
├── identity.py
├── decorators.py
├── errors.py
├── context.py
├── auth/
│   ├── flow.py
│   ├── client.py
│   ├── token_cache.py
│   └── routes.py
├── storage/
│   ├── base.py
│   ├── session.py
│   └── memory.py
├── hooks.py
├── typing.py
└── py.typed
```

## Responsabilidades

### Extensão

Inicializa configuração, registra estado em `app.extensions`, suporta múltiplas apps e não guarda `app` em atributo permanente.

### Serviço de autenticação

Orquestra o MSAL. Não implementa OAuth ou OIDC.

### Storage

Persiste fluxo e cache por contrato substituível.

### Identidade

Objeto imutável com claims mínimas normalizadas, sem access token.

### Contexto

Expõe a identidade da requisição atual.

### Hooks

Integra a identidade externa ao domínio local.

## Dependências

Núcleo planejado: Flask e MSAL. Redis, Flask-Login e clientes Graph devem ser opcionais ou pertencer ao template.

## Estado

- Por aplicação: `app.extensions`;
- Por requisição: contexto Flask;
- Persistente: storage;
- Proibido: dicionário global, singleton de usuário ou `self.app`.

## Fronteiras

A extensão controla autenticação e cache e a aplicação controla usuário local, autorização, banco, interface, storage de produção e chamadas downstream.
