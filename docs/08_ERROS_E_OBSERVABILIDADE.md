# Erros e observabilidade

## Respostas do blueprint

|                                         Erro | HTTP |
| -------------------------------------------: | ---- |
| Cancelamento, callback ou navegação inválida | 400  |
|                     Autenticação obrigatória | 401  |
|                               Rejeição local | 403  |
|                           Falha de aquisição | 502  |
|       Provedor, storage ou hook indisponível | 503  |
|                        Configuração inválida | 500  |

Respostas são curtas e sanitizadas. Com `MS_ENTRA_HANDLE_ROUTE_ERRORS=False`, exceções são propagadas.

## Eventos

Eventos atuais incluem:

- `authentication_started`;
- `authentication_succeeded`;
- `authentication_cancelled`;
- `authentication_rejected`;
- `authentication_error`;
- `identity_restored`;
- `token_acquired`;
- `logout_completed`;
- `storage_failure`.

## Request ID

A extensão lê o header configurado, normaliza formato seguro e o mantém em `flask.g`. Valores ausentes ou inválidos são substituídos por identificador aleatório.

## Logging

Quando habilitado, o logger `flask_ms_entra_auth` usa mensagem constante e campos extras normalizados. Não há interpolação de tokens, claims, auth code, segredo ou payload bruto.

## Política de falha

- Hooks de vínculo podem bloquear autenticação;
- Hook de logout pode informar falha após limpeza;
- Hooks de erro e evento não mascaram o comportamento original;
- O mesmo objeto de erro é notificado no máximo uma vez;
- Causas ficam disponíveis por `__cause__` para diagnóstico controlado.
