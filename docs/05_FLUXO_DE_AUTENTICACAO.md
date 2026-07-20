# Fluxo de autenticação

## Login

```text
GET /auth/login?next=/painel
      |
      +-- valida destino
      +-- cria state imprevisível
      +-- initiate_auth_code_flow
      +-- persiste dicionário MSAL com TTL
      +-- cookie recebe apenas flow_id aleatório
      v
Microsoft Entra ID
```

Um login novo descarta o fluxo pendente anterior da mesma sessão.

## Callback

```text
GET /auth/callback?code=...&state=...
      |
      +-- Consome flow_id do cookie
      +-- Carrega e apaga fluxo antes da redenção
      +-- Rejeita campos duplicados
      +-- Compara state em tempo constante
      +-- Acquire_token_by_auth_code_flow
      +-- Valida claims, tenant e conta
      +-- Persiste cache MSAL quando alterado
      +-- Persiste Identity server-side
      +-- Rotaciona referência de sessão
      v
Redirect para next validado
```

O nonce e demais dados OIDC permanecem dentro do dicionário do fluxo criado e validado pelo MSAL. A extensão não reimplementa a validação criptográfica do protocolo.

## Replay

O fluxo é removido do storage antes da troca do código. Repetição, concorrência ou reutilização do mesmo callback falham como `InvalidCallbackError`.

## Cancelamento e erros

- `access_denied` vira `AuthenticationCancelled`;
- State ausente ou divergente vira `InvalidCallbackError`;
- Erros retornados pelo provedor viram `TokenAcquisitionError` sanitizado;
- Falhas inesperadas viram `ProviderUnavailableError`;
- Auth code, descrição bruta e resposta completa não entram em mensagens públicas.

## Identidade e sessão

- O cookie Flask guarda apenas um identificador aleatório;
- A identidade serializada fica no storage com TTL e é restaurada em `before_request`;
- Uma nova autenticação rotaciona a referência e remove a identidade anterior.

## Logout

`POST /auth/logout` remove:

1. Fluxo pendente da sessão;
2. Identidade server-side;
3. Referência no cookie;
4. Token cache da conta autenticada.

Outras chaves da sessão Flask são preservadas (o logout é local e não encerra todas as sessões Microsoft).

## Next URL

- Rotas relativas locais são aceitas;
- URLs absolutas exigem allowlist exata;
- Valores ambíguos, protocol-relative, com barra invertida, fragmento ou host não permitido são rejeitados.
