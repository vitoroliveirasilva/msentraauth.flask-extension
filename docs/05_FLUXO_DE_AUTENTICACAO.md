# Fluxo de autenticação

## Estado atual

Somente o núcleo para aquisição silenciosa está implementado. Authorization Code Flow, login, callback, state, nonce, replay protection e rotas continuam planejados.

## Aquisição silenciosa implementada

```text
current_identity
      |
      +-- home_account_id
      v
storage namespaced -> SerializableTokenCache
      |
      v
ConfidentialClientApplication lazy
      |
      +-- get_accounts()
      +-- seleção exata por home_account_id
      +-- acquire_token_silent_with_error()
      |
      v
access token apenas no servidor
```

Regras:

1. Sem identidade atual, gera `AuthenticationRequired`;
2. Sem conta correspondente no cache, gera `AuthenticationRequired`;
3. Sem token silencioso disponível, gera `ConsentRequired`;
4. Erro retornado pelo MSAL vira `TokenAcquisitionError` sanitizado;
5. Exceção inesperada do cliente ou provedor vira `ProviderUnavailableError`;
6. Cache alterado é persistido mesmo quando a operação exige interação;
7. Cache inalterado não gera escrita;
8. Access token não entra em `Identity`, cookie ou log.

## Login planejado: ETAPA 05

```text
Navegador -> GET /auth/login -> initiate_auth_code_flow -> Entra ID
```

A etapa futura deverá validar destino, iniciar fluxo MSAL, persistir o dicionário retornado e redirecionar para `auth_uri`.

## Callback planejado: ETAPA 05

```text
Entra ID -> code + state -> /auth/callback -> acquire_token_by_auth_code_flow
```

Deverá validar state, consumir fluxo uma única vez, validar claims e tenant, criar `Identity`, persistir contexto de autenticação e nunca registrar auth code.

## Logout planejado

Deverá limpar somente fluxo, identidade e cache da sessão atual. Remover cache local não encerra automaticamente todas as sessões Microsoft.
