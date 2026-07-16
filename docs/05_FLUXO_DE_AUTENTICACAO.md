# Fluxo de autenticação

## Tipo de aplicação

Aplicação web confidencial Flask usando Authorization Code Flow em nome de um usuário.

## Login

```text
Navegador -> GET /auth/login -> initiate_auth_code_flow -> Entra ID
```

A extensão deve validar o destino pós-login, criar o cliente MSAL, iniciar o fluxo, persistir o dicionário retornado e redirecionar para `auth_uri`.

## Callback

```text
Entra ID -> code + state -> /auth/callback -> acquire_token_by_auth_code_flow
```

Regras:

1. Callback sem fluxo correspondente falha;
2. State inválido falha;
3. Fluxo consumido é removido;
4. Erro do provedor é sanitizado;
5. Auth code nunca é logado;
6. Claims obrigatórias e tenant são validados;
7. Destino pós-login deve ser local ou permitido;
8. Replay não autentica novamente.

## Token silencioso

Antes de interação, localizar a conta, executar `acquire_token_silent`, persistir cache alterado e retornar token apenas ao código servidor.

## Logout

Deve limpar fluxo, identidade e cache da sessão. Sendo assim, a rota padrão altera estado por `POST e o logout local não promete encerrar todas as sessões Microsoft.

## Next URL

- Aceita rota relativa local;
- URLs absolutas exigem allowlist explícita;
- Valores `//host` são rejeitados.

## Cancelamento

`access_denied` é cancelamento previsível e não deve virar stack trace ou erro `500`.
