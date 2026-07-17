# Arquitetura

## Estado atual: ETAPA 01

```text
Aplicação Flask
      |
      v
MicrosoftEntraAuth.init_app(app)
      |
      +-- resolve e valida configuração
      |
      v
app.extensions["ms_entra_auth"]
      |
      +-- configuração imutável
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
└── py.typed
```

### Responsabilidades atuais

- `__init__.py`: API pública tipada;
- `_version.py`: fonte única da versão;
- `config.py`: precedência, normalização e validação de configuração;
- `errors.py`: exceções públicas previsíveis;
- `extension.py`: integração com o ciclo de vida Flask e estado por aplicação;
- `py.typed`: declaração de pacote tipado.

## Configuração por aplicação

Cada aplicação recebe uma configuração resolvida e imutável. A ordem de precedência é:

1. Argumentos fornecidos à instância de `MicrosoftEntraAuth`;
2. Balores de `app.config`;
3. Padrões seguros para authority e scopes.

A mesma instância pode inicializar aplicações com configurações diferentes quando os valores vêm de cada `app.config`. Nenhuma configuração resolvida é armazenada globalmente ou compartilhada entre apps.

## Estado por aplicação

Cada aplicação recebe uma instância própria de estado em `app.extensions["ms_entra_auth"]`. A extensão não armazena `app` em atributo permanente.

A inicialização duplicada possui contrato explícito:

- Mesma instância e mesma aplicação: operação idempotente que preserva configuração e estado;
- Instância diferente e chave já registrada: `RuntimeError`;
- Valor estranho já presente na chave: `RuntimeError`.

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

Os módulos de identidade, decorators, contexto, autenticação, storage, hooks e typing permanecem futuros.

## Dependências

O núcleo declara Flask `3.1.x` e MSAL `1.x`. O MSAL permanece somente como dependência declarada: nenhum módulo atual importa ou inicializa a biblioteca.

Redis, Flask-Login e clientes Graph permanecem opcionais ou externos ao núcleo.

## Fronteiras

A extensão validará autenticação e cache em etapas futuras. A aplicação continua responsável por usuário local, autorização, banco, interface, storage de produção, secret providers e chamadas downstream.
