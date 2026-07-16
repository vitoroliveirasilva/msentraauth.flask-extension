# Arquitetura

## Estado atual: ETAPA 00

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      v
app.extensions["ms_entra_auth"]
      |
      v
estado exclusivo da aplicação
```

A fundação não cria cliente MSAL, não acessa rede, não registra blueprint e não interpreta configuração de autenticação.

## Pacote implementado

```text
src/flask_ms_entra_auth/
├── __init__.py
├── _version.py
├── extension.py
└── py.typed
```

### Responsabilidades atuais

- `__init__.py`: API pública mínima;
- `_version.py`: fonte única da versão;
- `extension.py`: integração com o ciclo de vida Flask;
- `py.typed`: declaração de pacote tipado.

## Estado por aplicação

Cada aplicação recebe uma instância própria de estado em `app.extensions["ms_entra_auth"]`. A extensão não armazena `app` em atributo permanente e a mesma instância de `MicrosoftEntraAuth` pode inicializar várias aplicações.

A inicialização duplicada possui contrato explícito:

- Mesma instância e mesma aplicação: operação idempotente;
- Instância diferente e chave já registrada: `RuntimeError`;
- Valor estranho já presente na chave: `RuntimeError`.

## Arquitetura planejada

```text
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

```text
src/flask_ms_entra_auth/
├── config.py
├── identity.py
├── decorators.py
├── errors.py
├── context.py
├── auth/
├── storage/
├── hooks.py
└── typing.py
```

Esses módulos futuros não foram criados na ETAPA 00.

## Dependências

O núcleo declara Flask `3.1.x` e MSAL `1.x`. A presença de MSAL no metadata consolida o contrato de runtime planejado, mas nenhum módulo da ETAPA 00 importa ou inicializa MSAL.

Redis, Flask-Login e clientes Graph permanecem opcionais ou externos ao núcleo.

## Fronteiras

A extensão controlará autenticação e cache em etapas futuras. A aplicação continuará responsável por usuário local, autorização, banco, interface, storage de produção e chamadas downstream.
