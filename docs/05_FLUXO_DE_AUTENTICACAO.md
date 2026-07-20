# Fluxo de autenticação

## Login

1. Valida sessão e destino;
2. Descarta fluxo anterior;
3. Solicita ao MSAL o Authorization Code Flow;
4. Persiste o dicionário server-side com TTL;
5. Guarda somente referência aleatória no cookie;
6. Emite `authentication_started`.

## Callback

1. Consome a referência pendente;
2. Consome o fluxo no storage antes da redenção;
3. Valida state e resposta;
4. Delega ao MSAL a troca do código;
5. Valida claims, tenant e conta;
6. Executa hooks de vínculo local;
7. Persiste identidade e rotaciona referência;
8. Emite sucesso ou erro sanitizado.

Quando o backend implementa `AtomicAuthStorage`, o consumo do fluxo é uma operação única. Caso contrário, a compatibilidade local não oferece garantia entre workers.

## Rejeição local

`AuthenticationRejected` interrompe a autenticação antes da sessão local. Falhas inesperadas do vínculo viram `LocalBindingError`. O token cache eventualmente criado é removido.

## Replay

Fluxo consumido, expirado ou ausente gera `InvalidCallbackError`. Consume-first prioriza segurança: falha posterior exige novo login.

## Logout

Remove fluxo, identidade e token cache da sessão atual, depois executa hooks de logout. A rota padrão usa `POST`. Logout local não encerra todas as sessões Microsoft.
