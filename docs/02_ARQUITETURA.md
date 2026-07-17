# Arquitetura

## Estado atual: ETAPA 02

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      +-- resolve e valida configuração
      +-- seleciona backend de storage
      +-- aplica namespace da aplicação
      |
      v
app.extensions["ms_entra_auth"]
      |
      +-- configuração imutável
      +-- storage namespaced
      +-- estado mutável exclusivo da aplicação
```

A extensão ainda não cria cliente MSAL, não acessa rede, não registra blueprint e não executa autenticação.

## Pacote implementado

```text
src/flask_ms_entra_auth/
├── __init__.py
├── _version.py
├── config.py
├── errors.py
├── extension.py
├── py.typed
└── storage/
    ├── __init__.py
    ├── base.py
    ├── memory.py
    ├── namespaced.py
    └── validation.py
```

### Responsabilidades atuais

- `config.py`: precedência, normalização e configuração de namespace;
- `errors.py`: exceções públicas previsíveis;
- `extension.py`: integração Flask, seleção do backend e estado por aplicação;
- `storage/base.py`: contrato `AuthStorage`;
- `storage/memory.py`: backend em memória com TTL e lock;
- `storage/namespaced.py`: isolamento de chaves antes da delegação;
- `storage/validation.py`: validação segura de chave, valor, TTL e namespace.

## Storage por aplicação

Cada estado registrado contém uma visão namespaced do backend. A aplicação usa apenas chaves lógicas, enquanto o adaptador delega ao backend chaves no formato:

```text
msentra:<namespace>:<chave-logica>
```

Quando nenhum backend é fornecido, cada aplicação recebe um `MemoryStorage` independente. Quando um backend é compartilhado, o namespace impede colisões entre aplicações configuradas com identificadores distintos.

O namespace pode ser definido por `MS_ENTRA_SESSION_NAMESPACE` ou argumento do construtor. Na ausência de valor explícito, ele é derivado de forma determinística a partir do nome da aplicação, client ID e tenant ID, sem incluir client secret.

## Concorrência e TTL

`MemoryStorage` usa `RLock` para tornar operações individuais atômicas. A política é last-write-wins: a última escrita concluída para uma chave substitui a anterior.

TTL é calculado com relógio monotônico. Valores expirados são removidos durante `load()` ou por `purge_expired()`.

## Estado por aplicação

A mesma instância de `MicrosoftEntraAuth` pode inicializar várias aplicações. A extensão não guarda `app` em atributo permanente. Inicialização duplicada da mesma instância preserva configuração, storage e estado originais.

## Arquitetura planejada

```text
MicrosoftEntraAuth
      |
      +-- configuração validada
      +-- storage substituível
      +-- identidade atual
      +-- serviço de autenticação
      +-- rotas opcionais
      +-- token cache
      +-- hooks
      |
      v
MSAL Python
      |
      v
Microsoft Entra ID
```

## Dependências

O núcleo declara Flask `3.1.x` e MSAL `1.x`. Nenhum módulo atual importa ou inicializa o MSAL. Redis, Flask-Login, SQLAlchemy e clientes Graph permanecem opcionais ou externos ao núcleo.

## Fronteiras

O storage desta etapa é byte-oriented e não conhece tokens, identidade, sessão Flask ou formato MSAL. Serialização de token cache será responsabilidade da etapa MSAL e deverá usar `SerializableTokenCache`.
